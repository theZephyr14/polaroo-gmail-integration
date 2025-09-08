#!/usr/bin/env python3
"""
Offline System Runner
=====================

This script runs the utility bill calculator system in offline mode
for testing the email and invoice management features.
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add src to path
sys.path.append('src')

def check_requirements():
    """Check if all required files exist."""
    required_files = [
        'src/api.py',
        'src/email_system/__init__.py',
        'src/email_system/email_generator.py',
        'src/email_system/invoice_downloader.py',
        'src/email_system/email_sender.py',
        'src/email_system/template_manager.py',
        'email_templates.xlsx',
        'src/static/index.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files found")
    return True

def create_sample_data():
    """Create sample data for testing."""
    print("📊 Creating sample data...")
    
    # Create _debug directory if it doesn't exist
    debug_dir = Path("_debug")
    debug_dir.mkdir(exist_ok=True)
    
    # Create invoices directory
    invoices_dir = debug_dir / "invoices"
    invoices_dir.mkdir(exist_ok=True)
    
    print("✅ Sample data directories created")

def main():
    """Main function to run the offline system."""
    print("🚀 Starting Offline Utility Bill Calculator System")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("❌ System requirements not met. Please check missing files.")
        return False
    
    # Create sample data
    create_sample_data()
    
    print("\n🌐 Starting web server...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("📧 Email Management tab will be available for testing")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run the FastAPI server
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
