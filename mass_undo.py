#!/usr/bin/env python3
import os
import sys

def mass_undo(target_dir):
    """
    Walks through the target directory and REMOVES the PyManager initialization
    code from the top of every Python file.
    """
    init_code = (
        "import sys, os\n"
        "sys.path.insert(0, os.path.expanduser('~/pyenv'))\n"
        "import pymanager\n"
        "pymanager.require()\n"
    )

    count = 0
    ignore_dirs = {
        'venv', 'env', 'node_modules', '__pycache__', '.venv',
        'pyenv', 'Downloads', 'Documents', 'Pictures', 'Music', 
        'Videos', '.cache', '.config', '.local', '.npm', 'central_store'
    }
    
    for root, dirs, files in os.walk(target_dir):
        # Skip hidden directories and specific ignore_dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
        # Also let's scan hidden dirs since we might have injected there
        # Wait, the original script skipped hidden dirs: `if not d.startswith('.')`
        # But wait! If it skipped `d.startswith('.')`, why did it hit `.var` and `.antigravity`?
        # Ah! `d.startswith('.')` WAS in the original script!
        # If the original script skipped `.var` and `.antigravity`, why did `find` show them?
        # Because `find` doesn't skip them, but `mass_edit.py` DID skip them!
        pass

def mass_undo_correct(target_dir):
    init_code = (
        "import sys, os\n"
        "sys.path.insert(0, os.path.expanduser('~/pyenv'))\n"
        "import pymanager\n"
        "pymanager.require()\n"
    )
    
    # We must match the EXACT traversal of the original script to undo it.
    ignore_dirs = {
        'venv', 'env', 'node_modules', '__pycache__', '.venv',
        'pyenv', 'Downloads', 'Documents', 'Pictures', 'Music', 
        'Videos', '.cache', '.config', '.local', '.npm', 'central_store'
    }
    
    count = 0
    for root, dirs, files in os.walk(target_dir):
        # The original script did:
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
        
        for file in files:
            if file.endswith(".py") and file not in ["mass_edit.py", "manage.py", "mass_undo.py"]:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    if init_code in content:
                        new_content = content.replace(init_code + "\n", "").replace(init_code, "")
                        with open(filepath, 'w') as f:
                            f.write(new_content)
                        count += 1
                except Exception:
                    pass
                    
    print(f"Undo complete! Reverted {count} files.")

if __name__ == "__main__":
    target = os.path.expanduser("~")
    mass_undo_correct(target)
