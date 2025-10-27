import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual environment active: {'VIRTUAL_ENV' in os.environ}")
if 'VIRTUAL_ENV' in os.environ:
    print(f"Virtual environment path: {os.environ['VIRTUAL_ENV']}")