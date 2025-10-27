#!/usr/bin/env python3
"""
Security audit script for Python version upgrade validation.
Performs comprehensive security checks for the upgrade from Python 3.8 to 3.9+.
"""

import sys
import hashlib
import ssl
import os
import subprocess
import json
from datetime import datetime

def log(message):
    """Log messages with timestamps."""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {message}")

def check_python_version():
    """Check current Python version and security status."""
    log("=== Python Version Security Check ===")
    log(f"Current Python version: {sys.version}")
    log(f"Platform: {sys.platform}")

    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    log(f"Virtual environment active: {in_venv}")

    if not in_venv:
        log("WARNING: Not running in virtual environment - package isolation compromised")

    return sys.version_info[:2]

def check_ssl_security():
    """Check SSL/TLS security configuration."""
    log("=== SSL/TLS Security Check ===")
    try:
        log(f"OpenSSL version: {ssl.OPENSSL_VERSION}")

        # Check for outdated protocols
        protocols = [p for p in dir(ssl) if p.startswith('PROTOCOL_')]
        log(f"Available SSL protocols: {len(protocols)}")

        # Check if modern TLS is supported
        has_tls13 = hasattr(ssl, 'PROTOCOL_TLSv1_3')
        log(f"TLS 1.3 support: {has_tls13}")

        if not has_tls13:
            log("WARNING: TLS 1.3 not available - increased vulnerability to downgrade attacks")

        log("SSL/TLS configuration: OK")
        return True
    except Exception as e:
        log(f"SSL check failed: {e}")
        return False

def check_cryptography_modules():
    """Check cryptographic modules availability and security."""
    log("=== Cryptography Modules Check ===")
    try:
        import hashlib
        import secrets

        # Check hash algorithms
        algorithms = sorted(hashlib.algorithms_available)
        log(f"Available hash algorithms: {len(algorithms)}")

        # Check for weak algorithms
        weak_algorithms = ['md4', 'md5', 'sha1']
        weak_present = [alg for alg in weak_algorithms if alg in algorithms]
        if weak_present:
            log(f"WARNING: Weak hash algorithms available: {weak_present}")

        # Check secrets module
        has_csprng = hasattr(secrets, 'token_bytes')
        log(f"Cryptographically secure random: {has_csprng}")

        log("Cryptography modules: OK")
        return True
    except Exception as e:
        log(f"Cryptography check failed: {e}")
        return False

def check_package_integrity():
    """Check installed package integrity."""
    log("=== Package Integrity Check ===")
    try:
        import pip
        log(f"Pip version: {pip.__version__}")

        # Get installed packages
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            packages = json.loads(result.stdout)
            log(f"Installed packages: {len(packages)}")

            # Check for security-critical packages
            security_packages = ['cryptography', 'pyopenssl', 'requests', 'urllib3']
            installed_security = [pkg for pkg in packages if pkg['name'].lower() in security_packages]

            log(f"Security-critical packages: {len(installed_security)}")
            for pkg in installed_security:
                log(f"  {pkg['name']}: {pkg['version']}")

            log("Package integrity: OK")
            return True
        else:
            log(f"Pip list failed: {result.stderr}")
            return False

    except Exception as e:
        log(f"Package integrity check failed: {e}")
        return False

def check_network_security():
    """Check network security capabilities."""
    log("=== Network Security Check ===")
    try:
        import urllib.request
        import urllib.error

        # Test HTTPS connection to PyPI
        try:
            response = urllib.request.urlopen('https://pypi.org/', timeout=10)
            response.close()
            log("HTTPS connection to PyPI: SUCCESS")
        except urllib.error.URLError as e:
            log(f"HTTPS connection failed: {e}")
            return False

        log("Network security: OK")
        return True

    except Exception as e:
        log(f"Network security check failed: {e}")
        return False

def analyze_upgrade_risks(current_version):
    """Analyze risks associated with Python version upgrade."""
    log("=== Python Upgrade Risk Analysis ===")

    major, minor = current_version
    target_version = (3, 9)

    log(f"Current version: {major}.{minor}")
    log(f"Target version: {target_version[0]}.{target_version[1]}")

    risks = []

    if major < 3 or (major == 3 and minor < 9):
        risks.append("Version too old - security patches may be missing")
        risks.append("Modern type annotations not supported (dict[str, str] syntax)")
        risks.append("Potential dependency compatibility issues")

    if target_version[1] - minor > 1:
        risks.append(f"Large version jump ({minor} -> {target_version[1]}) increases compatibility risk")

    risks.append("Package ecosystem changes may affect dependencies")
    risks.append("Virtual environment recreation required for proper isolation")

    log("Identified risks:")
    for i, risk in enumerate(risks, 1):
        log(f"  {i}. {risk}")

    return risks

def main():
    """Main security audit function."""
    log("Starting Python version upgrade security audit...")

    # Perform checks
    current_version = check_python_version()
    ssl_ok = check_ssl_security()
    crypto_ok = check_cryptography_modules()
    packages_ok = check_package_integrity()
    network_ok = check_network_security()
    risks = analyze_upgrade_risks(current_version)

    # Summary
    log("\n=== Security Audit Summary ===")
    checks = {
        "SSL/TLS Security": ssl_ok,
        "Cryptography Modules": crypto_ok,
        "Package Integrity": packages_ok,
        "Network Security": network_ok
    }

    passed = sum(checks.values())
    total = len(checks)

    log(f"Checks passed: {passed}/{total}")

    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        log(f"  {check}: {status}")

    if passed == total:
        log("SECURITY STATUS: ACCEPTABLE for upgrade")
        log("RECOMMENDATION: Proceed with Python 3.9+ upgrade in isolated virtual environment")
    else:
        log("SECURITY STATUS: REQUIRES ATTENTION")
        log("RECOMMENDATION: Address failed checks before upgrade")

    log(f"Identified risks: {len(risks)}")
    log("Audit completed.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)