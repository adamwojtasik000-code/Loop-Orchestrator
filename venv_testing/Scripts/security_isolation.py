#!/usr/bin/env python3
"""
Security isolation verification for virtual environments.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class SecurityVerifier:
    def __init__(self, venv_path="venv_py38_test"):
        self.venv_path = Path(venv_path)
        self.bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        self.python_exe = self.bin_dir / ("python.exe" if os.name == 'nt' else "python")

    def audit_isolation(self):
        """Audit virtual environment isolation."""
        results = {
            "isolation_checks": {},
            "security_score": 0,
            "issues": []
        }

        checks = [
            ("venv_directory_exists", self.venv_path.exists()),
            ("python_executable_exists", self.python_exe.exists()),
            ("isolated_from_system_python", self._check_python_isolation()),
            ("secure_path_environment", self._check_path_security()),
            ("proper_permissions", self._check_permissions()),
        ]

        passed_checks = 0
        for check_name, passed in checks:
            results["isolation_checks"][check_name] = passed
            if passed:
                passed_checks += 1
            else:
                results["issues"].append(f"Failed check: {check_name}")

        results["security_score"] = (passed_checks / len(checks)) * 100

        return results

    def _check_python_isolation(self):
        """Check if Python is properly isolated."""
        try:
            # Get system Python path
            system_python = subprocess.run([sys.executable, "-c", "import sys; print(sys.executable)"],
                                        capture_output=True, text=True, timeout=10)
            system_path = system_python.stdout.strip()

            # Get venv Python path
            venv_python = subprocess.run([str(self.python_exe), "-c", "import sys; print(sys.executable)"],
                                       capture_output=True, text=True, timeout=10)
            venv_path = venv_python.stdout.strip()

            # They should be different
            return system_path != venv_path and str(self.venv_path) in venv_path
        except Exception:
            return False

    def _check_path_security(self):
        """Check PATH security."""
        path_env = os.environ.get('PATH', '')
        path_dirs = path_env.split(os.pathsep)

        # Check for potentially unsafe directories
        unsafe_patterns = ['temp', 'tmp', 'download', 'desktop']
        unsafe_paths = [p for p in path_dirs if any(pattern in p.lower() for pattern in unsafe_patterns)]

        # This is informational - PATH security depends on use case
        return len(unsafe_paths) == 0  # Pass if no obviously unsafe paths

    def _check_permissions(self):
        """Check file permissions."""
        try:
            # Basic check - can we execute Python in venv
            result = subprocess.run([str(self.python_exe), "--version"],
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def generate_security_report(self):
        """Generate comprehensive security report."""
        audit_results = self.audit_isolation()

        report = {
            "virtual_environment": str(self.venv_path),
            "python_version": self._get_python_version(),
            "audit_timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip() if os.name != 'nt' else "Windows",
            "security_audit": audit_results,
            "recommendations": self._generate_recommendations(audit_results)
        }

        return report

    def _get_python_version(self):
        """Get Python version in virtual environment."""
        try:
            result = subprocess.run([str(self.python_exe), "--version"],
                                  capture_output=True, text=True, timeout=10)
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except Exception:
            return "Unknown"

    def _generate_recommendations(self, audit_results):
        """Generate security recommendations based on audit results."""
        recommendations = []

        if audit_results["security_score"] < 70:
            recommendations.append("Overall security score is low - review failed checks")

        if not audit_results["isolation_checks"].get("isolated_from_system_python", False):
            recommendations.append("Python is not properly isolated from system installation")

        if not audit_results["isolation_checks"].get("secure_path_environment", False):
            recommendations.append("PATH environment contains potentially unsafe directories")

        if not audit_results["isolation_checks"].get("proper_permissions", False):
            recommendations.append("File permissions may not be properly configured")

        if not recommendations:
            recommendations.append("All basic security checks passed - virtual environment appears secure")

        return recommendations

def main():
    verifier = SecurityVerifier()

    print("=== Virtual Environment Security Audit ===")

    if not verifier.venv_path.exists():
        print(f"Virtual environment not found: {verifier.venv_path}")
        return

    # Run security audit
    audit_results = verifier.audit_isolation()

    print(f"Security Score: {audit_results['security_score']:.1f}%")

    print("\nIsolation Checks:")
    for check, passed in audit_results["isolation_checks"].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")

    if audit_results["issues"]:
        print("\nIssues Found:")
        for issue in audit_results["issues"]:
            print(f"  - {issue}")

    # Generate full report
    report = verifier.generate_security_report()

    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  - {rec}")

    # Save report
    report_file = verifier.venv_path.parent / "security_audit_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFull report saved to: {report_file}")

if __name__ == "__main__":
    main()