#!/usr/bin/env python3
import os
import sys

def mass_edit(target_dir):
    """
    Walks through the target directory and injects the PyManager initialization
    code at the top of every Python file.
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
        
        for file in files:
            if file.endswith(".py") and file != "mass_edit.py" and file != "manage.py":
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    # Skip if already injected
                    if "import pymanager" in content:
                        continue
                        
                    # Check for shebang
                    if content.startswith("#!"):
                        lines = content.split("\n", 1)
                        if len(lines) == 2:
                            new_content = lines[0] + "\n" + init_code + "\n" + lines[1]
                        else:
                            new_content = lines[0] + "\n" + init_code
                    else:
                        new_content = init_code + "\n" + content
                        
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                        
                    count += 1
                    print(f"Updated {filepath}")
                except Exception as e:
                    print(f"Failed to update {filepath}: {e}")
                    
    print(f"\nMass edit complete! Successfully injected PyManager into {count} Python files in {target_dir}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./mass_edit.py <path_to_project>")
        print("Example: ./mass_edit.py /home/sashna/Desktop/my_project")
        sys.exit(1)
        
    target = sys.argv[1]
    print(f"Starting mass edit on: {target}")
    mass_edit(target)
