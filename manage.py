#!/usr/bin/env python3
import sys
import os

# Add pyenv to path so we can import pymanager
sys.path.insert(0, os.path.expanduser("/home/sashna/pyenv"))

import pymanager

def install_package(package_name):
    import subprocess
    import tempfile
    import shutil
    
    print(f"Installing '{package_name}' directly into PyManager Central Store...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run pip install into the temporary directory
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name, "--target", tmpdir],
            capture_output=False
        )
        if result.returncode == 0:
            print(f"\nSuccessfully downloaded. Absorbing into Central Store...")
            pymanager.absorb_packages(tmpdir)
            print(f"\nDone! '{package_name}' is now managed by PyManager.")
        else:
            print(f"Failed to install '{package_name}'.")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ./manage.py absorb           - Scan system and absorb all local packages into central store")
        print("  ./manage.py install <pkg>    - Install a new package directly into the central store")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "absorb":
        home = os.path.expanduser("~")
        pymanager.absorb_packages(home)
        print("Absorption and deduplication complete.")
    elif command == "install":
        if len(sys.argv) < 3:
            print("Usage: ./manage.py install <package_name>")
            sys.exit(1)
        install_package(sys.argv[2])
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
