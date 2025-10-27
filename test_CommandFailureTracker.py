import unittest
from unittest.mock import mock_open, patch, MagicMock
import sys
import os

# Add the current directory to sys.path to import orchestrator
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import CommandFailureTracker, CommandFailureLimitExceeded

class TestCommandFailureTracker(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tracker = CommandFailureTracker()

    def test_initialization(self):
        """Test that the tracker initializes with correct default values."""
        self.assertEqual(self.tracker.consecutive_failures, 0)
        self.assertEqual(self.tracker.failed_commands, [])
        self.assertEqual(self.tracker.last_failure_context, "")
        self.assertFalse(self.tracker.limit_reached)
        self.assertEqual(self.tracker.persistent_data_file, 'persistent-memory.md')

    def test_record_failure_increments_counter(self):
        """Test that recording a failure increments the counter and stores command/context."""
        self.tracker.record_failure("command1", "context1")
        self.assertEqual(self.tracker.consecutive_failures, 1)
        self.assertEqual(self.tracker.failed_commands, ["command1"])
        self.assertEqual(self.tracker.last_failure_context, "context1")

    def test_record_failure_multiple(self):
        """Test multiple failures accumulate correctly."""
        self.tracker.record_failure("cmd1", "ctx1")
        self.tracker.record_failure("cmd2", "ctx2")
        self.assertEqual(self.tracker.consecutive_failures, 2)
        self.assertEqual(self.tracker.failed_commands, ["cmd1", "cmd2"])
        self.assertEqual(self.tracker.last_failure_context, "ctx2")

    def test_record_failure_limit_exceeded(self):
        """Test that the 3rd failure raises CommandFailureLimitExceeded."""
        self.tracker.record_failure("cmd1")
        self.tracker.record_failure("cmd2")
        with self.assertRaises(CommandFailureLimitExceeded) as cm:
            self.tracker.record_failure("cmd3")
        self.assertIn("3", str(cm.exception))
        self.assertEqual(self.tracker.consecutive_failures, 3)
        self.assertTrue(self.tracker.limit_reached)

    def test_record_success_resets_counter(self):
        """Test that recording success resets the counter and clears lists."""
        self.tracker.record_failure("cmd1")
        self.tracker.record_failure("cmd2")
        self.tracker.record_success("success_cmd")
        self.assertEqual(self.tracker.consecutive_failures, 0)
        self.assertEqual(self.tracker.failed_commands, [])
        self.assertEqual(self.tracker.last_failure_context, "")
        self.assertFalse(self.tracker.limit_reached)

    @patch('builtins.open', new_callable=mock_open)
    def test_record_success_after_limit_writes_debug_entry(self, mock_file):
        """Test that success after limit reached writes debug entry and resets."""
        self.tracker.record_failure("cmd1")
        self.tracker.record_failure("cmd2")
        try:
            self.tracker.record_failure("cmd3")  # This should set limit_reached
        except CommandFailureLimitExceeded:
            pass
        self.assertTrue(self.tracker.limit_reached)

        # Mock the file read to return some content with the section
        mock_file.return_value.readlines.return_value = [
            "# Non-Obvious Implementation Patterns\n",
            "# Development & Debug Commands\n",
            "Some existing content\n",
            "# System Updates & Status\n"
        ]

        self.tracker.record_success("success_cmd")

        # Verify file was written
        mock_file.assert_called()
        # The write method is called with writelines, so call.args[0] is the list of lines
        written_lines = []
        for call in mock_file().writelines.call_args_list:
            written_lines.extend(call[0])  # call[0] is the list of lines
        # Flatten any nested lists and join
        flat_lines = []
        for line in written_lines:
            if isinstance(line, list):
                flat_lines.extend(line)
            else:
                flat_lines.append(line)
        written_content = ''.join(flat_lines)
        self.assertIn("Command Failure Recovery", written_content)
        self.assertIn("cmd1", written_content)
        self.assertIn("cmd2", written_content)
        self.assertIn("cmd3", written_content)
        self.assertIn("success_cmd", written_content)

        # Verify reset
        self.assertEqual(self.tracker.consecutive_failures, 0)
        self.assertEqual(self.tracker.failed_commands, [])
        self.assertEqual(self.tracker.last_failure_context, "")
        self.assertFalse(self.tracker.limit_reached)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_debug_entry_file_not_found(self, mock_file):
        """Test _write_debug_entry when file does not exist (appends at end)."""
        mock_file.side_effect = FileNotFoundError
        self.tracker._write_debug_entry("success_cmd")
        # Should not raise, just print error (mock print if needed, but for now assume it handles)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_debug_entry_section_not_found(self, mock_file):
        """Test _write_debug_entry when section not found, appends new section."""
        mock_file.return_value.readlines.return_value = ["# Non-Obvious\n", "# System Updates\n"]

        self.tracker._write_debug_entry("success_cmd")

        # Check that new section was added
        # Note: writelines is used, so check writelines calls
        written_lines = []
        for call in mock_file().writelines.call_args_list:
            written_lines.extend(call[0])  # extend with the list of lines
        # Flatten any nested lists and join
        flat_lines = []
        for line in written_lines:
            if isinstance(line, list):
                flat_lines.extend(line)
            else:
                flat_lines.append(line)
        written_content = ''.join(flat_lines)
        self.assertIn("# Development & Debug Commands\n", written_content)
        self.assertIn("Command Failure Recovery", written_content)

    def test_record_failure_with_list_command(self):
        """Test recording failure with list command (stores as list)."""
        self.tracker.record_failure(["cmd", "arg"], "context")
        self.assertEqual(self.tracker.failed_commands, [["cmd", "arg"]])

    def test_record_success_with_list_command(self):
        """Test recording success with list command."""
        self.tracker.record_success(["cmd", "arg"])
        # No assert needed beyond no exception

    def test_edge_case_success_without_failures(self):
        """Test success reset works even without prior failures."""
        self.tracker.record_success("cmd")
        self.assertEqual(self.tracker.consecutive_failures, 0)

    def test_limit_reached_flag_behavior(self):
        """Test limit_reached flag is set and reset appropriately."""
        self.assertFalse(self.tracker.limit_reached)
        self.tracker.record_failure("cmd1")
        self.tracker.record_failure("cmd2")
        try:
            self.tracker.record_failure("cmd3")  # Sets limit_reached but raises exception
        except CommandFailureLimitExceeded:
            pass  # Expected
        self.assertTrue(self.tracker.limit_reached)
        # After success, should reset
        self.tracker.record_success("cmd")
        self.assertFalse(self.tracker.limit_reached)

if __name__ == '__main__':
    unittest.main()