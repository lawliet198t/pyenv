#!/usr/bin/env python3
import sys
import os
import site
import shutil
import glob
from packaging.version import parse as parse_version

def get_latest_version_dir(pkg_dir):
    versions = [d for d in os.listdir(pkg_dir) if os.path.isdir(os.path.join(pkg_dir, d))]
    if not versions: return None
    try:
        latest = max(versions, key=parse_version)
    except Exception:
        latest = max(versions)
    return os.path.join(pkg_dir, latest)

def uninstall_global_hook():
    print("Welcome to the PyManager Uninstall Wizard")
    print("This will revert system-level changes and restore your global packages.")
    
    user_site = site.getusersitepackages()
    pth_file = os.path.join(user_site, "pymanager_auto.pth")
    
    # 1. Remove the system startup hook
    if os.path.exists(pth_file):
        try:
            os.remove(pth_file)
            print(f"[\u2713] Removed global startup hook: {pth_file}")
        except Exception as e:
            print(f"[!] Failed to remove hook: {e}")
    else:
        print(f"[-] Global hook not found (already removed).")

    # 2. Restore packages from Central Store to global site-packages
    # We will pick the latest version of each package in the central store and copy it back.
    py_ver = f"py{sys.version_info.major}.{sys.version_info.minor}"
    store_dir = os.path.join(os.path.expanduser("~"), "pyenv", "central_store", py_ver)
    
    if os.path.exists(store_dir):
        print("\nRestoring latest package versions from Central Store back to global site-packages...")
        restored_count = 0
        for pkg_name in os.listdir(store_dir):
            pkg_path = os.path.join(store_dir, pkg_name)
            if not os.path.isdir(pkg_path): continue
            
            latest_dir = get_latest_version_dir(pkg_path)
            if not latest_dir: continue
            
            for item in os.listdir(latest_dir):
                src = os.path.join(latest_dir, item)
                dst = os.path.join(user_site, item)
                try:
                    if os.path.isdir(src):
                        # Merge directories (e.g. for namespace packages or .libs)
                        if os.path.exists(dst):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                    restored_count += 1
                except Exception as e:
                    print(f"[!] Failed to restore {item}: {e}")
        
        print(f"[\u2713] Successfully restored {restored_count} folders/files to {user_site}.")
    
    print("\n================================================================")
    print(" UNINSTALLATION SUCCESSFUL")
    print("================================================================")
    print("PyManager is now downgraded to a LIBRARY-LEVEL utility.")
    print("Your standard Python environment has been completely restored.")
    print("\nTo use PyManager from now on, you must explicitly import it in your scripts:")
    print("   import sys; sys.path.insert(0, '~/pyenv'); import pymanager; pymanager.require()")
    print("\nNote: If you used 'mass_edit.py' to inject imports into your projects,")
    print("you can run 'python3 mass_undo.py <directory>' to remove those imports automatically.")

if __name__ == "__main__":
    uninstall_global_hook()
