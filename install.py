#!/usr/bin/env python3
import sys
import os
import site

def install_global_hook():
    """
    Installs the PyManager hook globally for the current user.
    Creates a .pth file in the user's site-packages directory.
    This works across all operating systems (Windows, macOS, Linux).
    """
    # Get the directory where pymanager actually lives (the directory of this script)
    pyenv_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if pymanager exists here
    if not os.path.exists(os.path.join(pyenv_dir, "pymanager", "__init__.py")):
        print(f"Error: Could not find 'pymanager' package in {pyenv_dir}")
        print("Please run this script from the directory containing pymanager.")
        sys.exit(1)

    # Get the user's global site-packages directory
    user_site = site.getusersitepackages()
    
    # Ensure the user site-packages directory exists
    if not os.path.exists(user_site):
        try:
            os.makedirs(user_site)
        except Exception as e:
            print(f"Failed to create user site-packages directory {user_site}: {e}")
            sys.exit(1)
            
    pth_file = os.path.join(user_site, "pymanager_auto.pth")
    
    # The code that will run every time Python starts
    # Note: On Windows paths contain backslashes, so we use repr() to escape them safely
    pth_content = (
        f"import sys, os; "
        f"sys.path.insert(0, {repr(pyenv_dir)}); "
        f"import pymanager; "
        f"pymanager.require()\n"
    )
    
    try:
        with open(pth_file, 'w') as f:
            f.write(pth_content)
        print("================================================================")
        print(" SUCCESS! PyManager is now globally installed on your machine!")
        print("================================================================")
        print(f"\nA system hook has been created at:\n  {pth_file}\n")
        print("From now on, ANY Python script you run will automatically:")
        print("  1. Parse its local requirements.txt (if it exists)")
        print("  2. Instantly load the exact library versions from the Central Store")
        print("  3. Fallback to the newest stored versions if no requirements are found\n")
        print("You NEVER need to activate a virtual environment again!")
    except Exception as e:
        print(f"Failed to install global hook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Welcome to the PyManager Universal Installer")
    print("This will configure your Python environment to automatically use the Central Store.")
    
    install_global_hook()
