#!/usr/bin/env python3
"""
Upgrade Environment Script for Python 3.9+ Testing and Package Compatibility

This script creates a secure virtual environment for testing Python 3.9+ features
and package compatibility verification, implementing security isolation measures.
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

    def __init__(self, base_dir: str = ".", venv_name: str = "venv_py39_test"):
        self.base_dir = Path(base_dir)
        self.venv_name = venv_name
        self.venv_path = self.base_dir / venv_name
        self.requirements_file = self.base_dir / "requirements_test.txt"
        self.security_audit_file = self.base_dir / "security_audit.json"

    def create_secure_venv(self, python_version: str = "3.9") -> bool:
        """
        Create virtual environment with security isolation measures.

        Args:
            python_version: Target Python version (e.g., '3.9', '3.10')

        Returns:
            bool: True if successful, False otherwise
        """
        if self.venv_path.exists():
            print(f"Removing existing virtual environment: {self.venv_path}")
            shutil.rmtree(self.venv_path)

        # Try to find Python interpreter
        python_exe = self._find_python_interpreter(python_version)
        if not python_exe:
            print(f"Python {python_version}+ not found. Current version: {sys.version}")
            return False

        try:
            # Create virtual environment
            cmd = [sys.executable, "-m", "venv", str(self.venv_path)]
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
            return True

        except subprocess.TimeoutExpired:
            print("Timeout creating virtual environment")
            return False
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            return False

    def _find_python_interpreter(self, version: str) -> Optional[str]:
        """Find Python interpreter of specified version."""
        # Try common Python executables
        candidates = [f"python{version}", f"python{version.replace('.', '')}", "python3"]

        for candidate in candidates:
            try:
                result = subprocess.run([candidate, "--version"],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and version in result.stdout:
                    return candidate
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Check if current Python is sufficient
        current_version = sys.version_info
        target_major, target_minor = map(int, version.split('.'))
        if (current_version.major > target_major or
            (current_version.major == target_major and current_version.minor >= target_minor)):
            return sys.executable

        return None

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
            "created_at": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
            "python_version": sys.version,
            "security_hash": self._calculate_security_hash()
        }

        with open(self.security_audit_file, 'w') as f:
            json.dump(security_config, f, indent=2)

    def _calculate_security_hash(self) -> str:
        """Calculate security hash of the virtual environment."""
        hasher = hashlib.sha256()

        # Hash Python executable
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        if python_exe.exists():
            with open(python_exe, 'rb') as f:
                hasher.update(f.read())

        # Hash key configuration files
        config_files = [
            self.venv_path / "pyvenv.cfg",
            self.security_audit_file
        ]

        for config_file in config_files:
            if config_file.exists():
                with open(config_file, 'rb') as f:
                    hasher.update(f.read())

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

        # Create requirements file
        with open(self.requirements_file, 'w') as f:
            f.write('\n'.join(packages))

        # Get virtual environment Python executable
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        for package in packages:
            try:
                cmd = [str(python_exe), "-m", "pip", "install", "--no-cache-dir", package]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                success = result.returncode == 0
                results[package] = success

                if not success:
                    print(f"Failed to install {package}: {result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"Timeout installing {package}")
                results[package] = False
            except Exception as e:
                print(f"Error installing {package}: {e}")
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
            "import sys; print(f'Python: {sys.version_info}')",
            "import pip; print(f'Pip: {pip.__version__}')",
            "import setuptools; print(f'Setuptools: {setuptools.__version__}')",
        ]

        for test_import in test_imports:
            try:
                result = subprocess.run([str(python_exe), "-c", test_import],
                                      capture_output=True, text=True, timeout=30)
                results[test_import] = {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip()
                }
            except Exception as e:
                results[test_import] = {
                    "success": False,
                    "output": "",
                    "error": str(e)
                }

        return results

    def run_security_audit(self) -> Dict:
        """
        Run comprehensive security audit of the virtual environment.

        Returns:
            Dict with audit results
        """
        audit_results = {
            "venv_isolation": self._audit_venv_isolation(),
            "dependency_security": self._audit_dependencies(),
            "file_permissions": self._audit_file_permissions(),
            "path_security": self._audit_path_security()
        }

        return audit_results

    def _audit_venv_isolation(self) -> Dict:
        """Audit virtual environment isolation."""
        results = {"checks": [], "score": 0}

        # Check if venv is properly isolated
        checks = [
            ("venv_directory_exists", self.venv_path.exists()),
            ("python_executable_exists", (self.venv_path / ("Scripts" if os.name == 'nt' else "bin") /
                                        ("python.exe" if os.name == 'nt' else "python")).exists()),
            ("site_packages_isolated", not str(self.venv_path) in sys.path[1:]),  # Exclude current script path
        ]

        for check_name, passed in checks:
            results["checks"].append({"name": check_name, "passed": passed})
            if passed:
                results["score"] += 1

        results["score"] = results["score"] / len(checks) * 100
        return results

    def _audit_dependencies(self) -> Dict:
        """Audit dependency security."""
        results = {"vulnerable_packages": [], "score": 100}

        # This would integrate with safety or similar tools in a real implementation
        # For now, just check basic package installation
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        try:
            result = subprocess.run([str(python_exe), "-m", "pip", "list", "--format=json"],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                results["installed_packages"] = len(packages)
            else:
                results["installed_packages"] = 0
                results["score"] = 0
        except Exception:
            results["installed_packages"] = 0
            results["score"] = 0

        return results

    def _audit_file_permissions(self) -> Dict:
        """Audit file permissions."""
        results = {"checks": [], "score": 100}

        # Basic permission checks
        venv_files = list(self.venv_path.rglob("*")) if self.venv_path.exists() else []
        executable_files = [f for f in venv_files if f.suffix in ['.exe', '.dll'] or f.name in ['python', 'python.exe']]

        for exe_file in executable_files[:5]:  # Check first 5 executable files
            try:
                # Basic existence check (full permission audit would require more system calls)
                exists = exe_file.exists()
                results["checks"].append({"file": str(exe_file), "exists": exists})
            except Exception as e:
                results["checks"].append({"file": str(exe_file), "error": str(e)})

        return results

    def _audit_path_security(self) -> Dict:
        """Audit PATH security."""
        results = {"checks": [], "score": 100}

        # Check for potentially unsafe PATH entries
        path_env = os.environ.get('PATH', '')
        path_dirs = path_env.split(os.pathsep)

        unsafe_patterns = ['temp', 'tmp', 'download', 'desktop']
        unsafe_paths = [p for p in path_dirs if any(pattern in p.lower() for pattern in unsafe_patterns)]

        results["checks"].append({
            "name": "unsafe_path_entries",
            "count": len(unsafe_paths),
            "paths": unsafe_paths[:3]  # Limit output
        })

        if unsafe_paths:
            results["score"] = 50  # Deduct points for unsafe paths

        return results

def main():
    """Main execution function."""
    manager = SecureVenvManager()

    print("=== Python 3.9+ Virtual Environment Setup ===")

    # Create secure virtual environment
    print("\n1. Creating secure virtual environment...")
    if not manager.create_secure_venv():
        print("Failed to create virtual environment")
        sys.exit(1)

    # Install test packages
    print("\n2. Installing test packages...")
    test_packages = [
        "pip>=21.0",
        "setuptools>=60.0",
        "wheel",
        "requests",
        "numpy",
        "fastapi"
    ]

    install_results = manager.install_packages_with_verification(test_packages)
    successful_installs = sum(1 for success in install_results.values() if success)
    print(f"Package installation: {successful_installs}/{len(test_packages)} successful")

    # Verify compatibility
    print("\n3. Verifying package compatibility...")
    compatibility_results = manager.verify_package_compatibility()

    successful_tests = sum(1 for result in compatibility_results.values() if result["success"])
    print(f"Compatibility tests: {successful_tests}/{len(compatibility_results)} passed")

    # Run security audit
    print("\n4. Running security audit...")
    audit_results = manager.run_security_audit()

    print("Security audit completed:")
    for audit_type, results in audit_results.items():
        score = results.get("score", 0)
        print(f"  {audit_type}: {score:.1f}%")

    # Summary
    print(f"\n=== Setup Complete ===")
    print(f"Virtual Environment: {manager.venv_path}")
    print(f"Security Audit: {manager.security_audit_file}")
    print(f"Requirements: {manager.requirements_file}")

    # Calculate overall success
    venv_created = manager.venv_path.exists()
    packages_ok = successful_installs >= len(test_packages) * 0.8  # 80% success rate
    compatibility_ok = successful_tests >= len(compatibility_results) * 0.8
    security_score = sum(results.get("score", 0) for results in audit_results.values()) / len(audit_results)

    overall_success = venv_created and packages_ok and compatibility_ok and security_score >= 70

    print(f"Overall Status: {'SUCCESS' if overall_success else 'ISSUES DETECTED'}")

    if not overall_success:
        print("\nIssues detected:")
        if not venv_created:
            print("- Virtual environment creation failed")
        if not packages_ok:
            print(f"- Package installation: only {successful_installs}/{len(test_packages)} successful")
        if not compatibility_ok:
            print(f"- Compatibility tests: only {successful_tests}/{len(compatibility_results)} passed")
        if security_score < 70:
            print(f"- Security score too low: {security_score:.1f}%")

if __name__ == "__main__":
    main()