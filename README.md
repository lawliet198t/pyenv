# PyManager (Centralized Python Library Manager)

PyManager is a revolutionary, storage-efficient alternative to Python virtual environments (`venv`). It eliminates the need for redundant package installations across multiple projects by centralizing all installed packages into a single, deduplicated `central_store`. 

With PyManager, you never need to activate a virtual environment again. It dynamically resolves dependencies and natively injects the required package versions for any Python script on the fly.

## Features
- **Total Deduplication**: Absorbs and consolidates packages from your global environment into a single store.
- **Global Native Hook**: Uses a Python `.pth` global hook and `sys.meta_path` finder to intercept imports safely and automatically.
- **Zero Config for Existing Scripts**: Automatically reads a local `requirements.txt` to determine which version of a library a project needs, and seamlessly loads it in memory.
- **Auto Fallback**: If no specific version is requested, PyManager automatically serves the latest version available in the central store.

## Installation

Run the universal installer on any OS (Linux, macOS, Windows):

```bash
chmod +x install.py
./install.py
```

This script automatically locates your system's global `site-packages` directory and installs a `.pth` hook, configuring your machine to use PyManager automatically.

## Usage

### 1. Absorb Existing Packages
To crawl your system and move all installed Python packages into your new central store (and delete the duplicates to save space), run:
```bash
./manage.py absorb
```

### 2. Run your code!
Just run your Python scripts normally:
```bash
python3 my_script.py
```
PyManager will intercept imports transparently. If there is a `requirements.txt` in the same directory as your script, PyManager uses it to load the exact requested versions.

### 3. Mass Codebase Migration (Optional)
If you want to explicitly require PyManager initialization at the top of your files (useful if you don't use the global `.pth` hook), you can use the mass editor on any project:
```bash
./mass_edit.py /path/to/my/project
```
This safely injects the PyManager initialization block into every `.py` file in the targeted project folder.

### 4. Revert Mass Migration
If you need to undo the manual mass-edit injection, just run:
```bash
./mass_undo.py /path/to/my/project
```

## How it works

Instead of hacking `sys.modules` or overriding the legacy `builtins.__import__`, PyManager registers a modern Python 3 `MetaPathFinder` in `sys.meta_path`. When a module is imported, PyManager looks up the calling file's dependency profile (derived from `requirements.txt`) and returns a standard `ModuleSpec` pointing directly into the deduplicated `central_store`.
