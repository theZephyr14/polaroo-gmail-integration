import io
import pandas as pd
from datetime import date
from typing import Tuple

def _clean_money(x):
    if x is None: return None
    s = str(x).strip()
    if s == "" or s.lower() in ("nan","none"): return None
    s = s.replace(".", "").replace(",", ".") if s.count(",") and s.count(".")>1 else s
    # Safe float parse
    try: return float(s)
    except: return None

def _as_int(x):
    try:
        if x is None or str(x).strip()=="":
            return None
        return int(float(str(x).replace(",",".")))
    except:
        return None

def _as_bool(x):
    if x is None: return None
    s = str(x).strip().lower()
    if s in ("true","yes","1"): return True
    if s in ("false","no","0"): return False
    return None

def locate_blocks(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Assumes a single sheet with 3 logical tables.
    We heuristically locate:
      - KPIs: cells containing keys like 'activeAssets' etc. (key/value layout)
      - Monthly x Service: header row containing ['month','service','contracts','cost',...]
      - Asset wide table: header row containing 'name' and utility columns.
    """
    # Lowercase string view
    dfl = df.astype(str).applymap(lambda x: x.strip().lower())

    # Find monthly x service header
    m_cols = ["month","service","contracts","cost","averagecost","consumption"]
    m_row = None
    for r in range(len(dfl)):
        row = [dfl.iat[r,c] for c in range(len(dfl.columns))]
        if all(any(m in cell for cell in row) for m in ["month","service"]):
            # Quick check that most target columns are present in this row
            hits = sum(1 for m in m_cols if any(m in cell for cell in row))
            if hits >= 4:
                m_row = r
                break

    # Find asset wide header
    a_row = None
    for r in range(len(dfl)):
        row = [dfl.iat[r,c] for c in range(len(dfl.columns))]
        if any(cell=="name" for cell in row) and any("water" in cell for cell in row) and any("electricity" in cell for cell in row):
            a_row = r
            break

    # KPIs: look in top 10x10 for key/value-ish pairs
    kpi_section = df.iloc[:10,:6].copy()

    # Build monthly table
    monthly = pd.DataFrame()
    if m_row is not None:
        monthly = df.iloc[m_row:, :].copy()
        monthly.columns = monthly.iloc[0].astype(str).str.strip()
        monthly = monthly.iloc[1:].reset_index(drop=True)

    # Build asset table
    asset = pd.DataFrame()
    if a_row is not None:
        asset = df.iloc[a_row:, :].copy()
        asset.columns = asset.iloc[0].astype(str).str.strip()
        asset = asset.iloc[1:].reset_index(drop=True)

    return kpi_section, monthly, asset

def parse_excel_report(file_bytes: bytes, report_date: date):
    # Read first sheet with header=None so we can detect blocks
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=None, engine="openpyxl")
    kpi_block, monthly_raw, asset_raw = locate_blocks(raw)

    # --- KPIs (single row)
    # Try to locate values anywhere in the small block
    text = kpi_block.astype(str).values.tolist()
    flat = [str(x).strip() for row in text for x in row]
    def find_after(key):
        key = key.lower()
        for i,v in enumerate(flat):
            if v.lower().replace(" ","") in (key,):
                # value likely in next non-empty cell
                for j in range(i+1, min(i+4, len(flat))):
                    if flat[j] and flat[j].lower() not in (key,):
                        return flat[j]
        return None

    kpi = {
        "report_date": report_date.isoformat(),
        "active_assets": _as_int(find_after("activeassets")),
        "active_services": _as_int(find_after("activeservices")),
        "total_cost": _clean_money(find_after("cost")),
        "avg_cost_per_asset": _clean_money(find_after("averagecostbyasset")),
    }

    # --- Monthly x Service
    if not monthly_raw.empty:
        # Normalize column names (strip & lowercase)
        monthly_raw.columns = [str(c).strip().lower() for c in monthly_raw.columns]
        # Expect at least these keys; others are ignored
        monthly_rows = []
        for _, r in monthly_raw.iterrows():
            if str(r.get("month", "")).strip() == "" and str(r.get("service", "")).strip() == "":
                continue
            month_val = str(r.get("month", "")).strip()
            # Accept 'YYYY-MM' or dates
            try:
                if len(month_val) == 7 and month_val[4] == "-":
                    month_date = pd.to_datetime(month_val + "-01").date()
                else:
                    month_date = pd.to_datetime(month_val).date().replace(day=1)
            except:
                continue
            monthly_rows.append({
                "report_date": report_date.isoformat(),
                "month": month_date.isoformat(),
                "service": str(r.get("service", "")).strip().lower() or None,
                "contracts": _as_int(r.get("contracts")),
                "total_cost": _clean_money(r.get("cost")),
                "avg_cost": _clean_money(r.get("averagecost")),
                "consumption": _clean_money(r.get("consumption")),
            })
    else:
        monthly_rows = []

    # --- Asset wide table
    asset_rows = []
    if not asset_raw.empty:
        cols = [str(c).strip() for c in asset_raw.columns]
        asset_raw.columns = cols
        for _, r in asset_raw.iterrows():
            name = str(r.get("name","")).strip()
            if not name:
                continue
            def g(k): return r.get(k)
            asset_rows.append({
                "report_date": report_date.isoformat(),
                "name": name,

                "generaltotalcost": _clean_money(g("generalTotalCost")),
                "generaltotalcostbym2": _clean_money(g("generalTotalCostByM2")),

                "assetssize": _as_int(g("assetSize")),   # keep your current column name
                "assetpeople": _as_int(g("assetPeople")),
                "assetrooms": _as_int(g("assetRooms")),
                "assetbaths": _as_int(g("assetBaths")),

                "assetpool": _as_bool(g("assetPool")),
                "assetac": _as_bool(g("assetAC")),
                "asseteheating": _as_bool(g("assetEHeating")),
                "assetheating": _as_bool(g("assetHeating")),
                "assetmicrowave": _as_bool(g("assetMicrowave")),
                "assetoven": _as_bool(g("assetOven")),
                "assetwasher": _as_bool(g("assetWasher")),
                "assetdryer": _as_bool(g("assetDryer")),
                "assetrefrigerator": _as_bool(g("assetRefrigerator")),

                "watercode": str(g("waterCode")) if g("waterCode") is not None else None,
                "waterprovider": str(g("waterProvider")) if g("waterProvider") is not None else None,
                "waterserviceowner": str(g("waterServiceOwner")) if g("waterServiceOwner") is not None else None,
                "watercost": _clean_money(g("waterCost")),
                "wateraveragecost": _clean_money(g("waterAverageCost")),
                "waterconsumption": _clean_money(g("waterConsumption")),
                "watercostbyconsumption": _clean_money(g("waterCostByConsumption")),
                "watercostbym2": _clean_money(g("waterCostByM2")),

                "electricitycode": str(g("electricityCode")) if g("electricityCode") is not None else None,
                "electricityprovider": str(g("electricityProvider")) if g("electricityProvider") is not None else None,
                "electricityserviceowner": str(g("electricityServiceOwner")) if g("electricityServiceOwner") is not None else None,
                "electricitycost": _clean_money(g("electricityCost")),
                "electricityaveragecost": _clean_money(g("electricityAverageCost")),
                "electricityconsumption": _clean_money(g("electricityConsumption")),
                "electricitycostbyconsumption": _clean_money(g("electricityCostByConsumption")),
                "electricitycostbym2": _clean_money(g("electricityCostByM2")),

                "gascode": str(g("gasCode")) if g("gasCode") is not None else None,
                "gasprovider": str(g("gasProvider")) if g("gasProvider") is not None else None,
                "gasserviceowner": str(g("gasServiceOwner")) if g("gasServiceOwner") is not None else None,
                "gascost": _clean_money(g("gasCost")),
                "gasaveragecost": _clean_money(g("gasAverageCost")),
                "gasconsumption": _clean_money(g("gasConsumption")),
                "gascostbyconsumption": _clean_money(g("gasCostByConsumption")),
                "gascostbym2": _clean_money(g("gasCostByM2")),
            })

    return kpi, monthly_rows, asset_rows
