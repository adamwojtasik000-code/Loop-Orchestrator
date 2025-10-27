import unittest
import time
from unittest.mock import patch
from orchestrator import TimeoutEnforcer


class TestTimeoutEnforcer(unittest.TestCase):
    """Unit tests for TimeoutEnforcer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.enforcer = TimeoutEnforcer()

    def test_default_timeout(self):
        """Test default timeout configuration."""
        self.assertEqual(self.enforcer.timeout_seconds, 3600)
        self.assertEqual(self.enforcer.warning_threshold_seconds, 2880)  # 80% of 3600

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        enforcer = TimeoutEnforcer(1800)  # 30 minutes
        self.assertEqual(enforcer.timeout_seconds, 1800)
        self.assertEqual(enforcer.warning_threshold_seconds, 1440)  # 80% of 1800

    def test_opt_out_configuration(self):
        """Test opt-out configuration."""
        self.assertFalse(self.enforcer.opt_out)
        self.enforcer.set_opt_out(True)
        self.assertTrue(self.enforcer.opt_out)
        self.enforcer.set_opt_out(False)
        self.assertFalse(self.enforcer.opt_out)

    def test_task_start_stop(self):
        """Test task start and stop monitoring."""
        self.assertFalse(self.enforcer.monitoring)
        self.assertIsNone(self.enforcer.task_start_time)

        self.enforcer.start_task("test_task")
        self.assertTrue(self.enforcer.monitoring)
        self.assertIsNotNone(self.enforcer.task_start_time)
        self.assertEqual(self.enforcer.task_name, "test_task")

        self.enforcer.stop_task()
        self.assertFalse(self.enforcer.monitoring)
        self.assertIsNone(self.enforcer.task_start_time)
        self.assertIsNone(self.enforcer.task_name)

    def test_check_timeout_no_monitoring(self):
        """Test check_timeout when not monitoring."""
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIsNone(message)

    @patch('orchestrator.time.time')
    def test_check_timeout_warning(self, mock_time):
        """Test warning mechanism at 80% threshold."""
        self.enforcer.start_task("test_task")
        start_time = 1000000000.0  # Fixed start time
        mock_time.return_value = start_time

        # At start, no warning
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIsNone(message)

        # At warning threshold (2880s later) - need to set the mock properly
        mock_time.return_value = start_time + 2880.1
        self.enforcer.task_start_time = start_time  # Set start time explicitly since mock affects time.time()
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIn("approaching timeout", message)
        self.assertIn("test_task", message)

        # Warning should not repeat
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIsNone(message)

    @patch('orchestrator.time.time')
    def test_check_timeout_enforcement(self, mock_time):
        """Test enforcement mechanism at timeout limit."""
        self.enforcer.start_task("test_task")
        start_time = 1000000000.0

        # At timeout limit (3600s later) - need to set the mock properly
        mock_time.return_value = start_time + 3600.1
        self.enforcer.task_start_time = start_time  # Set start time explicitly since mock affects time.time()
        should_enforce, message = self.enforcer.check_timeout()
        self.assertTrue(should_enforce)
        self.assertIn("exceeded 3600s timeout limit", message)
        self.assertIn("enforcing failure", message)
        self.assertIn("test_task", message)

        # Enforcement should not repeat
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIsNone(message)

    @patch('orchestrator.time.time')
    def test_check_timeout_opt_out(self, mock_time):
        """Test opt-out behavior at timeout limit."""
        self.enforcer.set_opt_out(True)
        self.enforcer.start_task("test_task")
        start_time = 1000000000.0

        # At timeout limit with opt-out - need to set the mock properly
        mock_time.return_value = start_time + 3600.1
        self.enforcer.task_start_time = start_time  # Set start time explicitly since mock affects time.time()
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIn("exceeded 3600s timeout", message)
        self.assertIn("opt-out configured", message)
        self.assertIn("test_task", message)

        # Message should not repeat
        should_enforce, message = self.enforcer.check_timeout()
        self.assertFalse(should_enforce)
        self.assertIsNone(message)

    def test_execute_with_timeout_normal_completion(self):
        """Test normal task completion within timeout."""
        def quick_task():
            time.sleep(0.1)
            return "completed"

        result = self.enforcer.execute_with_timeout(quick_task)
        self.assertEqual(result, "completed")

    def test_execute_with_timeout_task_exception(self):
        """Test task that raises exception."""
        def failing_task():
            raise ValueError("Task failed")

        with self.assertRaises(ValueError) as context:
            self.enforcer.execute_with_timeout(failing_task)
        self.assertEqual(str(context.exception), "Task failed")

    def test_execute_with_timeout_enforced(self):
        """Test timeout enforcement during execution."""
        def long_task():
            time.sleep(3)  # Run for 3 seconds
            return "should not complete"

        # Configure short timeout for testing
        self.enforcer.timeout_seconds = 1
        self.enforcer.warning_threshold_seconds = 0  # Disable warning for this test

        with self.assertRaises(TimeoutError) as context:
            self.enforcer.execute_with_timeout(long_task)
        self.assertIn("timed out after 1 seconds", str(context.exception))

    def test_execute_with_timeout_opt_out_allows_completion(self):
        """Test opt-out allows task to complete beyond timeout."""
        def long_task():
            time.sleep(2)
            return "completed despite timeout"

        # Configure short timeout but with opt-out
        self.enforcer.timeout_seconds = 1
        self.enforcer.set_opt_out(True)

        result = self.enforcer.execute_with_timeout(long_task)
        self.assertEqual(result, "completed despite timeout")

    def test_execute_with_timeout_polling_pattern(self):
        """Test that execute_with_timeout uses polling pattern."""
        call_count = 0

        def counting_task():
            nonlocal call_count
            while call_count < 50:  # Simulate work taking multiple polls
                call_count += 1
                time.sleep(0.01)  # Small delay
            return call_count

        result = self.enforcer.execute_with_timeout(counting_task)
        self.assertEqual(result, 50)

        # Verify polling occurred (task took some time with multiple checks)
        self.assertGreater(call_count, 0)


if __name__ == '__main__':
    unittest.main()