import time
import threading
try:
    from typing import Callable, Any, Optional, Tuple
except ImportError:
    # Python < 3.9 compatibility
    from typing import Callable, Any, Optional
    from typing import Tuple


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

        # Check for warning threshold (80%)
        if elapsed >= self.warning_threshold_seconds and not self.warning_issued:
            self.warning_issued = True
            remaining = self.timeout_seconds - elapsed
            message = ".2f"
            return False, message

        # Check for timeout limit
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