import re
from .store import load_db

try:
    from packaging.requirements import Requirement
    from packaging.version import parse as parse_version
except ImportError:
    Requirement = None
    parse_version = None

def resolve_version(pkg_name, requirement_str=None):
    db = load_db()
    pkg_name = pkg_name.lower().replace('_', '-')
    if pkg_name not in db:
        return None
        
    available_versions = list(db[pkg_name].keys())
    
    if not requirement_str or Requirement is None:
        if parse_version:
            return max(available_versions, key=parse_version)
        else:
            return max(available_versions)
            
    try:
        req = Requirement(requirement_str)
        valid_versions = [v for v in available_versions if parse_version(v) in req.specifier]
        if not valid_versions:
            return None
        return max(valid_versions, key=parse_version)
    except Exception:
        return None

def resolve_tree(requirements_dict):
    """
    Given a dict of {pkg_name: version_req}, returns a flat dict of {pkg_name: exact_version}
    that satisfies the tree.
    """
    db = load_db()
    resolved = {}
    queue = list(requirements_dict.items())
    processed = set()
    
    while queue:
        req_str, ver_req = queue.pop(0)
        
        if Requirement:
            try:
                req = Requirement(req_str)
                pkg_name = req.name
            except Exception:
                pkg_name = re.split(r'[=><~]', req_str)[0].strip()
        else:
            pkg_name = re.split(r'[=><~]', req_str)[0].strip()
            
        pkg_name = pkg_name.lower().replace('_', '-')
        
        if pkg_name in processed:
            continue
        processed.add(pkg_name)
        
        # Build the requirement string (e.g., 'requests>=2.0')
        full_req = f"{pkg_name}{ver_req}" if ver_req else pkg_name
        
        version = resolve_version(pkg_name, full_req)
        if version:
            resolved[pkg_name] = version
            
            # Add dependencies
            deps = db[pkg_name][version].get('requires', [])
            for dep in deps:
                if ';' in dep:
                    dep = dep.split(';')[0].strip()
                if 'extra ==' not in dep:
                    queue.append((dep, ""))
                    
    return resolved
