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
    print(f"⏳ [WAIT] {label} … {WAIT_MS}ms")
    await page.wait_for_timeout(WAIT_MS)

# ---------- helpers ----------
async def _wait_for_dashboard(page) -> None:
    """Wait until we are on any /dashboard page and the sidebar/nav is present."""
    print("🔍 [DASHBOARD] Waiting for dashboard page to load...")
    for i in range(MAX_WAIT_LOOPS):  # up to ~30s
        url = page.url
        has_sidebar = await page.locator("nav, [role='navigation']").count() > 0
        print(f"🔍 [DASHBOARD] Attempt {i+1}/{MAX_WAIT_LOOPS}: URL={url}, Has sidebar={has_sidebar}")
        if "/dashboard" in url and has_sidebar:
            print("✅ [DASHBOARD] Dashboard detected! Waiting for network idle...")
            await page.wait_for_load_state("networkidle")
            print("✅ [DASHBOARD] Dashboard fully loaded!")
            return
        await page.wait_for_timeout(500)
    raise PWTimeout("Did not reach a dashboard page with sidebar after sign-in.")

async def _ensure_logged_in(page) -> None:
    """Start at /login. If already authenticated, Polaroo will redirect to dashboard. If not, login and let it redirect."""
    print("🚀 [LOGIN] Starting login process...")
    
    # Add a small delay to make it look more human-like
    await page.wait_for_timeout(2000)
    
    await page.goto(LOGIN_URL)
    print(f"🌐 [LOGIN] Navigated to: {page.url}")
    await page.wait_for_load_state("domcontentloaded")
    await _wait(page, "after goto /login")

    if "login" in page.url.lower():
        print("🔐 [LOGIN] Login page detected, proceeding with authentication...")
        try:
            print("🔍 [LOGIN] Waiting for 'Sign in' heading...")
            await page.get_by_role("heading", name="Sign in").wait_for(timeout=30_000)  # Reduced from 60s to 30s
            print("✅ [LOGIN] 'Sign in' heading found!")
            
            print("📧 [LOGIN] Filling email...")
            await page.get_by_placeholder("Email").fill(POLAROO_EMAIL or "")
            print("🔑 [LOGIN] Filling password...")
            await page.get_by_placeholder("Password").fill(POLAROO_PASSWORD or "")
            await _wait(page, "after filling credentials")
            
            print("🖱️ [LOGIN] Clicking Sign in button...")
            await page.get_by_role("button", name="Sign in").click()
            await page.wait_for_load_state("domcontentloaded")
            print("✅ [LOGIN] Sign in button clicked, waiting for redirect...")
        except PWTimeout as e:
            print(f"❌ [LOGIN] Timeout waiting for login elements: {e}")
            # Take a screenshot for debugging
            await page.screenshot(path="_debug/login_timeout.png")
            print("📸 [LOGIN] Screenshot saved to _debug/login_timeout.png")
            raise
    else:
        print("✅ [LOGIN] Already logged in, redirected to dashboard")

    await _wait_for_dashboard(page)
    print("⏳ [WAIT] post-login dashboard settle … 10000ms")
    await page.wait_for_timeout(10_000)

async def _open_report_from_sidebar(page) -> None:
    """Click the 'Report' item in the left sidebar to open the Report page."""
    print("📊 [REPORT] Looking for Report link in sidebar...")
    candidates = [
        page.get_by_role("link", name="Report"),
        page.get_by_role("link", name=re.compile(r"\bReport\b", re.I)),
        page.locator('a:has-text("Report")'),
        page.locator('[role="navigation"] >> text=Report'),
        page.locator('nav >> text=Report'),
    ]
    for i, loc in enumerate(candidates):
        count = await loc.count()
        print(f"🔍 [REPORT] Candidate {i+1}: Found {count} elements")
        if count:
            btn = loc.first
            if await btn.is_visible():
                print("✅ [REPORT] Found visible Report link, clicking...")
                await btn.scroll_into_view_if_needed()
                await _wait(page, "before clicking sidebar → Report")
                await btn.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await _wait(page, "after landing on Report")
                print(f"✅ [REPORT] Successfully navigated to Report page: {page.url}")
                return
    raise PWTimeout("Could not click 'Report' in the sidebar.")

async def _set_date_range_last_month(page) -> None:
    """Open the date-range picker and select 'Last month' (robust for ng-select)."""
    print("📅 [DATE] Looking for date range selector...")
    container = page.locator(".ng-select .ng-select-container").filter(
        has_text=re.compile(r"last\s+\d+\s*month(s)?|last\s+month", re.I)
    ).first

    if await container.count() == 0:
        print("🔍 [DATE] Trying alternative selector...")
        chip = page.get_by_text(re.compile(r"^last\s+\d+\s*month(s)?$|^last\s+month$", re.I)).first
        if await chip.count():
            container = chip.locator(
                'xpath=ancestor-or-self::*[contains(@class,"ng-select")][1]//div[contains(@class,"ng-select-container")]'
            ).first

    if await container.count() == 0:
        raise PWTimeout("Date-range selector not found (no ng-select container with 'Last … month').")

    print("✅ [DATE] Found date range selector, opening dropdown...")
    await container.scroll_into_view_if_needed()
    await _wait(page, "before opening date-range menu")

    def listbox_open():
        return page.locator('[role="listbox"], .ng-dropdown-panel').first

    opened = False
    try:
        await container.click()
        await page.wait_for_timeout(600)
        opened = await listbox_open().count() > 0
        print(f"🔍 [DATE] Click attempt 1: Dropdown opened = {opened}")
    except Exception as e:
        print(f"⚠️ [DATE] Click attempt 1 failed: {e}")
        opened = False

    if not opened:
        arrow = container.locator(".ng-arrow-wrapper, .ng-arrow").first
        if await arrow.count():
            await arrow.click()
            await page.wait_for_timeout(600)
            opened = await listbox_open().count() > 0
            print(f"🔍 [DATE] Click attempt 2 (arrow): Dropdown opened = {opened}")

    if not opened:
        await container.focus()
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(600)
        opened = await listbox_open().count() > 0
        print(f"🔍 [DATE] Click attempt 3 (Enter): Dropdown opened = {opened}")

    if not opened:
        box = await container.bounding_box()
        if box:
            await page.mouse.click(box["x"] + box["width"] - 8, box["y"] + box["height"] / 2)
            await page.wait_for_timeout(600)
            opened = await listbox_open().count() > 0
            print(f"🔍 [DATE] Click attempt 4 (mouse): Dropdown opened = {opened}")

    if not opened:
        raise PWTimeout("Could not open the date-range dropdown.")

    print("✅ [DATE] Date range dropdown opened successfully!")
    await _wait(page, "after opening date-range menu")

    print("🔍 [DATE] Looking for 'Last month' option...")
    option = page.locator(
        '.ng-dropdown-panel .ng-option',
        has_text=re.compile(r"^\s*last\s+month(s)?\s*$", re.I),
    ).first
    if not await option.count():
        option = page.get_by_text(re.compile(r"^\s*last\s+month(s)?\s*$", re.I)).first

    await option.wait_for(timeout=30_000)  # Reduced from 60s to 30s
    await _wait(page, "before selecting 'Last month'")
    await option.click()
    await page.wait_for_load_state("networkidle")
    await _wait(page, "after selecting 'Last month'")
    print("✅ [DATE] Successfully selected 'Last month'!")

async def _open_download_menu(page) -> None:
    """Click the visible 'Download' control."""
    print("📥 [DOWNLOAD] Looking for Download button...")
    await page.evaluate("window.scrollTo(0, 0)")
    btns = page.get_by_text("Download", exact=True)
    if not await btns.count():
        print("🔍 [DOWNLOAD] Trying case-insensitive search...")
        btns = page.locator(r'text=/\bdownload\b/i')
    cnt = await btns.count()
    print(f"🔍 [DOWNLOAD] Found {cnt} Download elements")
    if cnt == 0:
        raise PWTimeout("No element with visible text matching 'Download' found.")
    for i in range(cnt):
        el = btns.nth(i)
        if await el.is_visible():
            print(f"✅ [DOWNLOAD] Found visible Download button #{i+1}, clicking...")
            await el.scroll_into_view_if_needed()
            await _wait(page, "before opening Download menu")
            await el.click()
            await page.wait_for_timeout(500)
            await _wait(page, "after opening Download menu")
            print("✅ [DOWNLOAD] Download menu opened successfully!")
            return
    raise PWTimeout("Found 'Download' elements, but none were visible/clickable.")

async def _pick_download_excel(page):
    """Return a locator for 'Download Excel'; fallback to 'Download CSV'."""
    print("📊 [FORMAT] Looking for download format options...")
    await page.wait_for_timeout(200)
    # Prioritize Excel format
    excel = page.get_by_text("Download Excel", exact=True)
    if await excel.count():
        print("✅ [FORMAT] Found 'Download Excel' option!")
        return excel.first
    
    # Try other Excel variations
    excel_labels = ["Download XLSX", "Download XLS", "Descargar Excel", "Descargar XLSX"]
    for label in excel_labels:
        loc = page.get_by_text(label, exact=True)
        if await loc.count():
            print(f"✅ [FORMAT] Found '{label}' option!")
            return loc.first
    
    print("⚠️ [FORMAT] Excel format not found, trying CSV...")
    # Fallback to CSV if Excel not available
    csv = page.get_by_text("Download CSV", exact=True)
    if await csv.count():
        print("✅ [FORMAT] Found 'Download CSV' option!")
        return csv.first
    
    csv_labels = ["Descargar CSV"]
    for label in csv_labels:
        loc = page.get_by_text(label, exact=True)
        if await loc.count():
            print(f"✅ [FORMAT] Found '{label}' option!")
            return loc.first
    
    raise PWTimeout("Dropdown did not contain 'Download Excel' or 'Download CSV'.")

# ---------- main flow ----------
async def download_report_bytes() -> tuple[bytes, str]:
    """
    Headful + persistent Chrome profile with deliberate waits:
      /login → dashboard → sidebar 'Report' → set 'Last month' → Download → Excel
      → save locally (timestamped) → upload to Supabase Storage.
    """
    print("🚀 [START] Starting Polaroo report download process...")
    Path("_debug").mkdir(exist_ok=True)
    Path("_debug/downloads").mkdir(parents=True, exist_ok=True)
    user_data = str(Path("./.chrome-profile").resolve())
    Path(user_data).mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("🌐 [BROWSER] Launching browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data,
            headless=True,  # headless for production
            slow_mo=0,       # no manual Resume needed
            viewport={"width": 1366, "height": 900},
            args=[
                "--disable-gpu",
                "--no-sandbox", 
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "--disable-blink-features=AutomationControlled",
                "--exclude-switches=enable-automation",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ],
            accept_downloads=True,
            ignore_https_errors=True,
        )
        context.set_default_timeout(120_000)
        page = context.pages[0] if context.pages else await context.new_page()

        # Add stealth measures to bypass Cloudflare
        print("🥷 [STEALTH] Adding anti-detection measures...")
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # Safe debug listeners
        page.on("console",       lambda m: print("🌐 [BROWSER]", m.type, m.text))
        page.on("requestfailed", lambda r: print("❌ [BROWSER] REQ-FAILED:", r.url, r.failure or ""))
        page.on("response",      lambda r: print("📡 [BROWSER] HTTP", r.status, r.url) if r.status >= 400 else None)

        try:
            # 1) Login / dashboard
            print("🔐 [STEP 1/4] Starting login process...")
            try:
                await _ensure_logged_in(page)
            except Exception as e:
                if "403" in str(e) or "401" in str(e) or "cloudflare" in str(e).lower():
                    print("🛡️ [CLOUDFLARE] Detected Cloudflare protection, trying alternative approach...")
                    # Try with different user agent and settings
                    await page.set_extra_http_headers({
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                    })
                    await page.wait_for_timeout(5000)  # Wait longer
                    await _ensure_logged_in(page)
                else:
                    raise

            # 2) Open Report
            print("📊 [STEP 2/4] Opening Report page...")
            await _open_report_from_sidebar(page)

            # 3) Set Last month
            print("📅 [STEP 3/4] Setting date range to Last month...")
            await _set_date_range_last_month(page)

            # 4) Download → Excel (preferred) or CSV
            print("📥 [STEP 4/4] Starting download process...")
            await _open_download_menu(page)
            item = await _pick_download_excel(page)

            print("💾 [DOWNLOAD] Initiating file download...")
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
            print(f"💾 [SAVED] {local_path} ({size} bytes)")

            # Read bytes for upload
            data = local_path.read_bytes()

            # Upload to Supabase Storage (same timestamped name)
            print("☁️ [UPLOAD] Uploading to Supabase...")
            key = _upload_to_supabase_bytes(filename, data)
            print(f"☁️ [UPLOAD] Successfully uploaded to: {STORAGE_BUCKET}/{key}")

            await _wait(page, "after download+upload")
            print("✅ [SUCCESS] Report download and upload completed successfully!")
            
        except Exception as e:
            print(f"❌ [ERROR] Scraping failed: {e}")
            # Take a screenshot for debugging
            await page.screenshot(path="_debug/error_screenshot.png")
            print("📸 [DEBUG] Error screenshot saved to _debug/error_screenshot.png")
            raise
        finally:
            await context.close()
            print("🔚 [CLEANUP] Browser closed")
            
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
