#!/usr/bin/env python3
"""
PDF Download Button Scraper
===========================

Handles clicking the download button in the PDF viewer toolbar:
1. Go to invoices page
2. Search for property
3. Look at elec bill for last 2 months and water bill
4. Look at initial date/final date columns
5. Go to first column (#) of that row
6. Click download (reference number link)
7. New tab opens with PDF
8. Click download button in PDF viewer toolbar
9. If that fails, try right-click "Save as"
"""

import sys
import os
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from datetime import datetime, timedelta

# Add src to path
sys.path.append('src')

# Global wait time - 5 seconds after each step
WAIT_MS = 5000

async def _wait(page, label: str):
    """Wait for 5 seconds with logging."""
    print(f"⏳ [WAIT] {label} … {WAIT_MS}ms")
    await page.wait_for_timeout(WAIT_MS)

def is_within_last_2_months(initial_date_str, final_date_str, service_type=None):
    """Check if the invoice date range is within the last 2 months."""
    try:
        # Parse dates (assuming DD/MM/YYYY format)
        initial_date = datetime.strptime(initial_date_str, "%d/%m/%Y")
        final_date = datetime.strptime(final_date_str, "%d/%m/%Y")
        
        # Calculate 2 months ago
        two_months_ago = datetime.now() - timedelta(days=60)  # Approximate 2 months
        
        # For electricity bills (monthly), check if final date is within last 2 months
        if service_type == "electricity":
            return final_date >= two_months_ago
        
        # For water bills (bi-monthly), we need to be more flexible
        # Water bills are bi-monthly, so we might be in the middle of a billing cycle
        # If we're in September 2025, we should look for July-August 2025 water bill
        # (the most recent completed bi-monthly cycle)
        elif service_type == "water":
            # For water bills, we need to find the bill that covers the last 2-month period
            # This might be a bill that ended more than 2 months ago but is still relevant
            # Let's look for water bills that ended within the last 4 months
            four_months_ago = datetime.now() - timedelta(days=120)
            return final_date >= four_months_ago
        
        # For unknown service types, use the standard 2-month logic
        else:
            return final_date >= two_months_ago
        
    except Exception as e:
        print(f"   ⚠️ Error parsing dates '{initial_date_str}' - '{final_date_str}': {e}")
        return False

def is_relevant_water_bill(initial_date_str, final_date_str):
    """Check if this water bill is relevant for the current 2-month billing period."""
    try:
        # Parse dates (assuming DD/MM/YYYY format)
        initial_date = datetime.strptime(initial_date_str, "%d/%m/%Y")
        final_date = datetime.strptime(final_date_str, "%d/%m/%Y")
        
        # Get current date
        now = datetime.now()
        
        # For water bills, we want the most recent completed bi-monthly cycle
        # If we're in September 2025, we want July-August 2025 water bill
        # If we're in August 2025, we want May-June 2025 water bill
        
        # Calculate the expected billing period
        # Water bills typically end on specific dates (like 25th of even months)
        # Let's look for bills that ended within the last 4 months
        four_months_ago = now - timedelta(days=120)
        
        # Also check if this bill covers a recent 2-month period
        # For example, if we're in September 2025, look for July-August 2025
        current_month = now.month
        current_year = now.year
        
        # Calculate expected billing periods
        if current_month >= 7:  # July, August, September, October, November, December
            # Look for July-August period
            expected_start = datetime(current_year, 7, 1)
            expected_end = datetime(current_year, 8, 31)
        elif current_month >= 5:  # May, June
            # Look for March-April period
            expected_start = datetime(current_year, 3, 1)
            expected_end = datetime(current_year, 4, 30)
        elif current_month >= 3:  # March, April
            # Look for January-February period
            expected_start = datetime(current_year, 1, 1)
            expected_end = datetime(current_year, 2, 28)
        else:  # January, February
            # Look for November-December of previous year
            expected_start = datetime(current_year - 1, 11, 1)
            expected_end = datetime(current_year - 1, 12, 31)
        
        # Check if this water bill overlaps with the expected period
        bill_overlaps = (initial_date <= expected_end and final_date >= expected_start)
        
        # Also check if it's within the last 4 months as a fallback
        within_last_4_months = final_date >= four_months_ago
        
        return bill_overlaps or within_last_4_months
        
    except Exception as e:
        print(f"   ⚠️ Error parsing water bill dates '{initial_date_str}' - '{final_date_str}': {e}")
        return False

async def pdf_download_button_scraper(property_name: str):
    """PDF download button scraper that clicks the download button in PDF viewer."""
    print(f"🚀 Starting PDF Download Button Scraper for: {property_name}")
    print("=" * 70)
    
    try:
        from src.config import POLAROO_EMAIL, POLAROO_PASSWORD
        
        Path("_debug").mkdir(exist_ok=True)
        Path("_debug/downloads").mkdir(parents=True, exist_ok=True)
        user_data = str(Path("./.chrome-profile").resolve())
        Path(user_data).mkdir(exist_ok=True)

        async with async_playwright() as p:
            print("🌐 [BROWSER] Launching browser...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data,
                headless=False,  # Set to False to see what's happening
                slow_mo=1000,    # Slow down for debugging
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
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ],
                accept_downloads=True,
                ignore_https_errors=True,
            )
            context.set_default_timeout(10_000)
            page = context.pages[0] if context.pages else await context.new_page()

            # Add stealth measures
            print("🥷 [STEALTH] Adding anti-detection measures...")
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)

            try:
                # 1) Login / dashboard
                print("🔐 [STEP 1/8] Starting login process...")
                await page.goto("https://app.polaroo.com/login")
                await page.wait_for_load_state("domcontentloaded")
                await _wait(page, "after navigating to login page")

                if "login" in page.url.lower():
                    print("🔐 [LOGIN] Login page detected, proceeding with authentication...")
                    await page.get_by_placeholder("Email").fill(POLAROO_EMAIL or "")
                    await _wait(page, "after filling email")
                    await page.get_by_placeholder("Password").fill(POLAROO_PASSWORD or "")
                    await _wait(page, "after filling password")
                    await page.get_by_role("button", name="Sign in").click()
                    await page.wait_for_load_state("domcontentloaded")
                    await _wait(page, "after clicking sign in")
                else:
                    print("✅ [LOGIN] Already logged in, redirected to dashboard")

                # 2) Navigate to Invoices
                print("📄 [STEP 2/8] Navigating to Invoices page...")
                await page.get_by_role("link", name="Invoices").click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await _wait(page, "after navigating to invoices page")
                print(f"✅ [INVOICES] Successfully navigated to Invoices page: {page.url}")

                # 3) Search for property
                print("🔍 [STEP 3/8] Searching for property invoices...")
                search_input = page.locator('input[placeholder*="search" i]').first
                await search_input.clear()
                await _wait(page, "after clearing search field")
                await search_input.fill(property_name)
                await _wait(page, "after filling search field")
                await search_input.press("Enter")
                await page.wait_for_load_state("networkidle")
                await _wait(page, "after pressing Enter in search field")
                print("✅ [SEARCH] Search completed")

                # 4) Analyze search results and find table
                print("📥 [STEP 4/8] Analyzing search results...")
                
                # Take a screenshot for debugging
                await page.screenshot(path="_debug/pdf_download_search_results.png")
                print("📸 [DEBUG] Screenshot saved to _debug/pdf_download_search_results.png")
                
                # Look for table
                table = page.locator('table').first
                if await table.count():
                    print("✅ [ANALYSIS] Found table")
                    
                    # Get all rows
                    rows = table.locator('tbody tr, .table-row, .invoice-row')
                    row_count = await rows.count()
                    print(f"🔍 [ANALYSIS] Found {row_count} rows in table")
                    
                    # Check headers
                    headers = table.locator('th, .table-header')
                    header_count = await headers.count()
                    print(f"🔍 [ANALYSIS] Found {header_count} headers")
                    
                    # Find column indices
                    column_indices = {}
                    for i in range(header_count):
                        header_text = await headers.nth(i).text_content()
                        if header_text:
                            header_text = header_text.lower().strip()
                            if "rence" in header_text or "#" in header_text:
                                column_indices["reference"] = i
                            elif "service" in header_text:
                                column_indices["service"] = i
                            elif "initial date" in header_text or "fecha inicial" in header_text:
                                column_indices["initial_date"] = i
                            elif "final date" in header_text or "fecha final" in header_text:
                                column_indices["final_date"] = i
                            elif "provider" in header_text:
                                column_indices["provider"] = i
                    
                    print(f"✅ [ANALYSIS] Column indices: {column_indices}")
                    
                    # Look for invoices to download
                    # Logic: 2 electricity bills (monthly) + 1 water bill (bi-monthly) = 3 invoices total
                    downloaded_files = []
                    elec_downloaded = 0
                    water_downloaded = 0
                    max_elec = 2  # 2 electricity bills for 2 months
                    max_water = 1  # 1 water bill for 2 months (bi-monthly)
                    
                    for i in range(min(15, row_count)):  # Check first 15 rows
                        row = rows.nth(i)
                        row_text = await row.text_content()
                        print(f"\n🔍 [ROW {i+1}] Analyzing row: {row_text[:150]}...")
                        
                        # Check service type
                        service_type = None
                        if "service" in column_indices:
                            service_cell = row.locator(f'td:nth-child({column_indices["service"] + 1}), .col-{column_indices["service"] + 1}')
                            if await service_cell.count():
                                service_text = await service_cell.text_content()
                                if service_text:
                                    service_text = service_text.lower().strip()
                                    if "electricity" in service_text or "elec" in service_text:
                                        service_type = "electricity"
                                    elif "water" in service_text:
                                        service_type = "water"
                                    print(f"   📋 Service type: {service_type}")
                        
                        # Check date range
                        date_relevant = False
                        if "initial_date" in column_indices and "final_date" in column_indices:
                            initial_date_cell = row.locator(f'td:nth-child({column_indices["initial_date"] + 1}), .col-{column_indices["initial_date"] + 1}')
                            final_date_cell = row.locator(f'td:nth-child({column_indices["final_date"] + 1}), .col-{column_indices["final_date"] + 1}')
                            
                            if await initial_date_cell.count() and await final_date_cell.count():
                                initial_date_text = await initial_date_cell.text_content()
                                final_date_text = await final_date_cell.text_content()
                                
                                if initial_date_text and final_date_text:
                                    initial_date_text = initial_date_text.strip()
                                    final_date_text = final_date_text.strip()
                                    print(f"   📅 Date range: {initial_date_text} to {final_date_text}")
                                    
                                    # Use different logic for water bills
                                    if service_type == "water":
                                        date_relevant = is_relevant_water_bill(initial_date_text, final_date_text)
                                        print(f"   📅 Water bill relevant (bi-monthly cycle): {date_relevant}")
                                    else:
                                        date_relevant = is_within_last_2_months(initial_date_text, final_date_text, service_type)
                                        print(f"   📅 Date relevant (last 2 months): {date_relevant}")
                        
                        # Check if we need this type of invoice
                        should_download = False
                        if date_relevant:
                            if service_type == "electricity" and elec_downloaded < max_elec:
                                should_download = True
                                elec_downloaded += 1
                                print(f"   ✅ Need electricity invoice {elec_downloaded}/{max_elec}")
                            elif service_type == "water" and water_downloaded < max_water:
                                should_download = True
                                water_downloaded += 1
                                print(f"   ✅ Need water invoice {water_downloaded}/{max_water}")
                            elif service_type is None:  # If we can't determine service type, download anyway
                                should_download = True
                                print(f"   ✅ Need unknown service invoice")
                        
                        if not should_download:
                            print(f"   ⏭️ Skipping row {i+1} (already have enough {service_type or 'unknown'} invoices or date not relevant)")
                            continue
                        
                        # Look for the first column (#) which contains asset names and cloud icons
                        first_cell = row.locator('td:first-child, .col-1')
                        if await first_cell.count():
                            # Get the text content of the first cell
                            first_cell_text = await first_cell.text_content()
                            print(f"   🔗 First cell text: '{first_cell_text}'")
                            
                            # Look for clickable elements in the first column
                            # Try different selectors for links
                            link_selectors = [
                                'a',  # Standard links
                                'button',  # Buttons
                                '[role="button"]',  # Elements with button role
                                '[onclick]',  # Elements with onclick
                                '.clickable',  # Elements with clickable class
                                'span',  # Spans that might be clickable
                                'div',  # Divs that might be clickable
                                'i',  # Icons that might be clickable
                                'svg'  # SVG icons that might be clickable
                            ]
                            
                            clickable_found = False
                            for selector in link_selectors:
                                clickable_elements = first_cell.locator(selector)
                                element_count = await clickable_elements.count()
                                
                                if element_count > 0:
                                    print(f"   ✅ Found {element_count} {selector} elements in first column")
                                    
                                    for j in range(element_count):
                                        element = clickable_elements.nth(j)
                                        element_text = await element.text_content()
                                        is_visible = await element.is_visible()
                                        is_enabled = await element.is_enabled()
                                        print(f"     Element {j+1}: '{element_text}' (visible: {is_visible}, enabled: {is_enabled})")
                                        
                                        if is_visible and is_enabled:
                                            try:
                                                print(f"     📥 Clicking element {j+1} in first column...")
                                                
                                                # Get the current number of pages before clicking
                                                pages_before = len(context.pages)
                                                print(f"     📄 Pages before click: {pages_before}")
                                                
                                                # Click the element (this should open new tab)
                                                await element.click()
                                                await _wait(page, "after clicking first column button")
                                                
                                                # Check if a new tab opened
                                                pages_after = len(context.pages)
                                                print(f"     📄 Pages after click: {pages_after}")
                                                
                                                if pages_after > pages_before:
                                                    print("     ✅ New tab opened!")
                                                    
                                                    # Switch to the new tab
                                                    new_page = context.pages[-1]  # Get the last (newest) tab
                                                    await new_page.wait_for_load_state("networkidle")
                                                    await _wait(new_page, "after new tab loads")
                                                    
                                                    # Check the URL of the new tab
                                                    new_url = new_page.url
                                                    print(f"     🌐 New tab URL: {new_url}")
                                                    
                                                    # Take screenshot of new tab
                                                    await new_page.screenshot(path=f"_debug/pdf_download_viewer_{i+1}_{j+1}.png")
                                                    print(f"     📸 [DEBUG] New tab screenshot saved to _debug/pdf_download_viewer_{i+1}_{j+1}.png")
                                                    
                                                    # Check if it's an S3-hosted PDF
                                                    if "s3.eu-west-3.amazonaws.com" in new_url and (".PDF" in new_url or ".pdf" in new_url):
                                                        print("     ✅ Detected S3-hosted PDF in new tab")
                                                        
                                                        # Try to click the download button in the PDF viewer toolbar
                                                        pdf_downloaded = False
                                                        
                                                        # PDF viewer download button selectors (more comprehensive)
                                                        pdf_download_selectors = [
                                                            # Chrome PDF viewer download button
                                                            'button[aria-label*="Download"]',
                                                            'button[title*="Download"]',
                                                            'button[aria-label*="Descargar"]',
                                                            'button[title*="Descargar"]',
                                                            'button[aria-label*="Save"]',
                                                            'button[title*="Save"]',
                                                            'button[aria-label*="Guardar"]',
                                                            'button[title*="Guardar"]',
                                                            
                                                            # Generic download buttons
                                                            'button:has-text("Download")',
                                                            'button:has-text("Descargar")',
                                                            'button:has-text("Save")',
                                                            'button:has-text("Guardar")',
                                                            
                                                            # Icon-based selectors
                                                            'button:has(svg[data-icon="download"])',
                                                            'button:has(svg[data-icon="arrow-down"])',
                                                            'button:has(.fa-download)',
                                                            'button:has(.fa-arrow-down)',
                                                            'button:has(.fa-save)',
                                                            
                                                            # PDF viewer specific
                                                            '.pdf-viewer button[title*="Download"]',
                                                            '.pdf-viewer button[aria-label*="Download"]',
                                                            '#download',
                                                            '#save',
                                                            '.download-btn',
                                                            '.btn-download',
                                                            
                                                            # Chrome PDF viewer specific selectors
                                                            'button[aria-label="Download"]',
                                                            'button[title="Download"]',
                                                            'button[aria-label="Descargar"]',
                                                            'button[title="Descargar"]',
                                                            
                                                            # Try to find any button with download-related attributes
                                                            'button[aria-label*="download" i]',
                                                            'button[title*="download" i]',
                                                            'button[aria-label*="save" i]',
                                                            'button[title*="save" i]'
                                                        ]
                                                        
                                                        print("     🔍 Looking for PDF viewer download button...")
                                                        for selector in pdf_download_selectors:
                                                            pdf_btn = new_page.locator(selector)
                                                            if await pdf_btn.count() > 0:
                                                                pdf_btn_element = pdf_btn.first
                                                                if await pdf_btn_element.is_visible() and await pdf_btn_element.is_enabled():
                                                                    print(f"     📄 Found PDF download button: {selector}")
                                                                    
                                                                    try:
                                                                        print("     📥 Clicking PDF download button...")
                                                                        async with new_page.expect_download() as dl_info:
                                                                            await pdf_btn_element.click()
                                                                        dl = await dl_info.value
                                                                        
                                                                        # Generate filename
                                                                        suggested = dl.suggested_filename or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}.pdf"
                                                                        stem = Path(suggested).stem or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}"
                                                                        ext = Path(suggested).suffix or ".pdf"
                                                                        from datetime import datetime, timezone
                                                                        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                                                                        filename = f"{stem}_{ts}{ext}"
                                                                        
                                                                        # Save locally
                                                                        local_path = Path("_debug/downloads") / filename
                                                                        await dl.save_as(str(local_path))
                                                                        size = local_path.stat().st_size if local_path.exists() else 0
                                                                        print(f"     💾 Downloaded: {local_path} ({size} bytes)")
                                                                        
                                                                        downloaded_files.append(str(local_path))
                                                                        pdf_downloaded = True
                                                                        await _wait(new_page, "after downloading PDF")
                                                                        break
                                                                        
                                                                    except Exception as e:
                                                                        print(f"     ❌ Failed to download PDF: {e}")
                                                                        continue
                                                        
                                                        # If download button click failed, try right-click "Save as"
                                                        if not pdf_downloaded:
                                                            print("     🔍 Download button click failed, trying right-click 'Save as'...")
                                                            try:
                                                                # Right-click on the PDF content area
                                                                await new_page.click('body', button='right')
                                                                await _wait(new_page, "after right-click")
                                                                
                                                                # Look for "Save as" option in context menu
                                                                save_as_selectors = [
                                                                    'text="Save as"',
                                                                    'text="Guardar como"',
                                                                    'text="Save"',
                                                                    'text="Guardar"',
                                                                    '[role="menuitem"]:has-text("Save as")',
                                                                    '[role="menuitem"]:has-text("Guardar como")',
                                                                    '[role="menuitem"]:has-text("Save")',
                                                                    '[role="menuitem"]:has-text("Guardar")'
                                                                ]
                                                                
                                                                for selector in save_as_selectors:
                                                                    save_as_btn = new_page.locator(selector)
                                                                    if await save_as_btn.count() > 0:
                                                                        save_as_element = save_as_btn.first
                                                                        if await save_as_element.is_visible():
                                                                            print(f"     📄 Found 'Save as' option: {selector}")
                                                                            
                                                                            try:
                                                                                async with new_page.expect_download() as dl_info:
                                                                                    await save_as_element.click()
                                                                                dl = await dl_info.value
                                                                                
                                                                                # Generate filename
                                                                                suggested = dl.suggested_filename or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}.pdf"
                                                                                stem = Path(suggested).stem or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}"
                                                                                ext = Path(suggested).suffix or ".pdf"
                                                                                from datetime import datetime, timezone
                                                                                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                                                                                filename = f"{stem}_{ts}{ext}"
                                                                                
                                                                                # Save locally
                                                                                local_path = Path("_debug/downloads") / filename
                                                                                await dl.save_as(str(local_path))
                                                                                size = local_path.stat().st_size if local_path.exists() else 0
                                                                                print(f"     💾 Downloaded via right-click: {local_path} ({size} bytes)")
                                                                                
                                                                                downloaded_files.append(str(local_path))
                                                                                pdf_downloaded = True
                                                                                await _wait(new_page, "after downloading PDF")
                                                                                break
                                                                                
                                                                            except Exception as e:
                                                                                print(f"     ❌ Failed to download via right-click: {e}")
                                                                                continue
                                                                
                                                                if not pdf_downloaded:
                                                                    print("     ⚠️ No 'Save as' option found in context menu")
                                                                    
                                                            except Exception as e:
                                                                print(f"     ❌ Right-click failed: {e}")
                                                        
                                                        # If all else fails, try Ctrl+S (Save As) fallback
                                                        if not pdf_downloaded:
                                                            print("     📥 All download methods failed, trying Ctrl+S (Save As) fallback...")
                                                            try:
                                                                # Press Ctrl+S to open Save As dialog
                                                                await new_page.keyboard.press('Control+s')
                                                                await _wait(new_page, "after pressing Ctrl+S")
                                                                
                                                                # Wait for download to start
                                                                try:
                                                                    async with new_page.expect_download() as dl_info:
                                                                        # Wait a bit for the download to start
                                                                        await new_page.wait_for_timeout(2000)
                                                                    dl = await dl_info.value
                                                                    
                                                                    # Generate filename
                                                                    suggested = dl.suggested_filename or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}.pdf"
                                                                    stem = Path(suggested).stem or f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}"
                                                                    ext = Path(suggested).suffix or ".pdf"
                                                                    from datetime import datetime, timezone
                                                                    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                                                                    filename = f"{stem}_{ts}{ext}"
                                                                    
                                                                    # Save locally
                                                                    local_path = Path("_debug/downloads") / filename
                                                                    await dl.save_as(str(local_path))
                                                                    size = local_path.stat().st_size if local_path.exists() else 0
                                                                    print(f"     💾 Downloaded via Ctrl+S: {local_path} ({size} bytes)")
                                                                    
                                                                    downloaded_files.append(str(local_path))
                                                                    pdf_downloaded = True
                                                                    
                                                                except Exception as e:
                                                                    print(f"     ❌ Ctrl+S download failed: {e}")
                                                                    
                                                            except Exception as e:
                                                                print(f"     ❌ Ctrl+S failed: {e}")
                                                        
                                                        # If all else fails, try direct download using requests
                                                        if not pdf_downloaded:
                                                            print("     📥 All download methods failed, trying direct download via requests...")
                                                            try:
                                                                import requests
                                                                
                                                                response = requests.get(new_url)
                                                                if response.status_code == 200:
                                                                    # Generate filename
                                                                    from datetime import datetime, timezone
                                                                    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                                                                    filename = f"invoice_{property_name}_{service_type or 'unknown'}_{i+1}_{j+1}_{ts}.pdf"
                                                                    
                                                                    # Save locally
                                                                    local_path = Path("_debug/downloads") / filename
                                                                    with open(local_path, 'wb') as f:
                                                                        f.write(response.content)
                                                                    
                                                                    size = local_path.stat().st_size if local_path.exists() else 0
                                                                    print(f"     💾 Downloaded via requests: {local_path} ({size} bytes)")
                                                                    
                                                                    downloaded_files.append(str(local_path))
                                                                    pdf_downloaded = True
                                                                    
                                                            except Exception as e:
                                                                print(f"     ❌ Requests download failed: {e}")
                                                        
                                                        if not pdf_downloaded:
                                                            print("     ⚠️ All download methods failed")
                                                    
                                                    else:
                                                        print(f"     ⚠️ Not an S3-hosted PDF, current URL: {new_url}")
                                                    
                                                    # Close the new tab
                                                    await new_page.close()
                                                    print("     🔚 Closed new tab")
                                                    
                                                else:
                                                    print("     ⚠️ No new tab opened")
                                                
                                                if downloaded_files:
                                                    clickable_found = True
                                                    break  # Successfully downloaded, move to next row
                                                    
                                            except Exception as e:
                                                print(f"     ❌ Failed to click element {j+1}: {e}")
                                    
                                    if clickable_found:
                                        break  # Found clickable element, move to next row
                            
                            if not clickable_found:
                                print(f"   ⚠️ No clickable elements found in first column")
                        
                        if not downloaded_files:
                            print(f"   ⚠️ No download buttons found in row {i+1}")
                    
                    print(f"\n📊 [SUMMARY] Downloaded {len(downloaded_files)} files total")
                    print(f"   - Electricity: {elec_downloaded}/{max_elec} (monthly bills)")
                    print(f"   - Water: {water_downloaded}/{max_water} (bi-monthly bill)")
                    print(f"   - Total for 2-month billing period: {len(downloaded_files)}/3 invoices")
                    
                else:
                    print("❌ [ANALYSIS] No table found")

                # 5) Upload to PDF storage
                print("☁️ [STEP 5/8] Uploading to PDF storage...")
                if downloaded_files:
                    from src.pdf_storage import pdf_storage
                    
                    for i, file_path in enumerate(downloaded_files, 1):
                        try:
                            # Read the file
                            with open(file_path, 'rb') as f:
                                pdf_content = f.read()
                            
                            # Generate object key
                            filename = Path(file_path).name
                            object_key = f"invoices/{property_name.replace(' ', '_').replace('º', '').replace('ª', '')}/{filename}"
                            
                            # Upload to Supabase
                            result = pdf_storage.upload_pdf(
                                file_data=pdf_content,
                                filename=filename,
                                property_name=property_name,
                                invoice_type=service_type or "unknown"
                            )
                            
                            if result.get("success"):
                                print(f"✅ Uploaded {i}/{len(downloaded_files)}: {filename}")
                                print(f"   Storage: {object_key}")
                                print(f"   URL: {result.get('public_url')}")
                            else:
                                print(f"❌ Failed to upload {filename}: {result.get('error')}")
                                
                        except Exception as e:
                            print(f"❌ Error uploading {filename}: {e}")
                else:
                    print("⚠️ No files to upload")

                # 6) Final wait
                print("⏳ [STEP 6/8] Final wait...")
                await _wait(page, "final wait before closing")

                # Wait for user to see the results
                print("\n⏳ [COMPLETE] Waiting 15 seconds before closing...")
                await page.wait_for_timeout(15000)
                
            except Exception as e:
                print(f"❌ [ERROR] Scraper failed: {e}")
                await page.screenshot(path="_debug/pdf_download_error_screenshot.png")
                print("📸 [DEBUG] Error screenshot saved to _debug/pdf_download_error_screenshot.png")
                raise
            finally:
                await context.close()
                print("🔚 [CLEANUP] Browser closed")
                
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run PDF download button scraper."""
    print("🚀 Starting PDF Download Button Scraper")
    print("=" * 60)
    print("This will open a browser window and download invoices")
    print("with 5-second delays after each step")
    print("Handles PDF download button clicking:")
    print("1. Go to invoices page")
    print("2. Search for property")
    print("3. Look at elec bill for last 2 months and water bill")
    print("4. Look at initial date/final date columns")
    print("5. Go to first column (#) of that row")
    print("6. Click download (reference number link)")
    print("7. New tab opens with PDF")
    print("8. Click download button in PDF viewer toolbar")
    print("9. If that fails, try right-click 'Save as'")
    print("10. Target: 2 electricity bills (monthly) + 1 water bill (bi-monthly) = 3 invoices total")
    print()
    
    # Test with a property that has overages
    test_property = "Aribau 1º 1ª"
    
    asyncio.run(pdf_download_button_scraper(test_property))

if __name__ == "__main__":
    main()
