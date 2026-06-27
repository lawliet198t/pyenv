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
    for frame_info in inspect.stack()[2:]:
        # Skip internal pymanager or importlib frames
        if 'importlib' not in frame_info.filename and 'pymanager' not in frame_info.filename:
            return os.path.abspath(frame_info.filename)
    return None

def find_module_in_store(module_name, target_pkg, target_version):
    """
    Manually find and load the module from our central store.
    """
    cache_key = (target_pkg, target_version, module_name)
    if cache_key in LOADED_MODULES_CACHE:
        return LOADED_MODULES_CACHE[cache_key]
        
    store_path = os.path.join(STORE_DIR, target_pkg, target_version)
    
    # Temporarily set sys.path to just this directory to find the spec
    old_path = sys.path[:]
    sys.path = [store_path]
    try:
        spec = importlib.machinery.PathFinder.find_spec(module_name)
    finally:
        sys.path = old_path
        
    if not spec:
        return None
        
    module = importlib.util.module_from_spec(spec)
    
    # Crucial: Register the file path as part of this profile!
    # So if this module imports something else, we know its profile.
    mod_file = os.path.abspath(spec.origin) if spec.origin else None
    if mod_file:
        # It inherits the dependencies of the package it belongs to
        # But for simplicity, we'll map it to the exact same versions resolved
        pass 
        
    # We execute the module. Note: any imports inside this module will call our custom_import!
    LOADED_MODULES_CACHE[cache_key] = module
    
    # We need to temporarily set the caller's profile to this module so it inherits dependencies.
    # Since we are executing it now, we can just let custom_import use the stack to find mod_file.
    if mod_file:
        # Find the profile from the original caller (we will just reuse the exact versions)
        caller_file = get_caller_file()
        if caller_file in FILE_PROFILES:
            FILE_PROFILES[mod_file] = FILE_PROFILES[caller_file]
            
    spec.loader.exec_module(module)
    return module

def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    caller_file = get_caller_file()
    
    # Determine base module
    base_module = name.split('.')[0] if level == 0 else globals.get('__package__', '').split('.')[0]
    if not base_module:
        base_module = name.split('.')[0]
        
    db = load_db()
    target_pkg = None
    target_version = None

    if caller_file and caller_file in FILE_PROFILES and FILE_PROFILES[caller_file]:
        profile = FILE_PROFILES[caller_file]
        # Find which package provides this module based on profile
        for pkg_name, version in profile.items():
            if pkg_name in db and version in db[pkg_name]:
                if base_module in db[pkg_name][version].get('modules', []):
                    target_pkg = pkg_name
                    target_version = version
                    break
    
    # If no profile or not found in profile, fallback to the latest available in store
    if not target_pkg:
        for pkg_name, versions in db.items():
            # Check if this package provides the module
            # We just take the latest version and check its 'modules'
            # Note: A proper search would check all versions, but latest is a good heuristic
            from packaging.version import parse as parse_version
            try:
                latest_version = max(versions.keys(), key=parse_version)
            except Exception:
                latest_version = max(versions.keys())
                
            if base_module in versions[latest_version].get('modules', []):
                target_pkg = pkg_name
                target_version = latest_version
                break
                
    if target_pkg:
        # We must load it from the central store manually to bypass sys.modules
        mod = find_module_in_store(name, target_pkg, target_version)
        if mod:
            if fromlist:
                return mod
            else:
                return mod

    # Fallback to standard import
    return original_import(name, globals, locals, fromlist, level)

# Install the hook
builtins.__import__ = custom_import

__all__ = ['require', 'absorb_packages']
