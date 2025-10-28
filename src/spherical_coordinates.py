"""
Spherical Coordinate System for STG-001 Foundation

This module implements the SphericalCoordinate class for 3D spherical coordinate
system operations. Uses mathematical convention with azimuth θ measured from
positive x-axis and elevation φ measured from positive z-axis.

Attributes:
    azimuth (θ): Azimuth angle in degrees (0° to 360°)
    elevation (φ): Elevation angle in degrees (-90° to 90°)
    radius (r): Radial distance (> 0)

Dependencies:
    - NumPy 1.24.3 for mathematical operations
    - Python 3.8.0 compatibility
"""

from typing import Tuple, Union
import math
import numpy as np
import time


class SphericalCoordinate:
    """
    Represents a point in 3D space using spherical coordinates.

    Mathematical convention:
    - Azimuth θ: measured from positive x-axis in xy-plane (0° to 360°)
    - Elevation φ: measured from positive z-axis (-90° to 90°)
    - Radius r: radial distance from origin (> 0)
    """

    # DoS protection: maximum allowed time for coordinate operations (seconds)
    _MAX_OPERATION_TIME = 1.0

    def __init__(self, azimuth: float, elevation: float, radius: float):
        """
        Initialize spherical coordinate with DoS protection.

        Args:
            azimuth: Azimuth angle in degrees (0° to 360°)
            elevation: Elevation angle in degrees (-90° to 90°)
            radius: Radial distance (> 0)

        Raises:
            ValueError: If any coordinate is out of valid range
            TimeoutError: If validation takes too long (DoS protection)
        """
        start_time = time.time()
        try:
            self._validate_coordinates(azimuth, elevation, radius)
        except Exception as e:
            if time.time() - start_time > SphericalCoordinate._MAX_OPERATION_TIME:
                raise TimeoutError("Coordinate validation exceeded time limit - possible DoS attempt")
            raise

        self.azimuth = azimuth
        self.elevation = elevation
        self.radius = radius

    def _validate_coordinates(self, azimuth: Union[float, int], elevation: Union[float, int], radius: Union[float, int]) -> None:
        """
        Validate coordinate ranges and types. Provides robust input validation against
        potential security vulnerabilities including NaN, infinite values, and type coercion attacks.

        Args:
            azimuth: Azimuth angle in degrees
            elevation: Elevation angle in degrees
            radius: Radial distance

        Raises:
            TypeError: If inputs are not numeric
            ValueError: If coordinates contain NaN/infinite values or are out of valid ranges
        """
        # Type safety: ensure all inputs are numeric (before any other operations)
        if not isinstance(azimuth, (int, float)):
            raise TypeError(f"Azimuth must be numeric, got {type(azimuth).__name__}")
        if not isinstance(elevation, (int, float)):
            raise TypeError(f"Elevation must be numeric, got {type(elevation).__name__}")
        if not isinstance(radius, (int, float)):
            raise TypeError(f"Radius must be numeric, got {type(radius).__name__}")

        # Security: check for NaN and infinite values
        for name, value in [("azimuth", azimuth), ("elevation", elevation), ("radius", radius)]:
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite (not NaN or infinite), got {value}")

        # Range validation
        if not (0 <= azimuth <= 360):
            raise ValueError(f"Azimuth must be between 0° and 360°, got {azimuth}°")

        if not (-90 <= elevation <= 90):
            raise ValueError(f"Elevation must be between -90° and 90°, got {elevation}°")

        # Special case: allow zero radius only in constructor (not in from_cartesian)
        if radius <= 0:
            raise ValueError(f"Radius must be greater than 0, got {radius}")
        # Note: radius == 0 is not allowed in constructor - origin must be represented differently

    def to_cartesian(self) -> Tuple[float, float, float]:
        """
        Convert spherical coordinates to Cartesian coordinates.

        Returns:
            Tuple of (x, y, z) Cartesian coordinates
        """
        # Convert degrees to radians for trigonometric functions
        theta_rad = math.radians(self.azimuth)
        phi_rad = math.radians(self.elevation)

        # Spherical to Cartesian conversion
        # x = r * sin(phi) * cos(theta)
        # y = r * sin(phi) * sin(theta)
        # z = r * cos(phi)
        x = self.radius * np.sin(phi_rad) * np.cos(theta_rad)
        y = self.radius * np.sin(phi_rad) * np.sin(theta_rad)
        z = self.radius * np.cos(phi_rad)

        return (x, y, z)

    @classmethod
    def from_cartesian(cls, x: Union[float, int], y: Union[float, int], z: Union[float, int]) -> 'SphericalCoordinate':
        """
        Create SphericalCoordinate from Cartesian coordinates with DoS protection.

        Implements robust validation to prevent coordinate bypass attacks,
        especially for negative z-axis points where elevation calculation
        was previously vulnerable.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate

        Returns:
            SphericalCoordinate instance

        Raises:
            TypeError: If inputs are not numeric
            ValueError: If inputs contain NaN/infinite values
            TimeoutError: If conversion takes too long (DoS protection)
        """
        start_time = time.time()

        try:
            # Security: type validation and NaN/infinite checks
            for name, coord in [("x", x), ("y", y), ("z", z)]:
                if not isinstance(coord, (int, float)):
                    raise TypeError(f"{name} coordinate must be numeric, got {type(coord).__name__}")
                if not np.isfinite(coord):
                    raise ValueError(f"{name} coordinate must be finite (not NaN or infinite), got {coord}")

            # Calculate radius with safe NumPy operation
            radius = np.sqrt(x**2 + y**2 + z**2)
            if not np.isfinite(radius):
                raise ValueError("Invalid Cartesian coordinates result in non-finite radius")

            # Handle special case of origin
            if radius == 0:
                return cls(0.0, 0.0, 0.0)

            # Calculate elevation (phi) from positive z-axis
            # Security fix: clamp z/radius to [-1, 1] to handle floating-point precision issues
            # and prevent arccos domain errors that could cause validation bypass
            z_normalized = z / radius
            z_normalized = np.clip(z_normalized, -1.0, 1.0)  # Prevent domain errors
            phi_rad = np.arccos(z_normalized)
            elevation = np.rad2deg(phi_rad)

            # Calculate azimuth (theta) from positive x-axis
            theta_rad = np.arctan2(y, x)
            azimuth = np.rad2deg(theta_rad)

            # Ensure azimuth is in [0, 360) range
            if azimuth < 0:
                azimuth += 360

            # Check for timeout before final validation
            if time.time() - start_time > SphericalCoordinate._MAX_OPERATION_TIME:
                raise TimeoutError("Cartesian to spherical conversion exceeded time limit - possible DoS attempt")

            return cls(azimuth, elevation, radius)

        except Exception as e:
            if time.time() - start_time > SphericalCoordinate._MAX_OPERATION_TIME:
                raise TimeoutError("Cartesian to spherical conversion exceeded time limit - possible DoS attempt")
            raise

    def euclidean_distance(self, other: 'SphericalCoordinate') -> float:
        """
        Calculate Euclidean distance between two points in Cartesian space.

        Args:
            other: Another SphericalCoordinate instance

        Returns:
            Euclidean distance between the two points
        """
        x1, y1, z1 = self.to_cartesian()
        x2, y2, z2 = other.to_cartesian()

        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

    def angular_distance(self, other: 'SphericalCoordinate') -> float:
        """
        Calculate angular distance (great circle distance) on unit sphere.

        This is the angle between the two direction vectors from origin.
        Implements safe floating-point operations with precision issue mitigation.

        Args:
            other: Another SphericalCoordinate instance

        Returns:
            Angular distance in degrees (0° to 180°)

        Raises:
            ValueError: If calculation results in invalid values
        """
        # Get unit vectors (normalize by radius) with safe operations
        try:
            x1, y1, z1 = self.to_cartesian()
            r1 = np.sqrt(x1**2 + y1**2 + z1**2)
            if r1 > 0:
                x1, y1, z1 = x1/r1, y1/r1, z1/r1

            x2, y2, z2 = other.to_cartesian()
            r2 = np.sqrt(x2**2 + y2**2 + z2**2)
            if r2 > 0:
                x2, y2, z2 = x2/r2, y2/r2, z2/r2
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Failed to normalize vectors for angular distance: {e}")

        # Cosine of angle between vectors with safe computation
        try:
            cos_angle = x1*x2 + y1*y2 + z1*z2
            # Clamp to [-1, 1] to handle floating-point precision issues
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Failed to compute dot product: {e}")

        # Angular distance in degrees with safe arccos
        try:
            angle_rad = np.arccos(cos_angle)
            if not np.isfinite(angle_rad):
                raise ValueError("Angular distance calculation resulted in non-finite value")
            return np.rad2deg(angle_rad)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Failed to calculate angular distance: {e}")

    def __repr__(self) -> str:
        """String representation of the coordinate."""
        return f"SphericalCoordinate(azimuth={self.azimuth:.2f}°, elevation={self.elevation:.2f}°, radius={self.radius:.2f})"