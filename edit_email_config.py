#!/usr/bin/env python3
"""
Edit Email Config
================

Simple script to edit email credentials in email_config.json
"""

import json
import os
from pathlib import Path

def load_config():
    """Load current configuration"""
    config_file = Path("email_config.json")
    
    if not config_file.exists():
        print("❌ email_config.json not found!")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def save_config(config):
    """Save configuration to file"""
    config_file = Path("email_config.json")
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def edit_credentials():
    """Edit Gmail credentials"""
    print("🔐 Edit Gmail Credentials")
    print("=" * 30)
    
    config = load_config()
    if not config:
        return
    
    # Get current credentials
    current_email = config.get('gmail_credentials', {}).get('email', '')
    current_password = config.get('gmail_credentials', {}).get('password', '')
    
    print(f"Current email: {current_email}")
    print(f"Current password: {'*' * len(current_password)}")
    print()
    
    # Get new credentials
    new_email = input(f"Enter new Gmail address (or press Enter to keep current): ").strip()
    if not new_email:
        new_email = current_email
    
    new_password = input(f"Enter new password (or press Enter to keep current): ").strip()
    if not new_password:
        new_password = current_password
    
    # Update config
    if 'gmail_credentials' not in config:
        config['gmail_credentials'] = {}
    
    config['gmail_credentials']['email'] = new_email
    config['gmail_credentials']['password'] = new_password
    
    # Save config
    if save_config(config):
        print(f"\n✅ Updated Gmail credentials:")
        print(f"   Email: {new_email}")
        print(f"   Password: {'*' * len(new_password)}")
        print("\nYou can now run: python run_gmail_demo.py")

def edit_settings():
    """Edit email settings"""
    print("⚙️  Edit Email Settings")
    print("=" * 25)
    
    config = load_config()
    if not config:
        return
    
    # Get current settings
    settings = config.get('email_settings', {})
    auto_login = settings.get('auto_login', True)
    headless = settings.get('headless_mode', False)
    wait_time = settings.get('wait_time_between_emails', 2)
    
    print(f"Current settings:")
    print(f"  Auto login: {auto_login}")
    print(f"  Headless mode: {headless}")
    print(f"  Wait time between emails: {wait_time} seconds")
    print()
    
    # Get new settings
    auto_login_input = input(f"Auto login? (y/n, or press Enter to keep current): ").lower()
    if auto_login_input == 'y':
        auto_login = True
    elif auto_login_input == 'n':
        auto_login = False
    
    headless_input = input(f"Headless mode? (y/n, or press Enter to keep current): ").lower()
    if headless_input == 'y':
        headless = True
    elif headless_input == 'n':
        headless = False
    
    wait_time_input = input(f"Wait time between emails in seconds (or press Enter to keep current): ").strip()
    if wait_time_input:
        try:
            wait_time = int(wait_time_input)
        except ValueError:
            print("Invalid number, keeping current value")
    
    # Update config
    config['email_settings'] = {
        'auto_login': auto_login,
        'headless_mode': headless,
        'wait_time_between_emails': wait_time
    }
    
    # Save config
    if save_config(config):
        print(f"\n✅ Updated email settings:")
        print(f"   Auto login: {auto_login}")
        print(f"   Headless mode: {headless}")
        print(f"   Wait time: {wait_time} seconds")

def view_config():
    """View current configuration"""
    print("📋 Current Configuration")
    print("=" * 25)
    
    config = load_config()
    if not config:
        return
    
    credentials = config.get('gmail_credentials', {})
    settings = config.get('email_settings', {})
    properties = config.get('demo_properties', [])
    
    print(f"Gmail Credentials:")
    print(f"  Email: {credentials.get('email', 'Not set')}")
    print(f"  Password: {'*' * len(credentials.get('password', ''))}")
    print()
    
    print(f"Email Settings:")
    print(f"  Auto login: {settings.get('auto_login', True)}")
    print(f"  Headless mode: {settings.get('headless_mode', False)}")
    print(f"  Wait time: {settings.get('wait_time_between_emails', 2)} seconds")
    print()
    
    print(f"Demo Properties: {len(properties)} properties configured")
    for i, prop in enumerate(properties, 1):
        print(f"  {i}. {prop.get('name', 'Unknown')} - €{prop.get('total_extra', 0):.2f}")

def main():
    """Main menu"""
    while True:
        print("\n🔧 Email Config Editor")
        print("=" * 25)
        print("1. Edit Gmail credentials")
        print("2. Edit email settings")
        print("3. View current configuration")
        print("4. Exit")
        print()
        
        choice = input("Choose an option (1-4): ").strip()
        
        if choice == '1':
            edit_credentials()
        elif choice == '2':
            edit_settings()
        elif choice == '3':
            view_config()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()
