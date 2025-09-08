#!/usr/bin/env python3
"""
Gmail API Setup Helper
======================

This script helps you set up Gmail API credentials step by step.
"""

import os
import webbrowser
from pathlib import Path

def check_credentials():
    """Check if credentials.json exists."""
    creds_file = Path('credentials.json')
    if creds_file.exists():
        print("✅ credentials.json found!")
        return True
    else:
        print("❌ credentials.json not found")
        return False

def check_packages():
    """Check if required packages are installed."""
    try:
        import google.auth
        import googleapiclient
        print("✅ Google API packages installed")
        return True
    except ImportError:
        print("❌ Google API packages not installed")
        print("   Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

def open_google_console():
    """Open Google Cloud Console."""
    print("🌐 Opening Google Cloud Console...")
    webbrowser.open("https://console.cloud.google.com/")

def show_setup_steps():
    """Show detailed setup steps."""
    print("\n📋 Gmail API Setup Steps:")
    print("=" * 50)
    print("1. 🌐 Go to Google Cloud Console (opening now...)")
    print("2. 📁 Create a new project or select existing one")
    print("3. 🔧 Enable Gmail API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Gmail API'")
    print("   - Click 'Enable'")
    print("4. 🔑 Create OAuth 2.0 Credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click '+ Create Credentials' > 'OAuth client ID'")
    print("   - Choose 'Desktop application'")
    print("   - Name it 'Email Draft Generator'")
    print("5. 📥 Download credentials:")
    print("   - Click the download button")
    print("   - Save as 'credentials.json' in this folder")
    print("6. ⚙️  Configure OAuth Consent Screen:")
    print("   - Go to 'APIs & Services' > 'OAuth consent screen'")
    print("   - Choose 'External' (unless you have Google Workspace)")
    print("   - Fill required fields and add your email as test user")
    print("=" * 50)

def main():
    """Main setup function."""
    print("🚀 Gmail API Setup Helper")
    print("=" * 30)
    
    # Check packages first
    if not check_packages():
        print("\n⚠️  Please install required packages first:")
        print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return
    
    # Check credentials
    if check_credentials():
        print("\n🎉 Setup complete! You can now run the draft generator.")
        print("   Run: python run_draft_generator.py")
        return
    
    # Show setup steps and open console
    show_setup_steps()
    
    # Ask if user wants to open Google Console
    open_console = input("\n🌐 Open Google Cloud Console now? (y/n): ").strip().lower()
    if open_console == 'y':
        open_google_console()
    
    print("\n💡 After completing the setup:")
    print("   1. Make sure 'credentials.json' is in this folder")
    print("   2. Run: python run_draft_generator.py")
    print("   3. The first time will open a browser for OAuth consent")

if __name__ == "__main__":
    main()
