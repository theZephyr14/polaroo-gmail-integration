#!/usr/bin/env python3
"""
Gmail Credentials Setup
======================

Helps you set up Gmail credentials for automatic login.
"""

import os
import getpass
import json
from pathlib import Path

def setup_credentials():
    """Set up Gmail credentials."""
    print("🔐 Gmail Credentials Setup")
    print("=" * 40)
    print()
    print("To enable automatic Gmail login, you need to:")
    print("1. Use an App Password (not your regular password)")
    print("2. Enable 2-Factor Authentication on your Google account")
    print("3. Generate an App Password for Gmail")
    print()
    print("Steps to get App Password:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Factor Authentication if not already enabled")
    print("3. Go to 'App passwords' section")
    print("4. Generate a new app password for 'Mail'")
    print("5. Copy the 16-character password")
    print()
    
    # Get credentials from user
    email = input("Enter your Gmail address: ").strip()
    if not email or '@' not in email:
        print("❌ Invalid email address")
        return False
    
    print("\nEnter your Gmail App Password (16 characters, no spaces):")
    password = getpass.getpass("App Password: ").strip()
    if len(password) != 16:
        print("❌ App Password should be 16 characters")
        return False
    
    # Save credentials
    credentials = {
        'email': email,
        'password': password
    }
    
    # Save to .env file
    env_file = Path('.env')
    with open(env_file, 'w') as f:
        f.write(f"GMAIL_EMAIL={email}\n")
        f.write(f"GMAIL_PASSWORD={password}\n")
    
    print(f"\n✅ Credentials saved to {env_file}")
    print("✅ You can now run the auto Gmail demo!")
    
    return True

def load_credentials():
    """Load credentials from .env file."""
    env_file = Path('.env')
    if not env_file.exists():
        return None, None
    
    email = None
    password = None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('GMAIL_EMAIL='):
                email = line.split('=', 1)[1].strip()
            elif line.startswith('GMAIL_PASSWORD='):
                password = line.split('=', 1)[1].strip()
    
    return email, password

def main():
    """Main setup function."""
    print("🚀 Gmail Auto Login Setup")
    print("=" * 30)
    print()
    
    # Check if credentials already exist
    email, password = load_credentials()
    if email and password:
        print(f"✅ Credentials found for: {email}")
        choice = input("Do you want to update them? (y/n): ").lower()
        if choice != 'y':
            print("Using existing credentials...")
            return
    
    # Setup new credentials
    if setup_credentials():
        print("\n🎉 Setup complete!")
        print("You can now run: python auto_gmail_demo.py")
    else:
        print("\n❌ Setup failed!")

if __name__ == "__main__":
    main()
