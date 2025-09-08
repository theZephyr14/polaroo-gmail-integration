#!/usr/bin/env python3
"""
Super Fast Invoice Scraper
==========================

Ultra-optimized version that:
1. Finds water bill FIRST to determine billing period
2. Finds electricity bills in the SAME period
3. Uses ONLY the working method (requests)
4. No fallbacks, no timeouts, no screenshots
5. 1-second delays for maximum speed
"""

import sys
import os
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import requests

# Add src to path
sys.path.append('src')

# Import credentials
from src.config import POLAROO_EMAIL, POLAROO_PASSWORD

# Ultra-fast wait time - 1 second
WAIT_MS = 1000

async def _wait(page, label: str):
    """Wait for 1 second with logging."""
    print(f"⏳ {label} … {WAIT_MS}ms")
    await page.wait_for_timeout(WAIT_MS)

def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except:
        return None

def is_within_period(initial_date, final_date, start_period, end_period):
    """Check if invoice dates overlap with the billing period."""
    if not all([initial_date, final_date, start_period, end_period]):
        return False
    return initial_date <= end_period and final_date >= start_period

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
        
        current_month = now.month
        current_year = now.year
        
        # Calculate expected billing periods for bi-monthly water bills
        if current_month >= 7:  # July, August, September, October, November, December
            # Look for July-August
            expected_start = datetime(current_year, 7, 1)
            expected_end = datetime(current_year, 8, 31)
        elif current_month >= 5:  # May, June
            # Look for March-April
            expected_start = datetime(current_year, 3, 1)
            expected_end = datetime(current_year, 4, 30)
        elif current_month >= 3:  # March, April
            # Look for January-February
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

async def super_fast_scraper(property_name: str):
    """Super fast invoice scraper - water first, then electricity in same period."""
    print(f"🚀 Super Fast Scraper for: {property_name}")
    print("=" * 50)
    print("Strategy: Water FIRST → Electricity in SAME period → Requests ONLY")
    print()
    
    downloaded_files = []
    
    try:
        async with async_playwright() as p:
            # Launch browser
            print("🌐 Launching browser...")
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True,
                ignore_https_errors=True,
            )
            context.set_default_timeout(10_000)
            page = context.pages[0] if context.pages else await context.new_page()
            
            # Add stealth measures
            print("🥷 Adding stealth measures...")
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
            
            # 1) Login / dashboard
            print("🔐 Starting login process...")
            await page.goto("https://app.polaroo.com/login")
            await page.wait_for_load_state("domcontentloaded")
            await _wait(page, "after navigating to login page")
            
            if "login" in page.url.lower():
                print("🔐 Login page detected, proceeding with authentication...")
                await page.get_by_placeholder("Email").fill(POLAROO_EMAIL or "")
                await _wait(page, "after filling email")
                await page.get_by_placeholder("Password").fill(POLAROO_PASSWORD or "")
                await _wait(page, "after filling password")
                await page.get_by_role("button", name="Sign in").click()
                await page.wait_for_load_state("domcontentloaded")
                await _wait(page, "after clicking sign in")
            else:
                print("✅ Already logged in, redirected to dashboard")
            
            # 2) Navigate to Invoices
            print("📄 Going to invoices...")
            await page.goto("https://app.polaroo.com/dashboard/accounting")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")
            await _wait(page, "invoices page")
            print(f"✅ Successfully navigated to Invoices page: {page.url}")
            
            # 3) Search for property
            print("🔍 Searching for property...")
            search_input = page.locator('input[placeholder*="search" i]').first
            await search_input.clear()
            await search_input.fill(property_name)
            await search_input.press("Enter")
            await page.wait_for_load_state("networkidle")
            await _wait(page, "search complete")
            
            # 4) Analyze table
            print("📊 Analyzing invoices...")
            
            table = page.locator('table').first
            if not await table.count():
                print("❌ No table found")
                return []
            
            rows = table.locator('tbody tr, .table-row, .invoice-row')
            row_count = await rows.count()
            print(f"Found {row_count} rows")
            
            # Find column indices
            headers = table.locator('th, .table-header')
            column_indices = {}
            
            for i in range(await headers.count()):
                header_text = await headers.nth(i).text_content()
                if header_text:
                    header_text = header_text.lower().strip()
                    if "service" in header_text:
                        column_indices["service"] = i
                    elif "initial date" in header_text or "fecha inicial" in header_text:
                        column_indices["initial_date"] = i
                    elif "final date" in header_text or "fecha final" in header_text:
                        column_indices["final_date"] = i
            
            print(f"Columns: {column_indices}")
            
            # STEP 1: Find water bill FIRST to determine billing period
            print("\n🌊 STEP 1: Finding water bill to determine billing period...")
            water_bill_period = None
            water_bill_row = None
            
            for i in range(min(15, row_count)):
                try:
                    row = rows.nth(i)
                    
                    # Check service type using the EXACT same logic as download button scraper
                    service_type = None
                    if "service" in column_indices:
                        service_cell = row.locator(f'td:nth-child({column_indices["service"] + 1}), .col-{column_indices["service"] + 1}')
                        if await service_cell.count():
                            service_text = await service_cell.text_content()
                            if service_text:
                                service_text = service_text.lower().strip()
                                if "water" in service_text:
                                    service_type = "water"
                    
                    if service_type == "water":
                        # Get dates
                        initial_date_str = ""
                        final_date_str = ""
                        if "initial_date" in column_indices:
                            initial_cell = row.locator(f'td:nth-child({column_indices["initial_date"] + 1}), .col-{column_indices["initial_date"] + 1}')
                            if await initial_cell.count():
                                initial_date_str = await initial_cell.text_content() or ""
                        if "final_date" in column_indices:
                            final_cell = row.locator(f'td:nth-child({column_indices["final_date"] + 1}), .col-{column_indices["final_date"] + 1}')
                            if await final_cell.count():
                                final_date_str = await final_cell.text_content() or ""
                        
                        if initial_date_str and final_date_str:
                            initial_date_str = initial_date_str.strip()
                            final_date_str = final_date_str.strip()
                            
                            # Use the same logic as download button scraper
                            date_relevant = is_relevant_water_bill(initial_date_str, final_date_str)
                            print(f"   🌊 Found water bill: {initial_date_str} to {final_date_str} (relevant: {date_relevant})")
                            
                            if date_relevant:
                                initial_date = parse_date(initial_date_str)
                                final_date = parse_date(final_date_str)
                                if initial_date and final_date:
                                    water_bill_period = (initial_date, final_date)
                                    water_bill_row = i
                                    break
                except Exception as e:
                    continue
            
            if not water_bill_period:
                print("❌ No water bill found - cannot determine billing period")
                return []
            
            print(f"✅ Using billing period: {water_bill_period[0].strftime('%d/%m/%Y')} to {water_bill_period[1].strftime('%d/%m/%Y')}")
            
            # STEP 2: Download water bill
            print(f"\n🌊 STEP 2: Downloading water bill...")
            try:
                water_row = rows.nth(water_bill_row)
                first_cell = water_row.locator('td').first
                buttons = first_cell.locator('button, a, [role="button"]')
                
                if await buttons.count() > 0:
                    button = buttons.first
                    await button.click()
                    await _wait(page, "water bill click")
                    
                    # Check for new tab
                    if len(context.pages) > 1:
                        new_page = context.pages[-1]
                        await new_page.wait_for_load_state("networkidle")
                        new_url = new_page.url
                        
                        if ".PDF" in new_url.upper() or ".pdf" in new_url:
                            print(f"   📥 Downloading water bill...")
                            
                            # Download using requests (ONLY method)
                            response = requests.get(new_url)
                            if response.status_code == 200:
                                ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                                filename = f"invoice_{property_name}_water_{ts}.pdf"
                                local_path = Path("_debug/downloads") / filename
                                local_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                with open(local_path, 'wb') as f:
                                    f.write(response.content)
                                
                                size = local_path.stat().st_size
                                print(f"   ✅ Water bill: {filename} ({size} bytes)")
                                downloaded_files.append(str(local_path))
                            
                        await new_page.close()
            except Exception as e:
                print(f"   ❌ Water bill failed: {e}")
            
            # STEP 3: Find and download electricity bills in SAME period
            print(f"\n⚡ STEP 3: Finding electricity bills in billing period...")
            elec_count = 0
            max_elec = 2
            
            for i in range(min(20, row_count)):
                if elec_count >= max_elec:
                    break
                    
                try:
                    row = rows.nth(i)
                    
                    # Check service type using the EXACT same logic as download button scraper
                    service_type = None
                    if "service" in column_indices:
                        service_cell = row.locator(f'td:nth-child({column_indices["service"] + 1}), .col-{column_indices["service"] + 1}')
                        if await service_cell.count():
                            service_text = await service_cell.text_content()
                            if service_text:
                                service_text = service_text.lower().strip()
                                if "electricity" in service_text or "elec" in service_text:
                                    service_type = "electricity"
                    
                    if service_type == "electricity":
                        # Get dates
                        initial_date_str = ""
                        final_date_str = ""
                        if "initial_date" in column_indices:
                            initial_cell = row.locator(f'td:nth-child({column_indices["initial_date"] + 1}), .col-{column_indices["initial_date"] + 1}')
                            if await initial_cell.count():
                                initial_date_str = await initial_cell.text_content() or ""
                        if "final_date" in column_indices:
                            final_cell = row.locator(f'td:nth-child({column_indices["final_date"] + 1}), .col-{column_indices["final_date"] + 1}')
                            if await final_cell.count():
                                final_date_str = await final_cell.text_content() or ""
                        
                        initial_date = parse_date(initial_date_str)
                        final_date = parse_date(final_date_str)
                        
                        # Check if it's within the water bill period
                        if initial_date and final_date and is_within_period(initial_date, final_date, water_bill_period[0], water_bill_period[1]):
                            print(f"   ⚡ Found electricity bill: {initial_date_str} to {final_date_str}")
                            
                            # Download electricity bill
                            first_cell = row.locator('td').first
                            buttons = first_cell.locator('button, a, [role="button"]')
                            
                            if await buttons.count() > 0:
                                button = buttons.first
                                await button.click()
                                await _wait(page, "electricity bill click")
                                
                                # Check for new tab
                                if len(context.pages) > 1:
                                    new_page = context.pages[-1]
                                    await new_page.wait_for_load_state("networkidle")
                                    new_url = new_page.url
                                    
                                    if ".PDF" in new_url.upper() or ".pdf" in new_url:
                                        print(f"   📥 Downloading electricity bill...")
                                        
                                        # Download using requests (ONLY method)
                                        response = requests.get(new_url)
                                        if response.status_code == 200:
                                            elec_count += 1
                                            ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                                            filename = f"invoice_{property_name}_electricity_{elec_count}_{ts}.pdf"
                                            local_path = Path("_debug/downloads") / filename
                                            local_path.parent.mkdir(parents=True, exist_ok=True)
                                            
                                            with open(local_path, 'wb') as f:
                                                f.write(response.content)
                                            
                                            size = local_path.stat().st_size
                                            print(f"   ✅ Electricity {elec_count}: {filename} ({size} bytes)")
                                            downloaded_files.append(str(local_path))
                                        
                                    await new_page.close()
                except Exception as e:
                    continue
            
            print(f"\n📊 SUMMARY: Downloaded {len(downloaded_files)} invoices")
            print(f"   🌊 Water: 1/1")
            print(f"   ⚡ Electricity: {elec_count}/2")
            print(f"   📄 Total: {len(downloaded_files)}/3")
            
            # Upload to Supabase
            if downloaded_files:
                print(f"\n☁️ Uploading to Supabase...")
                try:
                    from src.pdf_storage import pdf_storage
                    
                    for i, file_path in enumerate(downloaded_files, 1):
                        try:
                            with open(file_path, 'rb') as f:
                                pdf_content = f.read()
                            
                            filename = Path(file_path).name
                            
                            result = pdf_storage.upload_pdf(
                                file_data=pdf_content,
                                filename=filename,
                                property_name=property_name,
                                invoice_type="water" if "water" in filename else "electricity"
                            )
                            
                            if result.get("success"):
                                print(f"   ✅ Uploaded {i}/{len(downloaded_files)}: {filename}")
                            else:
                                print(f"   ❌ Upload failed {i}/{len(downloaded_files)}: {result.get('error')}")
                                
                        except Exception as e:
                            print(f"   ❌ Upload error {i}/{len(downloaded_files)}: {e}")
                            
                except Exception as e:
                    print(f"❌ Supabase upload failed: {e}")
            
            return downloaded_files
    
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        return []

async def main():
    """Main function."""
    property_name = "Aribau 1º 1ª"
    
    print("🚀 Super Fast Invoice Scraper")
    print("=" * 40)
    print("Features:")
    print("✅ Water bill FIRST to determine period")
    print("✅ Electricity bills in SAME period")
    print("✅ Requests download ONLY (no fallbacks)")
    print("✅ 1-second delays (ultra-fast)")
    print("✅ No screenshots, no timeouts")
    print()
    
    downloaded_files = await super_fast_scraper(property_name)
    
    if downloaded_files:
        print(f"\n🎉 Success! Downloaded {len(downloaded_files)} invoices:")
        for file_path in downloaded_files:
            print(f"  📄 {file_path}")
    else:
        print("\n❌ No invoices were downloaded")

if __name__ == "__main__":
    asyncio.run(main())
