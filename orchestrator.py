import os
import threading
import time
try:
    import fcntl
except ImportError:
    # Windows fallback
    import msvcrt
import time
import threading
import subprocess
try:
    from typing import Callable, Any, Optional, Tuple
except ImportError:
    # Python < 3.9 compatibility
    from typing import Callable, Any, Optional
    from typing import Tuple
from typing import List
import queue
class CommandFailureLimitExceeded(Exception):
    """Exception raised when consecutive command failures reach the limit."""
    pass



class TimeoutEnforcer:
    """
    Runtime timeout enforcement guard for task orchestrator.

    Monitors task execution against configurable timeout limits with warnings
    and failure enforcement. Uses polling-based monitoring in main thread
    per project patterns.
    """

    DEFAULT_TIMEOUT = 3600  # 1 hour in seconds
    WARNING_THRESHOLD = 0.8  # Warn at 80% of timeout

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT):
        self.timeout_seconds = timeout_seconds
        self.warning_threshold_seconds = int(timeout_seconds * self.WARNING_THRESHOLD)
        self.task_start_time: Optional[float] = None
        self.task_name: Optional[str] = None
        self.monitoring = False
        self.opt_out = False
        self.warning_issued = False
        self.enforced = False

    def set_opt_out(self, opt_out: bool = True):
        """Configure opt-out for timeout enforcement."""
        self.opt_out = opt_out

    def start_task(self, task_name: str):
        """Start monitoring a task execution."""
        self.task_name = task_name
        self.task_start_time = time.time()
        self.monitoring = True
        self.warning_issued = False
        self.enforced = False

    def stop_task(self):
        """Stop monitoring the current task."""
        self.monitoring = False
        self.task_start_time = None
        self.task_name = None
        self.warning_issued = False

    def _get_elapsed_time(self) -> float:
        """Get elapsed time since task start."""
        if self.task_start_time is None:
            return 0.0
        return float(time.time() - self.task_start_time)

    def check_timeout(self) -> Tuple[bool, Optional[str]]:
        """
        Check if timeout conditions are met.

        Returns:
            tuple: (should_enforce, message)
            - should_enforce: True if task should be stopped
            - message: Warning or enforcement message, None if no action needed
        """
        if not self.monitoring or self.task_start_time is None:
            return False, None

        elapsed = self._get_elapsed_time()

        # Check for timeout limit first (higher priority than warning)
        if elapsed >= self.timeout_seconds:
            if self.opt_out:
                # Task has opt-out, just log but don't enforce
                if not self.enforced:
                    self.enforced = True
                    message = f"Task '{self.task_name}' exceeded {self.timeout_seconds}s timeout but has opt-out configured"
                    return False, message
            else:
                # Enforce timeout
                if not self.enforced:
                    self.enforced = True
                    message = f"Task '{self.task_name}' exceeded {self.timeout_seconds}s timeout limit - enforcing failure"
                    return True, message

        # Check for warning threshold (80%)
        if elapsed >= self.warning_threshold_seconds and not self.warning_issued:
            self.warning_issued = True
            remaining = self.timeout_seconds - elapsed
            message = f"Task '{self.task_name}' approaching timeout - {remaining:.2f}s remaining"
            return False, message

        return False, None

    def execute_with_timeout(self, task_func: Callable, *args, **kwargs) -> Any:
        """
        Execute a task function with timeout monitoring.

        Args:
            task_func: Function to execute
            *args: Positional arguments for task_func
            **kwargs: Keyword arguments for task_func

        Returns:
            Result of task_func if completed within timeout

        Raises:
            TimeoutError: If task exceeds timeout and enforcement is active
        """
        task_name = getattr(task_func, '__name__', str(task_func))
        self.start_task(task_name)

        try:
            # Use polling-based monitoring in main thread
            result = None
            exception = None

            def task_wrapper():
                nonlocal result, exception
                try:
                    result = task_func(*args, **kwargs)
                except Exception as e:
                    exception = e

            # Start task in separate thread to allow main thread polling
            task_thread = threading.Thread(target=task_wrapper)
            task_thread.start()

            # Poll for timeout conditions in main thread
            while task_thread.is_alive():
                should_enforce, message = self.check_timeout()

                if message:
                    print(f"[TIMEOUT] {message}")

                if should_enforce:
                    # Task exceeded timeout and enforcement is active
                    raise TimeoutError(f"Task '{task_name}' timed out after {self.timeout_seconds} seconds")

                # Poll every 100ms
                time.sleep(0.1)

            # Check for any exception from task thread
            if exception:
                raise exception

            return result

        finally:
            self.stop_task()
class FileLocker:
    """Cross-platform file locking utility."""

    def __init__(self):
        self._has_fcntl = 'fcntl' in globals()

    def lock_file(self, file_handle, exclusive=True):
        """Acquire file lock on the given file handle."""
        if self._has_fcntl:
            # Unix-like systems
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        else:
            # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK, 1)

    def unlock_file(self, file_handle):
        """Release file lock on the given file handle."""
        if self._has_fcntl:
            # Unix-like systems
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        else:
            # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)


class AsyncBufferedWriter:
    """
    Asynchronous buffered writer for ultra-low latency persistent data writes.
    Uses background thread and queue for non-blocking I/O operations.
    """

    DEFAULT_BUFFER_SIZE = 10  # Increased for better throughput
    DEFAULT_FLUSH_INTERVAL = 0.1  # Faster flushes for concurrency
    DEFAULT_QUEUE_SIZE = 10000  # Larger queue for concurrent operations

    def __init__(self, file_path: str, buffer_size: int = DEFAULT_BUFFER_SIZE,
                 flush_interval: float = DEFAULT_FLUSH_INTERVAL, queue_size: int = DEFAULT_QUEUE_SIZE):
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.write_queue = queue.Queue(maxsize=queue_size)
        self.locker = FileLocker()
        self._shutdown_event = threading.Event()
        self._flush_event = threading.Event()
        self._writer_thread = threading.Thread(target=self._writer_worker, daemon=True)
        self._writer_thread.start()

        # Per-thread queues to eliminate queue contention
        self._thread_queues = {}
        self._thread_lock = threading.RLock()
        self._lock = threading.Lock()  # Thread synchronization for file operations
        self._thread_lock = self._thread_lock  # Ensure attribute exists for backward compatibility

    def add_entry(self, entry: str) -> float:
        """
        Add entry to per-thread queue (non-blocking, returns immediately).

        Returns:
            Queue operation latency in milliseconds
        """
        start_time = time.time()
        thread_id = threading.get_ident()

        with self._thread_lock:
            if thread_id not in self._thread_queues:
                # Create per-thread queue for lock-free operations
                self._thread_queues[thread_id] = queue.Queue(maxsize=self.write_queue.maxsize // 10)  # Smaller per-thread queues

            thread_queue = self._thread_queues[thread_id]

        try:
            # Try per-thread queue first
            thread_queue.put_nowait(entry)
        except queue.Full:
            # Fallback to global queue
            try:
                self.write_queue.put_nowait(entry)
            except queue.Full:
                # Final fallback to immediate write
                self._immediate_write(entry)

        # Signal writer thread only periodically to reduce contention
        if start_time % 0.01 < 0.001:  # Signal ~10% of the time
            self._flush_event.set()

        return (time.time() - start_time) * 1000  # Convert to ms

    def flush(self) -> float:
        """
        Force immediate flush of all queued entries.

        Returns:
            Flush latency in milliseconds
        """
        start_time = time.time()

        # Signal flush and wait for completion
        self._flush_event.set()
        # Small delay to allow background thread to process
        time.sleep(0.01)

        return (time.time() - start_time) * 1000  # Convert to ms

    def shutdown(self):
        """Shutdown the writer thread gracefully."""
        self._shutdown_event.set()
        self._flush_event.set()

        # Flush all per-thread queues to global queue
        with self._thread_lock:
            for thread_queue in self._thread_queues.values():
                while not thread_queue.empty():
                    try:
                        entry = thread_queue.get_nowait()
                        self.write_queue.put_nowait(entry)
                    except queue.Full:
                        break

        self._writer_thread.join(timeout=2.0)  # Increased timeout for draining queues

    def _writer_worker(self):
        """Background writer thread that processes per-thread and global queues."""
        buffer: List[str] = []
        last_flush_time = time.time()

        while not self._shutdown_event.is_set():
            try:
                # Process per-thread queues first (lock-free)
                entries_processed = 0
                with self._thread_lock:
                    thread_queues = list(self._thread_queues.items())

                for thread_id, thread_queue in thread_queues:
                    try:
                        # Drain thread queue quickly
                        with self._thread_lock:
                            while len(buffer) < self.buffer_size and not thread_queue.empty():
                                entry = thread_queue.get_nowait()
                                buffer.append(entry)
                                entries_processed += 1
                    except queue.Empty:
                        pass

                # Process global queue if needed
                if len(buffer) < self.buffer_size:
                    try:
                        entry = self.write_queue.get_nowait()
                        buffer.append(entry)
                        entries_processed += 1
                    except queue.Empty:
                        pass

                # Check flush conditions
                current_time = time.time()
                should_flush = (
                    len(buffer) >= self.buffer_size or
                    (current_time - last_flush_time) >= self.flush_interval or
                    self._flush_event.is_set() or
                    entries_processed > 0  # Flush if we processed any entries
                )

                if should_flush and buffer:
                    self._flush_buffer_to_file(buffer)
                    buffer.clear()
                    last_flush_time = current_time
                    self._flush_event.clear()

                # Sleep only if no work done
                if entries_processed == 0:
                    time.sleep(0.01)  # Reduced sleep for better responsiveness

            except Exception as e:
                print(f"Background writer error: {e}")

    def _flush_buffer_to_file(self, buffer: List[str]):
        """Flush buffer to file with optimized file locking and atomic operations."""
        if not buffer:
            return

        try:
            # Use file locking with proper thread synchronization for atomic operations
            with self._lock:
                with open(self.file_path, 'a') as f:
                    self.locker.lock_file(f)

                    # Check for section header efficiently (read only end of file)
                    file_size = f.tell()
                    if file_size == 0:
                        # New file
                        f.write('# Development & Debug Commands\n')
                    else:
                        # Check if section exists by reading last portion
                        f.seek(max(0, file_size - 200))  # Read last 200 chars
                        tail_content = f.read()
                        if '# Development & Debug Commands' not in tail_content:
                            f.seek(file_size)  # Go back to end
                            f.write('\n# Development & Debug Commands\n')

                    # Write all entries atomically
                    f.writelines(buffer)

        except Exception as e:
            print(f"Failed to flush buffered entries: {e}")
        finally:
            try:
                with self._lock:  # Ensure thread safety during unlock
                    self.locker.unlock_file(open(self.file_path, 'a'))
            except:
                pass

    def _immediate_write(self, entry: str):
        """Immediate synchronous write when queue is full."""
        buffer = [entry]
        self._flush_buffer_to_file(buffer)


# Backward compatibility alias
class CommandFailureTracker:
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(self, persistent_data_file='persistent-memory.md', buffer_size: int = AsyncBufferedWriter.DEFAULT_BUFFER_SIZE,
                 flush_interval: float = AsyncBufferedWriter.DEFAULT_FLUSH_INTERVAL):
        self.persistent_data_file = persistent_data_file
        self.consecutive_failures = 0
        self.failed_commands = []
        self.last_failure_context = ""
        self.limit_reached = False
        # Initialize buffered writer for optimized I/O
        self.buffered_writer = AsyncBufferedWriter(persistent_data_file, buffer_size, flush_interval)
        # Add thread synchronization for concurrent access
        self._lock = threading.Lock()
        # Add thread-local storage for per-thread tracker instances
        self._local = threading.local()

    def record_success(self, successful_command):
        with self._lock:
            if self.limit_reached:
                self._write_debug_entry(successful_command)
                self.limit_reached = False
            self.consecutive_failures = 0
            self.failed_commands = []
            self.last_failure_context = ""

    def record_failure(self, command, context=""):
        with self._lock:
            self.consecutive_failures += 1
            self.failed_commands.append(command)
            self.last_failure_context = context
            if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                self.limit_reached = True
                raise CommandFailureLimitExceeded(f"Consecutive command failures reached {self.MAX_CONSECUTIVE_FAILURES}")

    def get_thread_local_tracker(self):
        """Get a thread-local instance of CommandFailureTracker for per-thread isolation."""
        if not hasattr(self._local, 'tracker'):
            # Create a thread-local tracker instance
            self._local.tracker = CommandFailureTracker(
                persistent_data_file=self.persistent_data_file,
                buffer_size=self.buffered_writer.buffer_size,
                flush_interval=self.buffered_writer.flush_interval
            )
        return self._local.tracker

    def _write_debug_entry(self, successful_command):
        """
        Write debug entry using buffered writer for optimized I/O performance.

        Args:
            successful_command: The command that successfully recovered from failure sequence
        """
        try:
            # Create the debug entry
            entry = f"- **Command Failure Recovery**: Context: {self.last_failure_context}, Failed commands: {self.failed_commands}, Successful command: {successful_command}\n"

            # Add to buffer - returns latency for monitoring
            latency = self.buffered_writer.add_entry(entry)

            # Log if latency exceeds SLA target for monitoring
            if latency > 1.0:  # <1ms p95 SLA target (updated from 10ms)
                print(f"[SLA WARNING] Debug entry write exceeded 1ms SLA: {latency:.2f}ms")

        except Exception as e:
            print(f"Failed to write debug entry: {e}")

def execute_command_with_tracking(command, tracker, context="", shell=False, timeout=30):
    """
    Execute a command with failure tracking and basic error recovery.

    Args:
        command: Command to execute (string or list)
        tracker: CommandFailureTracker instance
        context: Context for failure logging
        shell: Whether to use shell execution
        timeout: Command timeout in seconds

    Returns:
        tuple: (stdout, stderr) on success, (None, stderr) on failure

    Raises:
        CommandFailureLimitExceeded: When consecutive failures reach limit
    """
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            tracker.record_success(command if isinstance(command, str) else ' '.join(command))
            return result.stdout, result.stderr
        else:
            # retry once
            time.sleep(1)
            try:
                result2 = subprocess.run(command, shell=shell, capture_output=True, text=True, timeout=timeout)
                if result2.returncode == 0:
                    tracker.record_success(command if isinstance(command, str) else ' '.join(command))
                    return result2.stdout, result2.stderr
                else:
                    # failed twice
                    tracker.record_failure(command if isinstance(command, str) else ' '.join(command), context + " (failed after retry)")
                    return None, result2.stderr
            except subprocess.TimeoutExpired:
                tracker.record_failure(command if isinstance(command, str) else ' '.join(command), context + " (timeout on retry)")
                return None, "Command timed out on retry"
            except Exception as e:
                tracker.record_failure(command if isinstance(command, str) else ' '.join(command), context + f" (exception on retry: {e})")
                return None, str(e)
    except subprocess.TimeoutExpired:
        tracker.record_failure(command if isinstance(command, str) else ' '.join(command), context + " (timeout)")
        return None, "Command timed out"
    except Exception as e:
        tracker.record_failure(command if isinstance(command, str) else ' '.join(command), context + f" (exception: {e})")
        return None, str(e)


def execute_command_with_tracking_thread_safe(command, tracker, context="", shell=False, timeout=30):
    """
    Thread-safe version of execute_command_with_tracking using thread-local trackers.

    Args:
        command: Command to execute (string or list)
        tracker: CommandFailureTracker instance (main shared tracker)
        context: Context for failure logging
        shell: Whether to use shell execution
        timeout: Command timeout in seconds

    Returns:
        tuple: (stdout, stderr) on success, (None, stderr) on failure

    Raises:
        CommandFailureLimitExceeded: When consecutive failures reach limit
    """
    # Get thread-local tracker instance for isolation
    local_tracker = tracker.get_thread_local_tracker()
    return execute_command_with_tracking(command, local_tracker, context, shell, timeout)
BufferedWriter = AsyncBufferedWriter
