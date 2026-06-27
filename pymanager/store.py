import os
import shutil
import json
from email import message_from_string

STORE_DIR = os.path.expanduser("/home/sashna/pyenv/central_store")
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
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

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
    db = load_db()
    
    for site_pkg in find_site_packages(root_dir):
        # We process .dist-info directories
        for item in os.listdir(site_pkg):
            if item.endswith('.dist-info'):
                metadata_path = os.path.join(site_pkg, item, 'METADATA')
                if os.path.exists(metadata_path):
                    pkg_info = parse_metadata(metadata_path)
                    if not pkg_info or not pkg_info['name'] or not pkg_info['version']:
                        continue
                        
                    name = pkg_info['name'].lower().replace('_', '-')
                    version = pkg_info['version']
                    
                    if name not in db:
                        db[name] = {}
                        
                    # Find top_level.txt to know which folders/files to move/delete
                    top_level_path = os.path.join(site_pkg, item, 'top_level.txt')
                    modules = []
                    if os.path.exists(top_level_path):
                        with open(top_level_path, 'r') as f:
                            modules = [m.strip() for m in f.readlines() if m.strip()]
                    else:
                        # Guess the module name (often same as package name)
                        modules = [pkg_info['name'].replace('-', '_')]
                        
                    dist_info_dir = os.path.join(site_pkg, item)
                        
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
                        
    print("Absorption and deduplication complete.")
