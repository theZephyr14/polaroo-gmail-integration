#!/usr/bin/env python3
"""
Fast PDF Invoice Scraper
========================

Optimized version that only uses the working method (requests) and finds water bills first
to determine the correct billing period for electricity bills.
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

# Global wait time - 2 seconds for speed
WAIT_MS = 2000

async def _wait(page, label: str):
    """Wait for 2 seconds with logging."""
    print(f"⏳ [WAIT] {label} … {WAIT_MS}ms")
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

async def download_invoices_fast(property_name: str):
    """Fast invoice download - only uses working methods."""
    print(f"🚀 Fast Invoice Scraper for: {property_name}")
    print("=" * 50)
    
    downloaded_files = []
    
    try:
        async with async_playwright() as p:
            # Launch browser
            print("🌐 [BROWSER] Launching browser...")
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # 1) Login
            print("🔐 [LOGIN] Checking login status...")
            await page.goto("https://app.polaroo.com/login")
            await _wait(page, "after navigating to login page")
            
            if "dashboard" not in page.url:
                print("❌ [LOGIN] Not logged in, please login manually first")
                return []
            
            print("✅ [LOGIN] Already logged in")
            
            # 2) Navigate to Invoices
            print("📄 [INVOICES] Navigating to invoices page...")
            await page.goto("https://app.polaroo.com/dashboard/accounting")
            await _wait(page, "after navigating to invoices page")
            
            # 3) Search for property
            print("🔍 [SEARCH] Searching for property...")
            search_input = page.locator('input[placeholder*="search" i]').first
            await search_input.clear()
            await search_input.fill(property_name)
            await search_input.press("Enter")
            await page.wait_for_load_state("networkidle")
            await _wait(page, "after search")
            
            # 4) Analyze table and find billing period
            print("📊 [ANALYSIS] Analyzing invoices...")
            
            table = page.locator('table').first
            if not await table.count():
                print("❌ [ERROR] No table found")
                return []
            
            rows = table.locator('tbody tr, .table-row, .invoice-row')
            row_count = await rows.count()
            print(f"🔍 Found {row_count} rows")
            
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
            
            print(f"✅ Column indices: {column_indices}")
            
            # STEP 1: Find the most recent water bill to determine billing period
            print("\n🌊 [STEP 1] Finding water bill to determine billing period...")
            water_bill_period = None
            water_bill_row = None
            
            for i in range(min(20, row_count)):
                try:
                    row = rows.nth(i)
                    
                    # Check if it's a water bill
                    if "service" in column_indices:
                        service_cell = row.locator('td').nth(column_indices["service"])
                        service_text = await service_cell.text_content()
                        if service_text and "water" in service_text.lower():
                            # Get dates
                            initial_date_str = ""
                            final_date_str = ""
                            if "initial_date" in column_indices:
                                initial_cell = row.locator('td').nth(column_indices["initial_date"])
                                initial_date_str = await initial_cell.text_content() or ""
                            if "final_date" in column_indices:
                                final_cell = row.locator('td').nth(column_indices["final_date"])
                                final_date_str = await final_cell.text_content() or ""
                            
                            initial_date = parse_date(initial_date_str)
                            final_date = parse_date(final_date_str)
                            
                            if initial_date and final_date:
                                print(f"   🌊 Found water bill: {initial_date_str} to {final_date_str}")
                                water_bill_period = (initial_date, final_date)
                                water_bill_row = i
                                break
                except Exception as e:
                    continue
            
            if not water_bill_period:
                print("❌ [ERROR] No water bill found to determine billing period")
                return []
            
            print(f"✅ [WATER] Using billing period: {water_bill_period[0].strftime('%d/%m/%Y')} to {water_bill_period[1].strftime('%d/%m/%Y')}")
            
            # STEP 2: Download water bill
            print(f"\n🌊 [STEP 2] Downloading water bill...")
            try:
                water_row = rows.nth(water_bill_row)
                first_cell = water_row.locator('td').first
                buttons = first_cell.locator('button, a, [role="button"]')
                
                if await buttons.count() > 0:
                    button = buttons.first
                    await button.click()
                    await _wait(page, "after clicking water bill")
                    
                    # Check for new tab
                    if len(context.pages) > 1:
                        new_page = context.pages[-1]
                        await new_page.wait_for_load_state("networkidle")
                        new_url = new_page.url
                        
                        if ".PDF" in new_url.upper() or ".pdf" in new_url:
                            print(f"   📥 Downloading water bill from: {new_url}")
                            
                            # Download using requests
                            response = requests.get(new_url)
                            if response.status_code == 200:
                                ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                                filename = f"invoice_{property_name}_water_{ts}.pdf"
                                local_path = Path("_debug/downloads") / filename
                                local_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                with open(local_path, 'wb') as f:
                                    f.write(response.content)
                                
                                size = local_path.stat().st_size
                                print(f"   ✅ Water bill downloaded: {filename} ({size} bytes)")
                                downloaded_files.append(str(local_path))
                            
                        await new_page.close()
            except Exception as e:
                print(f"   ❌ Water bill download failed: {e}")
            
            # STEP 3: Find and download electricity bills in the same period
            print(f"\n⚡ [STEP 3] Finding electricity bills in billing period...")
            elec_count = 0
            max_elec = 2
            
            for i in range(min(20, row_count)):
                if elec_count >= max_elec:
                    break
                    
                try:
                    row = rows.nth(i)
                    
                    # Check if it's an electricity bill
                    if "service" in column_indices:
                        service_cell = row.locator('td').nth(column_indices["service"])
                        service_text = await service_cell.text_content()
                        if service_text and ("electricity" in service_text.lower() or "elec" in service_text.lower()):
                            # Get dates
                            initial_date_str = ""
                            final_date_str = ""
                            if "initial_date" in column_indices:
                                initial_cell = row.locator('td').nth(column_indices["initial_date"])
                                initial_date_str = await initial_cell.text_content() or ""
                            if "final_date" in column_indices:
                                final_cell = row.locator('td').nth(column_indices["final_date"])
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
                                    await _wait(page, "after clicking electricity bill")
                                    
                                    # Check for new tab
                                    if len(context.pages) > 1:
                                        new_page = context.pages[-1]
                                        await new_page.wait_for_load_state("networkidle")
                                        new_url = new_page.url
                                        
                                        if ".PDF" in new_url.upper() or ".pdf" in new_url:
                                            print(f"   📥 Downloading electricity bill from: {new_url}")
                                            
                                            # Download using requests
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
                                                print(f"   ✅ Electricity bill {elec_count} downloaded: {filename} ({size} bytes)")
                                                downloaded_files.append(str(local_path))
                                            
                                        await new_page.close()
                except Exception as e:
                    continue
            
            print(f"\n📊 [SUMMARY] Downloaded {len(downloaded_files)} invoices:")
            print(f"   🌊 Water bills: 1/1")
            print(f"   ⚡ Electricity bills: {elec_count}/2")
            print(f"   📄 Total: {len(downloaded_files)}/3")
            
            # Upload to Supabase
            if downloaded_files:
                print(f"\n☁️ [UPLOAD] Uploading to Supabase...")
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
                    print(f"❌ [UPLOAD] Supabase upload failed: {e}")
            
            return downloaded_files
    
    except Exception as e:
        print(f"❌ [ERROR] Scraper failed: {e}")
        return []

async def main():
    """Main function."""
    property_name = "Aribau 1º 1ª"
    
    print("🚀 Fast PDF Invoice Scraper")
    print("=" * 40)
    print("Strategy:")
    print("1. Find water bill first to determine billing period")
    print("2. Find electricity bills in same period")
    print("3. Download only using requests (fast & reliable)")
    print("4. Upload to Supabase")
    print()
    
    downloaded_files = await download_invoices_fast(property_name)
    
    if downloaded_files:
        print(f"\n🎉 Success! Downloaded {len(downloaded_files)} invoices:")
        for file_path in downloaded_files:
            print(f"  📄 {file_path}")
    else:
        print("\n❌ No invoices were downloaded")

if __name__ == "__main__":
    asyncio.run(main())
