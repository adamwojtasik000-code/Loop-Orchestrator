#!/usr/bin/env python3
"""
Test script to validate data model fixes for critical validation failures.
"""

import json
import sys
import os
from pathlib import Path

# Add the mcp_server to the path
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))

from models import ScheduleData, TaskTimingContainer, ModeCapabilities

def test_schedule_data_parsing():
    """Test ScheduleData model with actual schedules.json data."""
    print("Testing ScheduleData model parsing...")
    
    try:
        # Load actual schedules.json
        schedules_file = Path(".roo/schedules.json")
        if schedules_file.exists():
            with open(schedules_file) as f:
                data = json.load(f)
            
            print(f"Loaded schedules.json with {len(data.get('schedules', []))} schedules")
            
            # Test parsing each schedule
            for schedule_data in data.get("schedules", []):
                try:
                    schedule = ScheduleData(**schedule_data)
                    print(f"✓ Successfully parsed schedule: {schedule.name}")
                    print(f"  - Schedule Type: {schedule.scheduleType}")
                    print(f"  - Time Interval: {schedule.timeInterval}")
                    print(f"  - Active: {schedule.active}")
                except Exception as e:
                    print(f"✗ Failed to parse schedule {schedule_data.get('id', 'unknown')}: {e}")
                    return False
            
            print("✓ All schedules parsed successfully!")
            return True
        else:
            print("✗ schedules.json not found")
            return False
            
    except Exception as e:
        print(f"✗ ScheduleData parsing failed: {e}")
        return False

def test_time_tracking_parsing():
    """Test time tracking parsing with non-numeric values."""
    print("\nTesting time tracking parsing...")
    
    # Test TSV content with problematic data
    test_tsv_content = """timestamp	mode	task_id	start_time	end_time	duration	task	result	priority
2023-01-01T00:00:00Z	test-mode	task-123	2023-01-01T00:00:00Z	2023-01-01T00:01:00Z	60	test task	completed	normal
2023-01-01T00:01:00Z	test-mode	task-124	2023-01-01T00:01:00Z		invalid	test task 2	started	normal
2023-01-01T00:02:00Z	test-mode	task-125	2023-01-01T00:02:00Z	2023-01-01T00:02:30Z	30	test task 3	completed	normal
"""
    
    try:
        container = TaskTimingContainer.from_tsv(test_tsv_content)
        print(f"✓ Parsed {len(container.entries)} time tracking entries")
        
        for i, entry in enumerate(container.entries):
            print(f"  Entry {i+1}: {entry.task} - Duration: {entry.duration}")
        
        # Should have 3 entries, with the second one having None duration
        if len(container.entries) == 3 and container.entries[1].duration is None:
            print("✓ Time tracking parsing handles non-numeric values correctly!")
            return True
        else:
            print(f"✗ Expected 3 entries, got {len(container.entries)}")
            return False
            
    except Exception as e:
        print(f"✗ Time tracking parsing failed: {e}")
        return False

def test_mode_capabilities_parsing():
    """Test mode capabilities parsing with problematic JSON."""
    print("\nTesting mode capabilities parsing...")
    
    # Test with various problematic data formats
    test_cases = [
        # Case 1: Valid data
        {
            "customModes": {
                "test-mode": {
                    "name": "Test Mode",
                    "description": "A test mode for testing"
                }
            }
        },
        # Case 2: Invalid customModes format
        {
            "customModes": "invalid_format"
        },
        # Case 3: Empty customModes
        {
            "customModes": {}
        },
        # Case 4: Missing required fields
        {
            "customModes": {
                "bad-mode": {
                    "name": "Bad Mode"
                    # missing description
                }
            }
        }
    ]
    
    try:
        for i, test_data in enumerate(test_cases):
            print(f"  Test case {i+1}: {test_data}")
            try:
                capabilities = ModeCapabilities.from_dict(test_data)
                print(f"  ✓ Test case {i+1} parsed successfully: {len(capabilities.modes)} modes")
            except Exception as e:
                print(f"  ✗ Test case {i+1} failed: {e}")
                return False
        
        print("✓ Mode capabilities parsing handles all error cases gracefully!")
        return True
        
    except Exception as e:
        print(f"✗ Mode capabilities parsing failed: {e}")
        return False

def test_field_validators():
    """Test individual field validators."""
    print("\nTesting field validators...")
    
    try:
        # Test time interval validation
        print("  Testing time interval validation...")
        test_data = {
            "id": "test",
            "name": "Test",
            "mode": "test",
            "taskInstructions": "test",
            "scheduleType": "time",
            "timeInterval": "10",  # String should be converted to int
            "startMinute": "00",
            "createdAt": "2023-01-01T00:00:00Z",
            "updatedAt": "2023-01-01T00:00:00Z"
        }
        
        schedule = ScheduleData(**test_data)
        assert schedule.timeInterval == 10, f"Expected 10, got {schedule.timeInterval}"
        print("  ✓ Time interval string-to-int conversion works")
        
        # Test invalid time interval
        try:
            invalid_data = test_data.copy()
            invalid_data["timeInterval"] = "invalid"
            ScheduleData(**invalid_data)
            print("  ✗ Should have failed with invalid time interval")
            return False
        except ValueError:
            print("  ✓ Invalid time interval properly rejected")
        
        # Test schedule type validation
        test_data["scheduleType"] = "TIME"  # Should be converted to enum
        schedule = ScheduleData(**test_data)
        print(f"  ✓ Schedule type conversion works: {schedule.scheduleType}")
        
        print("✓ All field validators working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Field validator testing failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🔍 Data Model Validation Tests")
    print("=" * 40)
    
    tests = [
        ("Schedule Data Parsing", test_schedule_data_parsing),
        ("Time Tracking Parsing", test_time_tracking_parsing),
        ("Mode Capabilities Parsing", test_mode_capabilities_parsing),
        ("Field Validators", test_field_validators),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("🎉 All data model validation failures have been FIXED!")
        return True
    else:
        print("⚠️  Some issues remain - further investigation needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)