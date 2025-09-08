#!/usr/bin/env python3
"""
Script to prepare files for deployment to Render or Railway.
This creates a clean deployment package without local files.
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a clean deployment package."""
    
    # Files to include in deployment
    include_files = [
        'api.py',
        'requirements.txt',
        'render.yaml',
        'Procfile',
        'runtime.txt',
        'src/',
        'README.md'
    ]
    
    # Files to exclude
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        '.env',
        '.venv',
        'node_modules',
        '.git',
        '_debug',
        'etl',
        '*.csv',
        '*.xlsx',
        'start_server.py',
        'deploy.sh'
    ]
    
    print("🚀 Preparing deployment package...")
    
    # Create deployment directory
    deploy_dir = Path('deployment')
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Copy files
    for item in include_files:
        src = Path(item)
        dst = deploy_dir / item
        
        if src.is_file():
            print(f"📄 Copying {item}")
            shutil.copy2(src, dst)
        elif src.is_dir():
            print(f"📁 Copying {item}/")
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude_patterns))
    
    # Create ZIP file
    zip_path = Path('polaroo-deployment.zip')
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"📦 Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(deploy_dir)
                zipf.write(file_path, arc_path)
    
    # Clean up
    shutil.rmtree(deploy_dir)
    
    print(f"✅ Deployment package created: {zip_path}")
    print(f"📏 Package size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("\n🎯 Next steps:")
    print("1. Go to https://render.com")
    print("2. Create a new Web Service")
    print("3. Upload polaroo-deployment.zip")
    print("4. Add your environment variables")
    print("5. Deploy!")

if __name__ == "__main__":
    create_deployment_package()
