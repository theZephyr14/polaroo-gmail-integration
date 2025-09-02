#!/usr/bin/env python3
"""
Test script to check if the application can start properly
"""

import sys
import os

print("Testing application startup...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("\n1. Testing basic imports...")
    from fastapi import FastAPI
    print("✅ FastAPI import successful")
    
    from pydantic import BaseModel
    print("✅ Pydantic import successful")
    
    import pandas as pd
    print("✅ Pandas import successful")
    
    print("\n2. Testing src imports...")
    from src.config import POLAROO_EMAIL, POLAROO_PASSWORD
    print("✅ Config import successful")
    print(f"   POLAROO_EMAIL: {'SET' if POLAROO_EMAIL else 'NOT SET'}")
    print(f"   POLAROO_PASSWORD: {'SET' if POLAROO_PASSWORD else 'NOT SET'}")
    
    from src.polaroo_scrape import download_report_sync
    print("✅ Polaroo scrape import successful")
    
    from src.polaroo_process import process_usage
    print("✅ Polaroo process import successful")
    
    from src.load_supabase import upload_raw
    print("✅ Supabase import successful")
    
    print("\n3. Testing FastAPI app creation...")
    app = FastAPI(title="Test App")
    print("✅ FastAPI app creation successful")
    
    print("\n4. Testing API import...")
    from api import app as main_app
    print("✅ Main API import successful")
    
    print("\n🎉 All tests passed! Application should start successfully.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
