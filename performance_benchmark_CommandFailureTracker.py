#!/usr/bin/env python3
"""
Performance Benchmark Suite for CommandFailureTracker Integration

This benchmark suite comprehensively tests the performance characteristics of
CommandFailureTracker integration with execute_command_with_tracking function,
including latency measurements, memory profiling, concurrent load testing, and
stress testing under high failure rates.

Benchmark Metrics:
- Latency: avg/median/p95/p99 for record_failure/record_success operations
- Memory: growth during persistent data writes
- Concurrency: command handling capacity (threads)
- Resilience: failure rate before system degradation
"""

import time
import threading
import psutil
import tracemalloc
import statistics
import concurrent.futures
import subprocess
import sys
import os
from typing import List, Dict, Any, Tuple
import json

# Add current directory to sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import CommandFailureTracker, execute_command_with_tracking, CommandFailureLimitExceeded


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite for CommandFailureTracker."""

    def __init__(self, test_data_file: str = 'benchmark_persistent_memory.md'):
        self.test_data_file = test_data_file
        self.tracker = CommandFailureTracker(test_data_file)

        # Benchmark metrics storage
        self.latency_results = {
            'record_failure': [],
            'record_success': [],
            'execute_command_success': [],
            'execute_command_failure': [],
            'persistent_write': []
        }
        self.memory_results = {
            'initial': 0,
            'peak_during_writes': [],
            'growth_per_write': []
        }
        self.concurrency_results = {
            'thread_capacity': 0,
            'throughput_per_thread': [],
            'errors_per_thread': []
        }
        self.resilience_results = {
            'degradation_threshold': 0,
            'failure_rates_tested': [],
            'system_stability': []
        }

    def setup_test_data(self):
        """Initialize test persistent data file."""
        with open(self.test_data_file, 'w') as f:
            f.write("# Non-Obvious Implementation Patterns\n\n")
            f.write("# Development & Debug Commands\n\n")
            f.write("# System Updates & Status\n")

    def teardown_test_data(self):
        """Clean up test files."""
        try:
            os.remove(self.test_data_file)
        except FileNotFoundError:
            pass

    def measure_latency(self, operation_name: str, operation_func, *args, **kwargs) -> float:
        """Measure execution time of an operation."""
        start = time.perf_counter()
        result = operation_func(*args, **kwargs)
        end = time.perf_counter()
        latency = (end - start) * 1000  # Convert to milliseconds
        self.latency_results[operation_name].append(latency)
        return result

    def benchmark_record_operations(self, iterations: int = 10000):
        """Benchmark record_failure and record_success latency."""
        print(f"Benchmarking record operations with {iterations} iterations...")

        # Reset tracker state
        tracker = CommandFailureTracker(self.test_data_file)

        # Benchmark record_failure (without triggering limit)
        for i in range(iterations):
            if tracker.consecutive_failures < 2:  # Prevent reaching limit
                self.measure_latency('record_failure', tracker.record_failure, f"cmd_{i}", f"context_{i}")
            else:
                tracker.record_success("reset_cmd")  # Reset to continue testing

        # Reset for success testing
        tracker = CommandFailureTracker(self.test_data_file)

        # Benchmark record_success
        for i in range(iterations):
            self.measure_latency('record_success', tracker.record_success, f"success_cmd_{i}")

        print("Record operations benchmark complete.")

    def benchmark_persistent_writes(self, iterations: int = 100):
        """Benchmark persistent data write performance and memory usage."""
        print(f"Benchmarking persistent writes with {iterations} iterations...")

        tracemalloc.start()

        # Create a custom tracker class that allows benchmarking without exception limits
        class BenchmarkCommandFailureTracker(CommandFailureTracker):
            def record_failure(self, command, context=""):
                with self._lock:
                    self.consecutive_failures += 1
                    self.failed_commands.append(command)
                    self.last_failure_context = context
                    # Always set limit_reached after 3 failures for benchmarking
                    if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                        self.limit_reached = True
                        # Don't raise exception for benchmarking - just set the flag

        tracker = BenchmarkCommandFailureTracker(self.test_data_file)

        # Force multiple limit exceedances to trigger writes
        for i in range(iterations):
            # Reach limit efficiently to trigger writes
            tracker.record_failure(f"fail_cmd_{i}_1", f"context_{i}")
            tracker.record_failure(f"fail_cmd_{i}_2", f"context_{i}")
            tracker.record_failure(f"fail_cmd_{i}_3", f"context_{i}")  # This sets limit_reached

            # Measure memory before success (with bounds checking)
            current_mem = tracemalloc.get_traced_memory()[1]
            if len(self.memory_results['growth_per_write']) < 1000:  # Bound memory storage
                self.memory_results['growth_per_write'].append(current_mem)

            # Trigger write and measure latency - record_success will write when limit_reached is True
            self.measure_latency('persistent_write', tracker.record_success, f"success_cmd_{i}")

            # Track peak memory (with bounds checking)
            peak_mem = tracemalloc.get_traced_memory()[1]
            if len(self.memory_results['peak_during_writes']) < 1000:  # Bound memory storage
                self.memory_results['peak_during_writes'].append(peak_mem)

        tracemalloc.stop()
        print("Persistent writes benchmark complete.")

    def benchmark_concurrent_load(self, max_threads: int = 50, operations_per_thread: int = 100):
        """Benchmark concurrent command handling capacity using ThreadPoolExecutor."""
        print(f"Benchmarking concurrent load with up to {max_threads} threads...")

        def worker_task(thread_id: int) -> Dict[str, Any]:
            """Worker function for concurrent testing using ThreadPoolExecutor."""
            local_tracker = CommandFailureTracker(self.test_data_file)
            thread_results = {
                'thread_id': thread_id,
                'operations': 0,
                'errors': 0,
                'latency_sum': 0.0
            }

            for i in range(operations_per_thread):
                try:
                    # Simulate mix of success/failure operations with cross-platform valid commands
                    if i % 10 < 8:  # 80% success rate
                        start = time.perf_counter()
                        # Cross-platform command that reliably succeeds on all systems
                        if os.name == 'nt':  # Windows
                            result = subprocess.run(['cmd', '/c', 'echo', 'test'],
                                                  capture_output=True, text=True, timeout=10)
                        else:  # Unix-like systems
                            result = subprocess.run(['echo', 'test'],
                                                  capture_output=True, text=True, timeout=10)
                        latency = (time.perf_counter() - start) * 1000
                        if result.returncode == 0:
                            local_tracker.record_success(f"echo test {thread_id}_{i}")
                        else:
                            local_tracker.record_failure(f"echo test {thread_id}_{i}", f"thread_{thread_id}")
                    else:
                        # Simulate controlled failure - just call record_failure directly to avoid subprocess overhead
                        local_tracker.record_failure(f"simulated_failure_{thread_id}_{i}", f"thread_{thread_id}")

                    thread_results['latency_sum'] += latency
                    thread_results['operations'] += 1

                except subprocess.TimeoutExpired:
                    thread_results['errors'] += 1
                    local_tracker.record_failure(f"timeout_cmd_{thread_id}_{i}", f"thread_{thread_id}")
                except Exception as e:
                    thread_results['errors'] += 1

            return thread_results

        # Test different thread counts to find capacity using ThreadPoolExecutor
        for thread_count in range(1, max_threads + 1, 5):
            start_time = time.time()

            # Use ThreadPoolExecutor for proper thread pool management
            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count, thread_name_prefix='benchmark') as executor:
                # Submit all tasks
                future_tasks = [executor.submit(worker_task, t) for t in range(thread_count)]

                # Collect results with timeout handling
                results = []
                for future in concurrent.futures.as_completed(future_tasks, timeout=60):  # 60 second total timeout
                    try:
                        result = future.result(timeout=30)  # 30 second per task timeout
                        results.append(result)
                    except concurrent.futures.TimeoutError:
                        # Handle timeout scenarios properly
                        print(f"Warning: Task timed out in thread pool execution")
                        results.append({
                            'thread_id': -1,  # Invalid thread ID to indicate timeout
                            'operations': 0,
                            'errors': 1,
                            'latency_sum': 0.0
                        })
                    except Exception as e:
                        # Handle other exceptions
                        print(f"Warning: Task failed with exception: {e}")
                        results.append({
                            'thread_id': -1,
                            'operations': 0,
                            'errors': 1,
                            'latency_sum': 0.0
                        })

            elapsed = time.time() - start_time
            total_operations = sum(r['operations'] for r in results)
            total_errors = sum(r['errors'] for r in results)
            avg_latency = sum(r['latency_sum'] / r['operations'] if r['operations'] > 0 else 0 for r in results) / len(results)

            throughput = total_operations / elapsed if elapsed > 0 else 0

            self.concurrency_results['throughput_per_thread'].append({
                'threads': thread_count,
                'throughput_ops_sec': throughput,
                'avg_latency_ms': avg_latency,
                'error_rate': total_errors / (total_operations + total_errors) if (total_operations + total_errors) > 0 else 0
            })

            # Stop increasing if throughput starts degrading significantly
            if len(self.concurrency_results['throughput_per_thread']) > 1:
                prev_throughput = self.concurrency_results['throughput_per_thread'][-2]['throughput_ops_sec']
                if throughput < prev_throughput * 0.8:  # 20% degradation threshold
                    self.concurrency_results['thread_capacity'] = thread_count - 5
                    break

        self.concurrency_results['thread_capacity'] = self.concurrency_results.get('thread_capacity', max_threads)
        print("Concurrent load benchmark complete.")

    def benchmark_failure_resilience(self, failure_rates: List[float] = [0.1, 0.25, 0.5, 0.75, 0.9, 0.95]):
        """Benchmark system resilience under different failure rates."""
        print("Benchmarking failure resilience across different failure rates...")

        for failure_rate in failure_rates:
            print(f"  Testing failure rate: {failure_rate}")

            tracker = CommandFailureTracker(self.test_data_file)
            operations = 1000
            successful_ops = 0
            failed_ops = 0
            degradation_indicators = []

            for i in range(operations):
                try:
                    if i / operations < failure_rate:
                        # Simulate failure
                        tracker.record_failure(f"fail_cmd_{i}", f"resilience_test_{failure_rate}")
                        failed_ops += 1
                        if tracker.consecutive_failures >= 2:
                            degradation_indicators.append(1)
                        else:
                            degradation_indicators.append(0)
                    else:
                        # Simulate success
                        tracker.record_success(f"success_cmd_{i}")
                        successful_ops += 1
                        degradation_indicators.append(0)

                    # Check for system stress indicators
                    if len(tracker.failed_commands) > 5:
                        degradation_indicators[-1] = 2  # High stress

                except CommandFailureLimitExceeded:
                    # Recovery simulation
                    tracker.record_success("recovery_cmd")
                    degradation_indicators.append(3)  # Full degradation

            # Calculate degradation threshold (point where system shows signs of stress)
            degradation_threshold = sum(1 for d in degradation_indicators if d > 0) / len(degradation_indicators)

            self.resilience_results['failure_rates_tested'].append({
                'failure_rate': failure_rate,
                'degradation_threshold': degradation_threshold,
                'successful_operations': successful_ops,
                'failed_operations': failed_ops,
                'recovery_events': sum(1 for d in degradation_indicators if d == 3)
            })

            # Stop if system is completely degraded
            if degradation_threshold > 0.5:
                self.resilience_results['degradation_threshold'] = failure_rate
                break

        print("Failure resilience benchmark complete.")

    def analyze_latency_results(self) -> Dict[str, Any]:
        """Analyze latency measurements with bounded memory usage."""
        analysis = {}

        for operation, latencies in self.latency_results.items():
            if latencies:
                # Limit latency storage to prevent memory issues
                if len(latencies) > 10000:  # Reasonable bound for analysis
                    latencies = latencies[-10000:]  # Keep most recent measurements

                sorted_latencies = sorted(latencies)
                analysis[operation] = {
                    'count': len(latencies),
                    'avg_ms': statistics.mean(latencies),
                    'median_ms': statistics.median(sorted_latencies),
                    'p95_ms': sorted_latencies[int(len(sorted_latencies) * 0.95)],
                    'p99_ms': sorted_latencies[int(len(sorted_latencies) * 0.99)],
                    'min_ms': min(latencies),
                    'max_ms': max(latencies)
                }

        return analysis

    def analyze_memory_results(self) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        return {
            'initial_memory_mb': self.memory_results['initial'] / (1024 * 1024),
            'avg_peak_memory_mb': statistics.mean(self.memory_results['peak_during_writes']) / (1024 * 1024) if self.memory_results['peak_during_writes'] else 0,
            'max_peak_memory_mb': max(self.memory_results['peak_during_writes']) / (1024 * 1024) if self.memory_results['peak_during_writes'] else 0,
            'avg_growth_per_write_mb': statistics.mean(self.memory_results['growth_per_write']) / (1024 * 1024) if self.memory_results['growth_per_write'] else 0,
            'memory_efficiency': 'Good' if len(self.memory_results['growth_per_write']) == 0 or statistics.mean(self.memory_results['growth_per_write']) < 10 * 1024 * 1024 else 'Needs optimization'
        }

    def analyze_concurrency_results(self) -> Dict[str, Any]:
        """Analyze concurrent load testing results."""
        if not self.concurrency_results['throughput_per_thread']:
            return {'thread_capacity': 0, 'max_throughput': 0}

        max_throughput_result = max(self.concurrency_results['throughput_per_thread'],
                                   key=lambda x: x['throughput_ops_sec'])

        return {
            'thread_capacity': self.concurrency_results['thread_capacity'],
            'max_throughput_ops_sec': max_throughput_result['throughput_ops_sec'],
            'optimal_threads': max_throughput_result['threads'],
            'avg_latency_at_peak_ms': max_throughput_result['avg_latency_ms'],
            'error_rate_at_peak': max_throughput_result['error_rate'],
            'scalability': 'Good' if max_throughput_result['error_rate'] < 0.1 else 'Needs optimization'
        }

    def analyze_resilience_results(self) -> Dict[str, Any]:
        """Analyze stress testing results."""
        if not self.resilience_results['failure_rates_tested']:
            return {'degradation_threshold': 1.0}

        return {
            'degradation_threshold': self.resilience_results['degradation_threshold'],
            'max_failure_rate_handled': max(r['failure_rate'] for r in self.resilience_results['failure_rates_tested']
                                           if r['degradation_threshold'] < 0.5),
            'recovery_events_total': sum(r['recovery_events'] for r in self.resilience_results['failure_rates_tested']),
            'resilience_rating': 'Excellent' if self.resilience_results['degradation_threshold'] > 0.8 else
                                'Good' if self.resilience_results['degradation_threshold'] > 0.6 else
                                'Needs improvement'
        }

    def run_complete_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark suite."""
        print("Starting comprehensive CommandFailureTracker performance benchmark...")
        print("=" * 80)

        self.setup_test_data()
        tracemalloc.start()
        self.memory_results['initial'] = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        try:
            # Run all benchmark tests
            self.benchmark_record_operations()
            self.benchmark_persistent_writes()
            self.benchmark_concurrent_load()
            self.benchmark_failure_resilience()

            # Analyze results
            results = {
                'timestamp': time.time(),
                'latency_analysis': self.analyze_latency_results(),
                'memory_analysis': self.analyze_memory_results(),
                'concurrency_analysis': self.analyze_concurrency_results(),
                'resilience_analysis': self.analyze_resilience_results(),
                'summary': {
                    'total_operations_tested': sum(len(latencies) for latencies in self.latency_results.values()),
                    'benchmark_duration_sec': time.time() - time.time(),  # Will be set by caller
                    'system_info': {
                        'python_version': sys.version,
                        'cpu_count': os.cpu_count(),
                        'platform': sys.platform
                    }
                }
            }

            print("=" * 80)
            print("BENCHMARK RESULTS SUMMARY")
            print("=" * 80)
            print(json.dumps(results, indent=2))

            return results

        finally:
            self.teardown_test_data()

    def save_results_to_file(self, results: Dict[str, Any], filename: str = 'benchmark_results.json'):
        """Save benchmark results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")


def main():
    """Main benchmark execution function."""
    benchmark = PerformanceBenchmark()

    start_time = time.time()
    results = benchmark.run_complete_benchmark()
    end_time = time.time()

    results['summary']['benchmark_duration_sec'] = end_time - start_time

    # Save results
    benchmark.save_results_to_file(results)

    # Print key metrics
    print("\nKEY PERFORMANCE METRICS:")
    print("-" * 40)
    if 'record_failure' in results['latency_analysis']:
        lat = results['latency_analysis']['record_failure']
        print(".3f")
        print(".3f")
        print(".3f")

    if 'persistent_write' in results['latency_analysis']:
        lat = results['latency_analysis']['persistent_write']
        print(".3f")

    mem = results['memory_analysis']
    print(".2f")

    conc = results['concurrency_analysis']
    print(f"Thread Capacity: {conc['thread_capacity']}")
    print(".1f")

    res = results['resilience_analysis']
    print(".1%")
    print(f"Resilience Rating: {res['resilience_rating']}")

    print(".2f")


if __name__ == '__main__':
    main()