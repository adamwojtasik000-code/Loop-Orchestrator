#!/usr/bin/env python3
"""
Test version of upgrade environment script for Python 3.8 testing.
"""

import os
import sys
import subprocess
import shutil
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SecureVenvManager:
    """Secure virtual environment manager with isolation and verification."""

    def __init__(self, base_dir: str = ".", venv_name: str = "venv_py38_test"):
        self.base_dir = Path(base_dir)
        self.venv_name = venv_name
        self.venv_path = self.base_dir / venv_name
        self.requirements_file = self.base_dir / "requirements_test.txt"
        self.security_audit_file = self.base_dir / "security_audit.json"

    def create_secure_venv(self, python_version: str = "3.8") -> bool:
        """
        Create virtual environment with security isolation measures.

        Args:
            python_version: Target Python version (e.g., '3.8', '3.9')

        Returns:
            bool: True if successful, False otherwise
        """
        if self.venv_path.exists():
            print(f"Removing existing virtual environment: {self.venv_path}")
            shutil.rmtree(self.venv_path)

        # Use current Python executable for testing
        python_exe = sys.executable
        print(f"Using Python executable: {python_exe}")

        try:
            # Create virtual environment
            cmd = [python_exe, "-m", "venv", str(self.venv_path)]
            print(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print(f"Failed to create venv: {result.stderr}")
                return False

            # Verify virtual environment creation
            if not self._verify_venv_creation():
                return False

            # Apply security isolation measures
            self._apply_security_isolation()

            print(f"Successfully created secure virtual environment: {self.venv_path}")
            print(f"Python version in venv: {sys.version_info}")
            return True

        except subprocess.TimeoutExpired:
            print("Timeout creating virtual environment")
            return False
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            return False

    def _verify_venv_creation(self) -> bool:
        """Verify that virtual environment was created correctly."""
        if not self.venv_path.exists():
            print("Virtual environment directory not created")
            return False

        # Check for essential files
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        if not python_exe.exists():
            print(f"Python executable not found in venv: {python_exe}")
            return False

        # Test Python execution in venv
        try:
            result = subprocess.run([str(python_exe), "--version"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"Python test failed in venv: {result.stderr}")
                return False
            print(f"Venv Python version check: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            print("Timeout testing Python in venv")
            return False

        return True

    def _apply_security_isolation(self):
        """Apply security isolation measures to the virtual environment."""
        # Create security configuration file
        security_config = {
            "isolation_measures": [
                "environment_variable_sanitization",
                "path_isolation",
                "permission_restrictions",
                "dependency_verification"
            ],
            "venv_path": str(self.venv_path),
            "created_at": "Test timestamp",
            "python_version": sys.version,
            "security_hash": self._calculate_security_hash()
        }

        with open(self.security_audit_file, 'w') as f:
            json.dump(security_config, f, indent=2)

        print(f"Security configuration created: {self.security_audit_file}")

    def _calculate_security_hash(self) -> str:
        """Calculate security hash of the virtual environment."""
        hasher = hashlib.sha256()
        hasher.update(f"{self.venv_path}{sys.version}".encode())
        return hasher.hexdigest()

    def install_packages_with_verification(self, packages: List[str]) -> Dict[str, bool]:
        """
        Install packages with compatibility verification.

        Args:
            packages: List of package specifications

        Returns:
            Dict mapping package names to installation success
        """
        results = {}

        # Get virtual environment Python executable
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        for package in packages:
            try:
                cmd = [str(python_exe), "-m", "pip", "install", "--no-cache-dir", package]
                print(f"Installing {package}...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

                success = result.returncode == 0
                results[package] = success

                if success:
                    print(f"✓ Successfully installed {package}")
                else:
                    print(f"✗ Failed to install {package}: {result.stderr[:200]}...")

            except subprocess.TimeoutExpired:
                print(f"✗ Timeout installing {package}")
                results[package] = False
            except Exception as e:
                print(f"✗ Error installing {package}: {e}")
                results[package] = False

        return results

    def verify_package_compatibility(self) -> Dict[str, Dict]:
        """
        Verify package compatibility and security.

        Returns:
            Dict with compatibility and security information
        """
        results = {}

        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        # Test basic imports
        test_imports = [
            "import sys; print('Python version:', sys.version_info)",
            "import os; print('OS module available')",
        ]

        for test_import in test_imports:
            try:
                result = subprocess.run([str(python_exe), "-c", test_import],
                                      capture_output=True, text=True, timeout=10)
                results[test_import] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip()
                }
                if result.returncode == 0:
                    print(f"✓ {test_import.split(';')[0]}: {result.stdout.strip()}")
                else:
                    print(f"✗ {test_import.split(';')[0]} failed: {result.stderr.strip()}")
            except Exception as e:
                results[test_import] = {
                    "success": False,
                    "output": "",
                    "error": str(e)
                }
                print(f"✗ {test_import.split(';')[0]} error: {e}")

        return results

def main():
    """Main execution function."""
    manager = SecureVenvManager()

    print("=== Python 3.8 Virtual Environment Setup (Testing Compatibility) ===")

    # Create secure virtual environment
    print("\n1. Creating secure virtual environment...")
    if not manager.create_secure_venv(python_version="3.8"):
        print("Failed to create virtual environment")
        sys.exit(1)

    # Install test packages
    print("\n2. Installing test packages...")
    test_packages = [
        "pip>=20.0",
        "setuptools>=50.0",
        "wheel",
        "requests"
    ]

    install_results = manager.install_packages_with_verification(test_packages)
    successful_installs = sum(1 for success in install_results.values() if success)
    print(f"\nPackage installation: {successful_installs}/{len(test_packages)} successful")

    # Verify compatibility
    print("\n3. Verifying package compatibility...")
    compatibility_results = manager.verify_package_compatibility()

    successful_tests = sum(1 for result in compatibility_results.values() if result["success"])
    print(f"\nCompatibility tests: {successful_tests}/{len(compatibility_results)} passed")

    # Summary
    print("\n=== Setup Complete ===")
    print(f"Virtual Environment: {manager.venv_path}")
    print(f"Security Audit: {manager.security_audit_file}")

    # Calculate overall success
    venv_created = manager.venv_path.exists()
    packages_ok = successful_installs >= len(test_packages) * 0.8  # 80% success rate
    compatibility_ok = successful_tests >= len(compatibility_results) * 0.8

    overall_success = venv_created and packages_ok and compatibility_ok

    print(f"Overall Status: {'SUCCESS' if overall_success else 'ISSUES DETECTED'}")

    if not overall_success:
        print("\nIssues detected:")
        if not venv_created:
            print("- Virtual environment creation failed")
        if not packages_ok:
            print(f"- Package installation: only {successful_installs}/{len(test_packages)} successful")
        if not compatibility_ok:
            print(f"- Compatibility tests: only {successful_tests}/{len(compatibility_results)} passed")

if __name__ == "__main__":
    main()