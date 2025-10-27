#!/usr/bin/env python3
"""
Workaround script for MCP Python SDK installation with uv-dynamic-versioning issues.
This script manually clones, patches, and installs the MCP SDK to bypass build issues.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"In directory: {cwd}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result

def main():
    # Check Python version
    if sys.version_info < (3, 9):
        print("WARNING: Python version is below 3.9, but proceeding with installation...")

    # Create temporary directory for the clone
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "mcp-python-sdk"

        # Clone the repository
        print("Cloning MCP Python SDK repository...")
        run_command(["git", "clone", "https://github.com/modelcontextprotocol/python-sdk.git", str(repo_path)])

        # Change to the repository directory
        os.chdir(repo_path)

        # Examine the pyproject.toml to understand the build configuration
        pyproject_path = repo_path / "pyproject.toml"
        if pyproject_path.exists():
            print("Examining pyproject.toml...")
            with open(pyproject_path, 'r') as f:
                content = f.read()
                print("Build dependencies found in pyproject.toml:")
                for line in content.split('\n'):
                    if 'uv-dynamic-versioning' in line:
                        print(f"  {line.strip()}")

        # Create a patched version without uv-dynamic-versioning
        print("Creating patched pyproject.toml without uv-dynamic-versioning...")

        # Read the original content
        with open(pyproject_path, 'r') as f:
            content = f.read()

        # Remove uv-dynamic-versioning from build dependencies
        lines = content.split('\n')
        patched_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            if 'uv-dynamic-versioning' in line:
                # Remove this line and potentially the next few related lines
                print(f"Removing line: {line}")
                # Check if this is part of a list
                if i > 0 and ('[' in lines[i-1] or ',' in line):
                    # This is likely part of a list, skip it
                    continue
                if i < len(lines) - 1 and (']' in lines[i+1] or ',' in lines[i+1]):
                    # Next line closes the list, skip this one
                    continue
                continue
            patched_lines.append(line)

        # Write the patched content
        with open(pyproject_path, 'w') as f:
            f.write('\n'.join(patched_lines))

        print("Patched pyproject.toml created successfully.")

        # Now try to install using pip with --no-build-isolation to avoid the build dependency issue
        print("Installing MCP SDK with patched configuration...")
        run_command([sys.executable, "-m", "pip", "install", "-e", ".", "--no-build-isolation"])

        print("Installation completed successfully!")

        # Test the installation
        print("Testing MCP SDK installation...")
        test_code = """
try:
    import mcp
    print("✓ MCP SDK imported successfully")
    print(f"MCP version: {getattr(mcp, '__version__', 'unknown')}")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
"""
        run_command([sys.executable, "-c", test_code])

if __name__ == "__main__":
    main()