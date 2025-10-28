"""
Security-focused unit tests for SphericalCoordinate class.
Tests vulnerabilities identified in static analysis:
- Input validation bypasses
- NaN/infinite value handling
- Floating-point precision issues
- Coordinate validation bypasses
- DoS attack vectors
- Type safety issues
"""

import unittest
import numpy as np
import time
from src.spherical_coordinates import SphericalCoordinate


class TestSphericalCoordinateSecurity(unittest.TestCase):
    """Comprehensive security test suite for SphericalCoordinate class."""

    def test_nan_infinite_inputs_constructor(self):
        """Test that NaN and infinite values are rejected in constructor."""
        # NaN values should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate(float('nan'), 0.0, 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, float('nan'), 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, 0.0, float('nan'))

        # Infinite values should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate(float('inf'), 0.0, 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, float('-inf'), 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, 0.0, float('inf'))

    def test_nan_infinite_inputs_from_cartesian(self):
        """Test that NaN and infinite values are rejected in from_cartesian."""
        # NaN coordinates should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(float('nan'), 0.0, 0.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(0.0, float('nan'), 0.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(0.0, 0.0, float('nan'))

        # Infinite coordinates should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(float('inf'), 0.0, 0.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(0.0, float('-inf'), 0.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate.from_cartesian(0.0, 0.0, float('inf'))

    def test_type_safety_constructor(self):
        """Test that non-numeric types are rejected in constructor."""
        # String inputs should be rejected
        with self.assertRaises(TypeError):
            SphericalCoordinate("0.0", 0.0, 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, "0.0", 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, 0.0, "1.0")

        # None inputs should be rejected
        with self.assertRaises(TypeError):
            SphericalCoordinate(None, 0.0, 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, None, 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, 0.0, None)

        # List inputs should be rejected
        with self.assertRaises(TypeError):
            SphericalCoordinate([0.0], 0.0, 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, [0.0], 1.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate(0.0, 0.0, [1.0])

    def test_type_safety_from_cartesian(self):
        """Test that non-numeric types are rejected in from_cartesian."""
        # String coordinates should be rejected
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian("0.0", 0.0, 0.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian(0.0, "0.0", 0.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian(0.0, 0.0, "0.0")

        # None coordinates should be rejected
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian(None, 0.0, 0.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian(0.0, None, 0.0)
        with self.assertRaises(TypeError):
            SphericalCoordinate.from_cartesian(0.0, 0.0, None)

    def test_coordinate_validation_bypass_negative_z(self):
        """Test that negative z-axis points cannot bypass validation."""
        # Points with negative z should properly calculate elevation
        coord = SphericalCoordinate.from_cartesian(0.0, 0.0, -1.0)
        self.assertEqual(coord.elevation, 180.0)  # Should be 180° for negative z-axis

        coord2 = SphericalCoordinate.from_cartesian(0.0, 0.0, -0.5)
        self.assertGreater(coord2.elevation, 90.0)  # Should be > 90° for negative z

    def test_floating_point_precision_edge_cases(self):
        """Test floating-point precision issues and edge cases."""
        # Very small values near origin
        coord = SphericalCoordinate.from_cartesian(1e-15, 1e-15, 1e-15)
        self.assertTrue(np.isfinite(coord.azimuth))
        self.assertTrue(np.isfinite(coord.elevation))
        self.assertTrue(np.isfinite(coord.radius))

        # Very large values (within floating-point limits)
        large_val = 1e10
        coord2 = SphericalCoordinate.from_cartesian(large_val, large_val, large_val)
        self.assertTrue(np.isfinite(coord2.azimuth))
        self.assertTrue(np.isfinite(coord2.elevation))
        self.assertTrue(np.isfinite(coord2.radius))

    def test_arithmetic_overflow_protection(self):
        """Test protection against arithmetic overflows."""
        # Values that could cause overflow in calculations
        max_float = np.finfo(np.float64).max
        large_coords = [max_float * 0.1, max_float * 0.1, max_float * 0.1]

        # Should handle gracefully or raise appropriate errors
        try:
            coord = SphericalCoordinate.from_cartesian(*large_coords)
            # If successful, results should be finite
            self.assertTrue(np.isfinite(coord.radius))
        except (ValueError, OverflowError):
            # Acceptable to raise error for extreme values
            pass

    def test_dos_protection_constructor(self):
        """Test DoS protection in constructor."""
        # Normal operation should work
        start_time = time.time()
        coord = SphericalCoordinate(0.0, 0.0, 1.0)
        self.assertLess(time.time() - start_time, 0.1)  # Should be fast

        # Validation should still be time-bounded
        # (Testing timeout would require mocking time, but structure is in place)

    def test_dos_protection_from_cartesian(self):
        """Test DoS protection in from_cartesian conversion."""
        # Normal operation should work
        start_time = time.time()
        coord = SphericalCoordinate.from_cartesian(1.0, 1.0, 1.0)
        self.assertLess(time.time() - start_time, 0.1)  # Should be fast

        # Complex calculations should still be bounded
        # (Testing timeout would require mocking time, but structure is in place)

    def test_origin_handling(self):
        """Test proper handling of origin point (0,0,0)."""
        coord = SphericalCoordinate.from_cartesian(0.0, 0.0, 0.0)
        self.assertEqual(coord.azimuth, 0.0)
        self.assertEqual(coord.elevation, 0.0)
        self.assertEqual(coord.radius, 0.0)

    def test_azimuth_range_normalization(self):
        """Test that azimuth angles are properly normalized to [0, 360)."""
        # Test negative azimuth from arctan2
        coord = SphericalCoordinate.from_cartesian(-1.0, 0.0, 0.0)
        self.assertAlmostEqual(coord.azimuth, 180.0, places=5)

        coord2 = SphericalCoordinate.from_cartesian(-1.0, -1.0, 0.0)
        self.assertGreaterEqual(coord2.azimuth, 0.0)
        self.assertLess(coord2.azimuth, 360.0)

    def test_elevation_range_validation(self):
        """Test that elevation angles are properly validated."""
        # Valid elevations should work
        SphericalCoordinate(0.0, -90.0, 1.0)  # South pole
        SphericalCoordinate(0.0, 90.0, 1.0)   # North pole

        # Invalid elevations should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, -91.0, 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, 91.0, 1.0)

    def test_origin_special_case_constructor(self):
        """Test that origin point (0,0,0) is handled specially in constructor."""
        # Origin should be allowed in constructor when explicitly set
        coord = SphericalCoordinate(0.0, 0.0, 0.0)
        self.assertEqual(coord.azimuth, 0.0)
        self.assertEqual(coord.elevation, 0.0)
        self.assertEqual(coord.radius, 0.0)

    def test_azimuth_range_validation(self):
        """Test that azimuth angles are properly validated."""
        # Valid azimuths should work
        SphericalCoordinate(0.0, 0.0, 1.0)
        SphericalCoordinate(360.0, 0.0, 1.0)

        # Invalid azimuths should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate(-1.0, 0.0, 1.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(361.0, 0.0, 1.0)

    def test_radius_validation(self):
        """Test that radius values are properly validated."""
        # Valid radius should work
        SphericalCoordinate(0.0, 0.0, 1.0)
        SphericalCoordinate(0.0, 0.0, 0.1)

        # Invalid radius should be rejected
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            SphericalCoordinate(0.0, 0.0, -1.0)

    def test_cartesian_roundtrip_consistency(self):
        """Test that cartesian -> spherical -> cartesian conversion is consistent."""
        test_points = [
            (1.0, 0.0, 0.0),      # X-axis
            (0.0, 1.0, 0.0),      # Y-axis
            (0.0, 0.0, 1.0),      # Z-axis
            (1.0, 1.0, 1.0),      # Diagonal
            (1.0, 2.0, 3.0),      # General point
        ]

        for x, y, z in test_points:
            with self.subTest(x=x, y=y, z=z):
                # Convert to spherical and back
                spherical = SphericalCoordinate.from_cartesian(x, y, z)
                x2, y2, z2 = spherical.to_cartesian()

                # Should be approximately equal (within floating-point precision)
                self.assertAlmostEqual(x, x2, places=10)
                self.assertAlmostEqual(y, y2, places=10)
                self.assertAlmostEqual(z, z2, places=10)

    def test_angular_distance_edge_cases(self):
        """Test angular distance calculation with edge cases."""
        coord1 = SphericalCoordinate(0.0, 0.0, 1.0)
        coord2 = SphericalCoordinate(180.0, 0.0, 1.0)

        # Distance should be finite
        distance = coord1.angular_distance(coord2)
        self.assertTrue(np.isfinite(distance))
        self.assertGreaterEqual(distance, 0.0)
        self.assertLessEqual(distance, 180.0)

    def test_angular_distance_same_point(self):
        """Test angular distance between identical points."""
        coord = SphericalCoordinate(45.0, 30.0, 2.0)
        distance = coord.angular_distance(coord)
        self.assertAlmostEqual(distance, 0.0, places=10)


if __name__ == '__main__':
    unittest.main()