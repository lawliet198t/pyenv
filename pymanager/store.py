import os
import shutil
import json
from email import message_from_string

import sys
STORE_DIR = os.path.expanduser(f"~/pyenv/central_store/py{sys.version_info.major}.{sys.version_info.minor}")
DB_PATH = os.path.join(STORE_DIR, "db.json")

def init_store():
    if not os.path.exists(STORE_DIR):
        os.makedirs(STORE_DIR)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w') as f:
            json.dump({}, f)

def load_db():
    init_store()
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def save_db(db):
    tmp_path = DB_PATH + ".tmp"
    with open(tmp_path, 'w') as f:
        json.dump(db, f, indent=2)
    os.replace(tmp_path, DB_PATH)

def find_site_packages(root_dir):
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.cache', 'Downloads', 'Documents', 'Pictures', 'central_store', 'pymanager'}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.npm')]
        if os.path.basename(dirpath) == 'site-packages':
            yield dirpath

def parse_metadata(metadata_path):
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            msg = message_from_string(f.read())
            requires = msg.get_all('Requires-Dist') or []
            return {
                'name': msg.get('Name'),
                'version': msg.get('Version'),
                'requires_dist': requires
            }
    except Exception:
        return None

def absorb_packages(root_dir):
    """
    Scans the system for site-packages and MOVES unique versions into the central store.
    If a version is already in the central store, the duplicate is DELETED to save space.
    """
    print(f"Scanning {root_dir} for packages to absorb into central store...")
    init_store()
    
    lock_file = os.path.join(STORE_DIR, "absorb.lock")
    try:
        import fcntl
        lf = open(lock_file, 'w')
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (ImportError, BlockingIOError, OSError):
        try:
            if 'lf' in locals(): lf.close()
        except Exception: pass
        if 'BlockingIOError' in str(sys.exc_info()[0]) or 'BlockingIOError' in str(sys.exc_info()[1]):
            print("[PyManager] Another process is already absorbing packages. Skipping.")
            return
            
    try:
        db = load_db()
        
        for site_pkg in find_site_packages(root_dir):
            for item in os.listdir(site_pkg):
                # Skip editable installs and symlinks
                if item.endswith('.egg-link') or os.path.islink(os.path.join(site_pkg, item)):
                    continue
                    
                if item.endswith('.dist-info'):
                    dist_info_dir = os.path.join(site_pkg, item)
                    if os.path.islink(dist_info_dir):
                        continue
                        
                    metadata_path = os.path.join(dist_info_dir, 'METADATA')
                    if os.path.exists(metadata_path):
                        pkg_info = parse_metadata(metadata_path)
                        if not pkg_info or not pkg_info['name'] or not pkg_info['version']:
                            continue
                            
                        name = pkg_info['name'].lower().replace('_', '-')
                        version = pkg_info['version']
                        
                        if name not in db:
                            db[name] = {}
                            
                        top_level_path = os.path.join(dist_info_dir, 'top_level.txt')
                        modules = []
                        if os.path.exists(top_level_path):
                            with open(top_level_path, 'r') as f:
                                modules = [m.strip() for m in f.readlines() if m.strip()]
                        else:
                            record_path = os.path.join(dist_info_dir, 'RECORD')
                            if os.path.exists(record_path):
                                with open(record_path, 'r') as f:
                                    for line in f:
                                        filepath = line.split(',')[0]
                                        top_dir = filepath.split('/')[0].split('\\')[0]
                                        if not top_dir.endswith('.dist-info') and top_dir not in modules:
                                            if top_dir.endswith('.py'): top_dir = top_dir[:-3]
                                            modules.append(top_dir)
                            if not modules:
                                modules = [pkg_info['name'].replace('-', '_')]
                                
                        if version not in db[name]:
                            print(f"Moving new package to central store: {name} v{version}")
                            target_dir = os.path.join(STORE_DIR, name, version)
                            os.makedirs(target_dir, exist_ok=True)
                        
                        # Move the dist-info
                        shutil.move(dist_info_dir, os.path.join(target_dir, item))
                        
                        # Move the actual module folders/files
                        for mod in modules:
                            src_mod_dir = os.path.join(site_pkg, mod)
                            src_mod_file = os.path.join(site_pkg, mod + '.py')
                            if os.path.isdir(src_mod_dir):
                                shutil.move(src_mod_dir, os.path.join(target_dir, mod))
                            elif os.path.isfile(src_mod_file):
                                shutil.move(src_mod_file, os.path.join(target_dir, mod + '.py'))
                                
                        db[name][version] = {
                            'requires': pkg_info['requires_dist'],
                            'modules': modules
                        }
                        save_db(db)
                    else:
                        # It is already in the database, meaning this is a duplicate!
                        print(f"Deleting duplicate package to save space: {name} v{version} at {site_pkg}")
                        
                        # Delete the dist-info
                        if os.path.exists(dist_info_dir):
                            shutil.rmtree(dist_info_dir)
                            
                        # Delete the modules
                        for mod in modules:
                            src_mod_dir = os.path.join(site_pkg, mod)
                            src_mod_file = os.path.join(site_pkg, mod + '.py')
                            if os.path.isdir(src_mod_dir):
                                shutil.rmtree(src_mod_dir)
                            elif os.path.isfile(src_mod_file):
                                os.remove(src_mod_file)
                        
    finally:
        try:
            if 'lf' in locals():
                import fcntl
                fcntl.flock(lf, fcntl.LOCK_UN)
                lf.close()
        except Exception:
            pass
            
    print("Absorption and deduplication complete.")
