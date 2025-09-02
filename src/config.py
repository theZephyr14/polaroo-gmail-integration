import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

POLAROO_EMAIL = os.getenv("POLAROO_EMAIL")
POLAROO_PASSWORD = os.getenv("POLAROO_PASSWORD")

STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "polaroo")
STORAGE_PREFIX = os.getenv("STORAGE_PREFIX", "raw")
STORAGE_STATE_PATH = os.getenv("STORAGE_STATE_PATH", "./.auth/polaroo-state.json")

REPORT_DATE = os.getenv("REPORT_DATE")  # YYYY-MM-DD or None
