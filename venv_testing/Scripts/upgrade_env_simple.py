#!/usr/bin/env python3
"""
Simple upgrade environment script for Python virtual environment testing.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class VenvManager:
    def __init__(self, venv_name="venv_py38_test"):
        self.venv_name = venv_name
        self.venv_path = Path(venv_name)

    def create_venv(self) -> bool:
        if self.venv_path.exists():
            shutil.rmtree(self.venv_path)

        python_exe = sys.executable
        cmd = [python_exe, "-m", "venv", str(self.venv_path)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"Failed to create venv: {result.stderr}")
            return False

        print(f"Created virtual environment: {self.venv_path}")
        return True

    def test_venv(self) -> bool:
        bin_dir = self.venv_path / ("Scripts" if os.name == 'nt' else "bin")
        python_exe = bin_dir / ("python.exe" if os.name == 'nt' else "python")

        if not python_exe.exists():
            print("Python executable not found")
            return False

        result = subprocess.run([str(python_exe), "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Venv Python: {result.stdout.strip()}")
            return True
        return False

def main():
    manager = VenvManager()
    print("Creating Python virtual environment...")

    if manager.create_venv() and manager.test_venv():
        print("SUCCESS: Virtual environment created and tested")
    else:
        print("FAILED: Virtual environment setup failed")

if __name__ == "__main__":
    main()