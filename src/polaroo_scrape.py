import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from src.config import (
    POLAROO_EMAIL,
    POLAROO_PASSWORD,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    STORAGE_BUCKET,
)

LOGIN_URL = "https://app.polaroo.com/login"

# ---------- global waits ----------
WAIT_MS = 5_000          # minimum wait after each step
MAX_WAIT_LOOPS = 20       # 20 * 500ms = 30s for dashboard detection

# ---------- utils ----------
def _infer_content_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".csv"):
        return "text/csv"
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"

def _upload_to_supabase_bytes(filename: str, data: bytes) -> str:
    """
    Uploads `data` to Supabase Storage using REST.
    Returns the path key stored in the bucket.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not STORAGE_BUCKET:
        raise RuntimeError("Supabase env config missing: SUPABASE_URL / SUPABASE_SERVICE_KEY / STORAGE_BUCKET")

    # namespacing by month keeps things tidy
    month_slug = datetime.now(timezone.utc).strftime("%Y-%m")
    object_key = f"polaroo/raw/{month_slug}/{filename}"

    url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/{quote(STORAGE_BUCKET)}/{quote(object_key)}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": _infer_content_type(filename),
        "x-upsert": "true",
    }
    resp = requests.post(url, headers=headers, data=data, timeout=60)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Supabase upload failed [{resp.status_code}]: {resp.text}")

    return object_key

async def _wait(page, label: str):
    print(f"[wait] {label} … {WAIT_MS}ms")
    await page.wait_for_timeout(WAIT_MS)

# ---------- helpers ----------
async def _wait_for_dashboard(page) -> None:
    """Wait until we are on any /dashboard page and the sidebar/nav is present."""
    for _ in range(MAX_WAIT_LOOPS):  # up to ~30s
        url = page.url
        has_sidebar = await page.locator("nav, [role='navigation']").count() > 0
        if "/dashboard" in url and has_sidebar:
            await page.wait_for_load_state("networkidle")
            return
        await page.wait_for_timeout(500)
    raise PWTimeout("Did not reach a dashboard page with sidebar after sign-in.")

async def _ensure_logged_in(page) -> None:
    """Start at /login. If already authenticated, Polaroo will redirect to dashboard. If not, login and let it redirect."""
    await page.goto(LOGIN_URL)
    await page.wait_for_load_state("domcontentloaded")
    await _wait(page, "after goto /login")

    if "login" in page.url.lower():
        await page.get_by_role("heading", name="Sign in").wait_for(timeout=60_000)
        await page.get_by_placeholder("Email").fill(POLAROO_EMAIL or "")
        await page.get_by_placeholder("Password").fill(POLAROO_PASSWORD or "")
        await _wait(page, "after filling credentials")
        await page.get_by_role("button", name="Sign in").click()
        await page.wait_for_load_state("domcontentloaded")

    await _wait_for_dashboard(page)
    await _wait(page, "post-login dashboard settle")

async def _open_report_from_sidebar(page) -> None:
    """Click the 'Report' item in the left sidebar to open the Report page."""
    candidates = [
        page.get_by_role("link", name="Report"),
        page.get_by_role("link", name=re.compile(r"\bReport\b", re.I)),
        page.locator('a:has-text("Report")'),
        page.locator('[role="navigation"] >> text=Report'),
        page.locator('nav >> text=Report'),
    ]
    for loc in candidates:
        if await loc.count():
            btn = loc.first
            if await btn.is_visible():
                await btn.scroll_into_view_if_needed()
                await _wait(page, "before clicking sidebar → Report")
                await btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await _wait(page, "after landing on Report")
                return
    raise PWTimeout("Could not click 'Report' in the sidebar.")

async def _set_date_range_last_month(page) -> None:
    """Open the date-range picker and select 'Last month' (robust for ng-select)."""
    container = page.locator(".ng-select .ng-select-container").filter(
        has_text=re.compile(r"last\s+\d+\s*month(s)?|last\s+month", re.I)
    ).first

    if await container.count() == 0:
        chip = page.get_by_text(re.compile(r"^last\s+\d+\s*month(s)?$|^last\s+month$", re.I)).first
        if await chip.count():
            container = chip.locator(
                'xpath=ancestor-or-self::*[contains(@class,"ng-select")][1]//div[contains(@class,"ng-select-container")]'
            ).first

    if await container.count() == 0:
        raise PWTimeout("Date-range selector not found (no ng-select container with 'Last … month').")

    await container.scroll_into_view_if_needed()
    await _wait(page, "before opening date-range menu")

    def listbox_open():
        return page.locator('[role="listbox"], .ng-dropdown-panel').first

    opened = False
    try:
        await container.click()
        await page.wait_for_timeout(600)
        opened = await listbox_open().count() > 0
    except Exception:
        opened = False

    if not opened:
        arrow = container.locator(".ng-arrow-wrapper, .ng-arrow").first
        if await arrow.count():
            await arrow.click()
            await page.wait_for_timeout(600)
            opened = await listbox_open().count() > 0

    if not opened:
        await container.focus()
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(600)
        opened = await listbox_open().count() > 0

    if not opened:
        box = await container.bounding_box()
        if box:
            await page.mouse.click(box["x"] + box["width"] - 8, box["y"] + box["height"] / 2)
            await page.wait_for_timeout(600)
            opened = await listbox_open().count() > 0

    if not opened:
        raise PWTimeout("Could not open the date-range dropdown.")

    await _wait(page, "after opening date-range menu")

    option = page.locator(
        '.ng-dropdown-panel .ng-option',
        has_text=re.compile(r"^\s*last\s+month(s)?\s*$", re.I),
    ).first
    if not await option.count():
        option = page.get_by_text(re.compile(r"^\s*last\s+month(s)?\s*$", re.I)).first

    await option.wait_for(timeout=60_000)
    await _wait(page, "before selecting 'Last month'")
    await option.click()
    await page.wait_for_load_state("networkidle")
    await _wait(page, "after selecting 'Last month'")

async def _open_download_menu(page) -> None:
    """Click the visible 'Download' control."""
    await page.evaluate("window.scrollTo(0, 0)")
    btns = page.get_by_text("Download", exact=True)
    if not await btns.count():
        btns = page.locator(r'text=/\bdownload\b/i')
    cnt = await btns.count()
    if cnt == 0:
        raise PWTimeout("No element with visible text matching 'Download' found.")
    for i in range(cnt):
        el = btns.nth(i)
        if await el.is_visible():
            await el.scroll_into_view_if_needed()
            await _wait(page, "before opening Download menu")
            await el.click()
            await page.wait_for_timeout(500)
            await _wait(page, "after opening Download menu")
            return
    raise PWTimeout("Found 'Download' elements, but none were visible/clickable.")

async def _pick_download_excel(page):
    """Return a locator for 'Download Excel'; fallback to 'Download CSV'."""
    await page.wait_for_timeout(200)
    # Prioritize Excel format
    excel = page.get_by_text("Download Excel", exact=True)
    if await excel.count():
        return excel.first
    
    # Try other Excel variations
    for label in ["Download XLSX", "Download XLS", "Descargar Excel", "Descargar XLSX"]:
        loc = page.get_by_text(label, exact=True)
        if await loc.count():
            return loc.first
    
    # Fallback to CSV if Excel not available
    csv = page.get_by_text("Download CSV", exact=True)
    if await csv.count():
        return csv.first
    
    for label in ["Descargar CSV"]:
        loc = page.get_by_text(label, exact=True)
        if await loc.count():
            return loc.first
    
    raise PWTimeout("Dropdown did not contain 'Download Excel' or 'Download CSV'.")

# ---------- main flow ----------
async def download_report_bytes() -> tuple[bytes, str]:
    """
    Headful + persistent Chrome profile with deliberate waits:
      /login → dashboard → sidebar 'Report' → set 'Last month' → Download → Excel
      → save locally (timestamped) → upload to Supabase Storage.
    """
    Path("_debug").mkdir(exist_ok=True)
    Path("_debug/downloads").mkdir(parents=True, exist_ok=True)
    user_data = str(Path("./.chrome-profile").resolve())
    Path(user_data).mkdir(exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data,
            channel="chrome",
            headless=False,  # popup so you can watch it
            slow_mo=0,       # no manual Resume needed
            viewport={"width": 1366, "height": 900},
            args=["--disable-gpu", "--no-sandbox", "--disable-blink-features=AutomationControlled"],
            accept_downloads=True,
        )
        context.set_default_timeout(120_000)
        page = context.pages[0] if context.pages else await context.new_page()

        # Safe debug listeners
        page.on("console",       lambda m: print("BROWSER:", m.type, m.text))
        page.on("requestfailed", lambda r: print("REQ-FAILED:", r.url, r.failure or ""))
        page.on("response",      lambda r: print("HTTP", r.status, r.url) if r.status >= 400 else None)

        # 1) Login / dashboard
        await _ensure_logged_in(page)

        # 2) Open Report
        await _open_report_from_sidebar(page)

        # 3) Set Last month
        await _set_date_range_last_month(page)

        # 4) Download → Excel (preferred) or CSV
        await _open_download_menu(page)
        item = await _pick_download_excel(page)

        await _wait(page, "before clicking Download item")
        async with page.expect_download() as dl_info:
            await item.click()
        dl = await dl_info.value

        # --- timestamped filename (UTC) ---
        suggested = dl.suggested_filename or "polaroo_report.xlsx"
        stem = Path(suggested).stem or "polaroo_report"
        ext = Path(suggested).suffix or ".xlsx"
        ts  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{stem}_{ts}{ext}"

        # Save locally for debugging/inspection
        local_path = Path("_debug/downloads") / filename
        await dl.save_as(str(local_path))
        size = local_path.stat().st_size if local_path.exists() else 0
        print(f"[saved] {local_path} ({size} bytes)")

        # Read bytes for upload
        data = local_path.read_bytes()

        # Upload to Supabase Storage (same timestamped name)
        key = _upload_to_supabase_bytes(filename, data)
        print(f"[supabase] uploaded to: {STORAGE_BUCKET}/{key}")

        await _wait(page, "after download+upload")
        await context.close()
        return data, filename


def download_report_sync() -> tuple[bytes, str]:
    """Synchronous wrapper for download_report_bytes that works with FastAPI."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in a running loop, we need to run in a thread with a new event loop
            import concurrent.futures
            import threading
            
            def run_in_thread():
                # Create a new event loop in this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(download_report_bytes())
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            # No running loop, safe to use asyncio.run
            return asyncio.run(download_report_bytes())
    except RuntimeError:
        # Fallback to asyncio.run
        return asyncio.run(download_report_bytes())
