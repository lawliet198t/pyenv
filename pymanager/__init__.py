import sys
import os
import builtins
import inspect
import importlib.util
import importlib.machinery
from .resolver import resolve_tree
from .store import absorb_packages, STORE_DIR, load_db

def _auto_absorb():
    """Fast check on startup to absorb any newly pip-installed packages automatically."""
    import site
    # Prevent infinite loops or breaking pip itself while it's installing
    if sys.argv and ('pip' in sys.argv[0] or 'manage.py' in sys.argv[0] or 'mass_edit.py' in sys.argv[0]):
        return
        
    user_site = site.getusersitepackages()
    if not os.path.exists(user_site):
        return
        
    # Check if any new packages were installed by looking for .dist-info
    try:
        has_new_packages = any(item.endswith('.dist-info') for item in os.listdir(user_site))
        if has_new_packages:
            print("[PyManager] Newly installed global packages detected! Auto-absorbing into central store...")
            absorb_packages(os.path.expanduser("~"))
    except Exception:
        pass

# Run auto-absorb instantly when pymanager is loaded
_auto_absorb()

original_import = builtins.__import__

FILE_PROFILES = {}

def require(**kwargs):
    """
    Called from inside a program to specify requirements for that file.
    If no kwargs are provided, it looks for requirements.txt in the same directory.
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
                        import re
                        parts = re.split(r'([=><~]+)', line, 1)
                        if len(parts) == 3:
                            kwargs[parts[0].strip()] = parts[1] + parts[2].strip()
                        else:
                            kwargs[parts[0].strip()] = ""
                            
    resolved_profile = resolve_tree(kwargs)
    FILE_PROFILES[caller_file] = resolved_profile
    print(f"[PyManager] Profile set for {caller_file}: {resolved_profile}")

def get_caller_file():
    for frame_info in inspect.stack()[1:]:
        if 'importlib' not in frame_info.filename and 'pymanager' not in frame_info.filename:
            return os.path.abspath(frame_info.filename)
    return None

class PyManagerFinder(importlib.abc.MetaPathFinder):
    def find_distributions(self, context=None):
        """Fixes importlib.metadata / pkg_resources DistributionNotFound errors"""
        name = context.name if context else None
        if not name:
            return []
            
        db = load_db()
        from importlib.metadata import PathDistribution
        from pathlib import Path
        
        dists = []
        if name in db:
            # For simplicity, we just return the latest version's distribution data
            # since find_distributions is usually queried globally.
            try:
                from packaging.version import parse as parse_version
                latest_version = max(db[name].keys(), key=parse_version)
            except Exception:
                latest_version = max(db[name].keys())
                
            store_path = os.path.join(STORE_DIR, name, latest_version)
            if os.path.exists(store_path):
                for item in os.listdir(store_path):
                    if item.endswith('.dist-info'):
                        dists.append(PathDistribution(Path(os.path.join(store_path, item))))
                        break
        return dists

    def find_spec(self, fullname, path, target=None):
        base_module = fullname.split('.')[0]
        
        if base_module == 'pymanager' or base_module in sys.builtin_module_names:
            return None
            
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
            spec = importlib.machinery.PathFinder.find_spec(fullname, [store_path])
            if spec:
                mod_file = os.path.abspath(spec.origin) if spec.origin else None
                if mod_file and caller_file and caller_file in FILE_PROFILES:
                    FILE_PROFILES[mod_file] = FILE_PROFILES[caller_file]
                return spec
                
        return None

# Install the hook at the front of sys.meta_path
if not any(isinstance(finder, PyManagerFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, PyManagerFinder())

__all__ = ['require', 'absorb_packages']

