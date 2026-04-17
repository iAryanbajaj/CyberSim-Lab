#!/usr/bin/env python3
"""
CyberSim Lab - Windows EXE Builder Engine
Builds standalone Windows .exe from Python script on Linux (no Wine needed)
Uses: Windows Embeddable Python + ZIP append technique
"""
import os, sys, zipfile, io, shutil, tempfile

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBED_DIR = os.path.join(BASE_DIR, '_embed_python')
BOOTLOADER = os.path.join(EMBED_DIR, 'pythonw.exe')

def ensure_embed_python():
    """Download and setup Windows embeddable Python if not present"""
    if os.path.exists(BOOTLOADER):
        return True
    
    os.makedirs(EMBED_DIR, exist_ok=True)
    zip_path = os.path.join(EMBED_DIR, 'pyembed.zip')
    
    # Download Windows embeddable Python 3.13
    import urllib.request
    url = 'https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip'
    print(f"[BUILD] Downloading Windows Python 3.13 embeddable...")
    urllib.request.urlretrieve(url, zip_path)
    
    # Extract
    shutil.unpack_archive(zip_path, EMBED_DIR)
    os.remove(zip_path)
    
    # Configure ._pth for site-packages
    pth_path = os.path.join(EMBED_DIR, 'python313._pth')
    with open(pth_path, 'w') as f:
        f.write('python313.zip\n.\nimport site\n')
    
    # Create Lib/site-packages dir
    os.makedirs(os.path.join(EMBED_DIR, 'Lib', 'site-packages'), exist_ok=True)
    
    # Download essential packages
    import subprocess
    wheels_dir = os.path.join(EMBED_DIR, '_wheels')
    os.makedirs(wheels_dir, exist_ok=True)
    
    packages = ['requests>=2.28.0', 'Pillow>=9.0.0', 'pynput>=1.7.6']
    subprocess.run([
        sys.executable, '-m', 'pip', 'download',
        '--platform', 'win_amd64', '--python-version', '313',
        '--only-binary=:all:', '-d', wheels_dir
    ] + packages, capture_output=True)
    
    # Extract wheels
    sp_dir = os.path.join(EMBED_DIR, 'Lib', 'site-packages')
    for whl in os.listdir(wheels_dir):
        if whl.endswith('.whl'):
            shutil.unpack_archive(os.path.join(wheels_dir, whl), sp_dir)
    
    # Clean up
    shutil.rmtree(wheels_dir, ignore_errors=True)
    print(f"[BUILD] Windows Python ready: {EMBED_DIR}")
    return True


def build_exe(script_content, output_name='SystemUpdate'):
    """
    Build a standalone Windows .exe from Python script.
    Returns: (file_path, file_size)
    """
    ensure_embed_python()
    
    # Create ZIP package
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Main script
        zf.writestr('__main__.py', script_content)
        
        # site-packages
        sp_dir = os.path.join(EMBED_DIR, 'Lib', 'site-packages')
        if os.path.exists(sp_dir):
            for root, dirs, files in os.walk(sp_dir):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for f in files:
                    fp = os.path.join(root, f)
                    arc = os.path.join('Lib', 'site-packages', os.path.relpath(fp, sp_dir))
                    zf.write(fp, arc)
        
        # DLLs, PYDs, .pth, .zip from embed dir
        for f in os.listdir(EMBED_DIR):
            if any(f.endswith(ext) for ext in ('.dll', '.pyd', '._pth', '.zip', '.cat')):
                zf.write(os.path.join(EMBED_DIR, f), f)
    
    zip_data = zip_buf.getvalue()
    
    # Read bootloader
    with open(BOOTLOADER, 'rb') as f:
        boot = f.read()
    
    exe_data = boot + zip_data
    return exe_data


if __name__ == '__main__':
    test = 'import sys; print(f"EXE OK! {sys.version}"); input()'
    data = build_exe(test)
    out = '/tmp/test_build.exe'
    with open(out, 'wb') as f:
        f.write(data)
    print(f"Built: {out} ({len(data):,} bytes)")