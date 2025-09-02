import os
import sys
import re
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
REPORT_MONTH_STR = os.getenv("POLAROO_REPORT_MONTH")  # e.g., 2025-07
if REPORT_MONTH_STR is None:
    # fallback: last full month from "today"
    today = datetime.utcnow()
    last_month = (today.replace(day=1) - pd.offsets.MonthBegin(1)).date()
    REPORT_MONTH_STR = last_month.strftime("%Y-%m")

REPORT_MONTH_DATE = pd.to_datetime(REPORT_MONTH_STR + "-01").date()

# --- canonical header mapping (keep 5 water + 5 elec exactly) ---
HEADER_MAP = {
    # identity from CSV (often "name")
    "name": "address_raw",

    # electricity (5)
    "electricitycode": "elec_code",
    "electricityprovider": "elec_provider",
    "electricityserviceowner": "elec_owner",
    "electricityconsumption": "elec_consumption_kwh",
    "electricitycost": "elec_cost_eur",

    # water (5)
    "watercode": "water_code",
    "waterprovider": "water_provider",
    "waterserviceowner": "water_owner",
    "waterconsumption": "water_consumption_m3",
    "watercost": "water_cost_eur",
}

# sometimes headers come truncated like "waterProvi", "waterServi" in your screenshot.
# we'll allow a few safe aliases:
ALIASES = {
    "waterprovi": "waterprovider",
    "waterservi": "waterserviceowner",
    "watercons": "waterconsumption",
    "wateraver": "watercost",  # if file has 'waterAverageCost' but you bill against total cost, prefer waterCost
    "electricityc": "electricitycost",
    "electricitycons": "electricityconsumption",
    "electricityprovi": "electricityprovider",
    "electricityservi": "electricityserviceowner",
}

NUMERIC_COLS = {
    "elec_consumption_kwh",
    "elec_cost_eur",
    "water_consumption_m3",
    "water_cost_eur",
}

def normalize_header(h: str) -> str:
    if h is None:
        return ""
    key = re.sub(r"[^a-zA-Z]", "", h).lower()  # strip non-letters and lowercase
    key = ALIASES.get(key, key)
    return key

def parse_numeric(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    # handle comma decimals "1.234,56" and dot decimals "1234.56"
    s = s.replace(" ", "")
    if re.search(r",\d{1,2}$", s) and s.count(",") == 1 and s.count(".") <= 1:
        s = s.replace(".", "").replace(",", ".")  # "1.234,56" -> "1234.56"
    try:
        return float(s)
    except:
        return None

def canonicalize_address(addr_raw: str) -> str:
    if not addr_raw:
        return None
    a = addr_raw.strip()
    # minimal cleanup; you can extend with your map later
    a = re.sub(r"\s+", " ", a)
    # unify common prefixes
    a = re.sub(r"^C\/\s*", "C/", a, flags=re.IGNORECASE)
    return a

def main(csv_path: str):
    # read CSV with either ; or , as separator
    # try ; first since your file uses semicolons in some sections
    try:
        df = pd.read_csv(csv_path, sep=";", engine="python")
        if df.shape[1] == 1:
            # not actually ; separated
            df = pd.read_csv(csv_path)
    except Exception:
        df = pd.read_csv(csv_path)

    # normalize headers
    df.columns = [normalize_header(c) for c in df.columns]

    # keep only columns we know how to map
    keep_keys = set(HEADER_MAP.keys())
    present = [c for c in df.columns if c in keep_keys]
    if "name" not in present and "address_raw" not in present:
        raise RuntimeError("Expected a 'name' column for address_raw in the CSV.")

    # rename to canonical names
    df = df[present].rename(columns=HEADER_MAP)

    # attach report_month and canonical address
    df["report_month"] = REPORT_MONTH_DATE
    df["address"] = df["address_raw"].apply(canonicalize_address)

    # numeric cleanup
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(parse_numeric)

    # fill missing utility sides with 0 so we always have a row
    for col in ["elec_consumption_kwh", "elec_cost_eur", "water_consumption_m3", "water_cost_eur"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = df[col].fillna(0.0)

    # provenance
    df["source_file_name"] = os.path.basename(csv_path)

    # drop obvious empties
    df = df[~df["address"].isna() & (df["address"] != "")]

    # UPSERT to Supabase
    supa: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # chunked upsert for safety
    records = df.to_dict(orient="records")
    table = supa.table("polaroo_monthly")
    batch = 1000
    for i in range(0, len(records), batch):
        chunk = records[i:i+batch]
        (
            table.upsert(chunk, on_conflict="address,report_month")
            .execute()
        )

    print(f"Upserted {len(records)} rows for report_month={REPORT_MONTH_STR}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python etl/load_polaroo_monthly.py /path/to/csv.csv")
        sys.exit(1)
    main(sys.argv[1])
