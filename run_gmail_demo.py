#!/usr/bin/env python3
"""
Run Gmail Demo
==============

Simple script to run the Gmail demo using credentials from email_config.json
"""

import json
import os
import sys
from pathlib import Path

def load_config():
    """Load configuration from email_config.json"""
    config_file = Path("email_config.json")
    
    if not config_file.exists():
        print("❌ email_config.json not found!")
        print("   Please create the config file with your Gmail credentials")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def set_environment_variables(config):
    """Set environment variables from config"""
    credentials = config.get('gmail_credentials', {})
    os.environ['GMAIL_EMAIL'] = credentials.get('email', '')
    os.environ['GMAIL_PASSWORD'] = credentials.get('password', '')
    
    print(f"📧 Using Gmail account: {credentials.get('email', 'Not set')}")
    print(f"🔐 Password: {'*' * len(credentials.get('password', ''))}")

def main():
    """Main function"""
    print("🚀 Gmail Demo Runner")
    print("=" * 30)
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Set environment variables
    set_environment_variables(config)
    
    # Import and run the auto Gmail demo
    try:
        from auto_gmail_demo import AutoGmailDemo
        
        demo = AutoGmailDemo()
        
        # Get settings from config
        settings = config.get('email_settings', {})
        auto_login = settings.get('auto_login', True)
        headless = settings.get('headless_mode', False)
        
        print(f"🔧 Auto login: {auto_login}")
        print(f"🔧 Headless mode: {headless}")
        print()
        
        # Run the demo
        success = demo.run_demo(auto_login=auto_login)
        
        if success:
            print("\n✅ Demo completed successfully!")
        else:
            print("\n❌ Demo failed!")
            
    except ImportError as e:
        print(f"❌ Error importing auto_gmail_demo: {e}")
        print("   Make sure auto_gmail_demo.py is in the same directory")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        if 'demo' in locals():
            demo.cleanup()

if __name__ == "__main__":
    main()
