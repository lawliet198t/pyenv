#!/usr/bin/env python3
import sys
import os

# Add pyenv to path so we can import pymanager
sys.path.insert(0, os.path.expanduser("/home/sashna/pyenv"))

import pymanager

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "absorb":
        # Scan the user's home directory and absorb venvs into central store
        pymanager.absorb_packages(os.path.expanduser("~"))
    else:
        print("Usage: ./manage.py absorb")

if __name__ == "__main__":
    main()
