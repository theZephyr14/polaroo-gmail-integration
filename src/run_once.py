from datetime import date
import argparse
from .config import REPORT_DATE
from .polaroo_scrape import download_report_sync
from .excel_parse import parse_excel_report
from .load_supabase import upload_raw, upsert_kpis, upsert_monthly, upsert_assets

def resolve_report_date() -> date:
    if REPORT_DATE:
        return date.fromisoformat(REPORT_DATE)
    # Madrid timezone stamp
    from zoneinfo import ZoneInfo
    from datetime import datetime
    return datetime.now(ZoneInfo("Europe/Madrid")).date()

def main():
    parser = argparse.ArgumentParser(description="Download, parse, load Polaroo report on demand.")
    parser.add_argument("--local-file", help="Skip scraping and use a local XLSX/CSV file", default=None)
    args = parser.parse_args()

    rpt_date = resolve_report_date()

    if args.local_file:
        with open(args.local_file, "rb") as f:
            file_bytes = f.read()
        filename = args.local_file.split("/")[-1]
    else:
        file_bytes, filename = download_report_sync()

    # Upload raw
    storage_path = upload_raw(rpt_date, file_bytes, filename)
    print(f"[raw] uploaded → {storage_path}")

    # Parse & load
    kpi, monthly_rows, asset_rows = parse_excel_report(file_bytes, rpt_date)
    upsert_kpis(kpi)
    upsert_monthly(monthly_rows)
    upsert_assets(asset_rows)

    print(f"[done] KPIs=1, monthly={len(monthly_rows)}, assets={len(asset_rows)} for {rpt_date}")

if __name__ == "__main__":
    main()
