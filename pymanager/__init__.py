import sys
import os
import builtins
import inspect
import importlib.util
import importlib.machinery
from .resolver import resolve_tree
from .store import absorb_packages, STORE_DIR, load_db

original_import = builtins.__import__

FILE_PROFILES = {}
LOADED_MODULES_CACHE = {} # Keyed by (package_name, version, module_name)

def require(**kwargs):
    """
    Called from inside a program to specify requirements for that file.
    If no kwargs are provided, it looks for requirements.txt in the same directory.
    e.g. pymanager.require(requests=">=2.20", numpy="")
    """
    caller_frame = inspect.stack()[1]
    caller_file = os.path.abspath(caller_frame.filename)
    caller_dir = os.path.dirname(caller_file)
    
    if not kwargs:
        req_path = os.path.join(caller_dir, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Very simple parsing
                        import re
                        parts = re.split(r'([=><~]+)', line, 1)
                        if len(parts) == 3:
                            kwargs[parts[0].strip()] = parts[1] + parts[2].strip()
                        else:
                            kwargs[parts[0].strip()] = ""
                            
    # Resolve the full dependency tree for this file
    resolved_profile = resolve_tree(kwargs)
    FILE_PROFILES[caller_file] = resolved_profile
    print(f"[PyManager] Profile set for {caller_file}: {resolved_profile}")

def get_caller_file():
    for frame_info in inspect.stack()[1:]:
        # Skip internal pymanager or importlib frames
        if 'importlib' not in frame_info.filename and 'pymanager' not in frame_info.filename:
            return os.path.abspath(frame_info.filename)
    return None

class PyManagerFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        base_module = fullname.split('.')[0]
        
        # Do not intercept built-ins or pymanager itself
        if base_module == 'pymanager' or base_module in sys.builtin_module_names:
            return None
            
        # Do not intercept standard library modules (Python 3.10+)
        if hasattr(sys, 'stdlib_module_names') and base_module in sys.stdlib_module_names:
            return None
            
        caller_file = get_caller_file()
        db = load_db()
        target_pkg = None
        target_version = None

        if caller_file and caller_file in FILE_PROFILES and FILE_PROFILES[caller_file]:
            profile = FILE_PROFILES[caller_file]
            for pkg_name, version in profile.items():
                if pkg_name in db and version in db[pkg_name]:
                    if base_module in db[pkg_name][version].get('modules', []):
                        target_pkg = pkg_name
                        target_version = version
                        break
        
        if not target_pkg:
            for pkg_name, versions in db.items():
                try:
                    from packaging.version import parse as parse_version
                    latest_version = max(versions.keys(), key=parse_version)
                except Exception:
                    latest_version = max(versions.keys())
                    
                if base_module in versions[latest_version].get('modules', []):
                    target_pkg = pkg_name
                    target_version = latest_version
                    break
                    
        if target_pkg and target_version:
            store_path = os.path.join(STORE_DIR, target_pkg, target_version)
            # Use standard PathFinder but ONLY looking in our isolated store_path
            spec = importlib.machinery.PathFinder.find_spec(fullname, [store_path])
            if spec:
                # Inherit profile for sub-imports
                mod_file = os.path.abspath(spec.origin) if spec.origin else None
                if mod_file and caller_file and caller_file in FILE_PROFILES:
                    FILE_PROFILES[mod_file] = FILE_PROFILES[caller_file]
                return spec
                
        return None

# Install the hook at the front of sys.meta_path
if not any(isinstance(finder, PyManagerFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, PyManagerFinder())

__all__ = ['require', 'absorb_packages']

