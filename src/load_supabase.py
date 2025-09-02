import io, hashlib
from datetime import date
from supabase import create_client
from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_BUCKET, STORAGE_PREFIX

def _client():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def _md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

def upload_raw(report_date: date, file_bytes: bytes, filename: str) -> str:
    supa = _client()
    md5 = _md5(file_bytes)
    path = f"{STORAGE_PREFIX}/{report_date.isoformat()}/{md5}_{filename}"
    supa.storage.from_(STORAGE_BUCKET).upload(
        path=path, file=io.BytesIO(file_bytes),
        file_options={"cache-control":"3600","content-type":"application/octet-stream","upsert":True}
    )
    return path

def upsert_kpis(kpi: dict):
    _client().table("polaroo_kpis").upsert(kpi).execute()

def upsert_monthly(rows: list[dict]):
    if not rows: return
    supa = _client()
    for i in range(0, len(rows), 1000):
        supa.table("polaroo_monthly_service").upsert(rows[i:i+1000]).execute()

def upsert_assets(rows: list[dict]):
    if not rows: return
    supa = _client()
    for i in range(0, len(rows), 500):
        supa.table("polaroo_asset_costs").upsert(rows[i:i+500]).execute()
