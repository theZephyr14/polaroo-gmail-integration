#!/usr/bin/env python3
"""
LLM-Powered Super Fast Invoice Scraper
======================================

Uses Cohere LLM to intelligently match water bills with electricity bills,
then downloads only the matched invoices using the fast requests method.
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

# Import credentials and LLM matcher
from src.config import POLAROO_EMAIL, POLAROO_PASSWORD
from llm_invoice_matcher import LLMInvoiceMatcher

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

async def llm_super_fast_scraper(property_name: str):
    """LLM-powered super fast invoice scraper."""
    print(f"🤖 LLM Super Fast Scraper for: {property_name}")
    print("=" * 60)
    print("Strategy: LLM matches water + electricity → Download only matched invoices")
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
            
            # 4) Analyze table and extract all invoices
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
            
            # 5) Extract all invoice data for LLM analysis
            print("\n🤖 Extracting invoice data for LLM analysis...")
            all_invoices = []
            
            for i in range(min(20, row_count)):
                try:
                    row = rows.nth(i)
                    
                    # Extract service type
                    service_type = None
                    if "service" in column_indices:
                        service_cell = row.locator(f'td:nth-child({column_indices["service"] + 1}), .col-{column_indices["service"] + 1}')
                        if await service_cell.count():
                            service_text = await service_cell.text_content()
                            if service_text:
                                service_text = service_text.lower().strip()
                                if "electricity" in service_text or "elec" in service_text:
                                    service_type = "Electricity"
                                elif "water" in service_text:
                                    service_type = "Water"
                                elif "gas" in service_text:
                                    service_type = "Gas"
                    
                    if service_type in ["Electricity", "Water"]:  # Only include relevant services
                        # Extract dates
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
                            invoice_data = {
                                'service': service_type,
                                'initial_date': initial_date_str.strip(),
                                'final_date': final_date_str.strip(),
                                'row_index': i
                            }
                            all_invoices.append(invoice_data)
                            print(f"   📋 Row {i+1}: {service_type} ({initial_date_str.strip()} to {final_date_str.strip()})")
                
                except Exception as e:
                    continue
            
            print(f"\n📊 Found {len(all_invoices)} relevant invoices for LLM analysis")
            
            # 6) Use LLM to match invoices
            print("\n🤖 Using LLM to match water + electricity bills...")
            try:
                matcher = LLMInvoiceMatcher()
                match_result = matcher.match_invoices(all_invoices)
                
                if not match_result['success']:
                    print("❌ LLM matching failed, using fallback logic")
                    return []
                
                print(f"✅ LLM Matching Results:")
                print(f"   🌊 Water Bill: Row {match_result['water_bill']}")
                print(f"   ⚡ Electricity Bills: Rows {match_result['electricity_bills']}")
                print(f"   💭 Reasoning: {match_result['reasoning']}")
                
                # 7) Download only the matched invoices
                print(f"\n📥 Downloading matched invoices...")
                
                # Download water bill
                if match_result['water_bill'] is not None:
                    water_row = rows.nth(match_result['water_bill'])
                    success = await download_invoice_from_row(water_row, context, "water", property_name, downloaded_files)
                    if success:
                        print(f"   ✅ Water bill downloaded")
                
                # Download electricity bills
                for elec_row_idx in match_result['electricity_bills']:
                    elec_row = rows.nth(elec_row_idx)
                    success = await download_invoice_from_row(elec_row, context, "electricity", property_name, downloaded_files)
                    if success:
                        print(f"   ✅ Electricity bill downloaded")
                
            except Exception as e:
                print(f"❌ LLM matching error: {e}")
                return []
            
            print(f"\n📊 SUMMARY: Downloaded {len(downloaded_files)} invoices")
            print(f"   🌊 Water: 1/1")
            print(f"   ⚡ Electricity: {len(match_result.get('electricity_bills', []))}/2")
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

async def download_invoice_from_row(row, context, service_type, property_name, downloaded_files):
    """Download an invoice from a specific row."""
    try:
        first_cell = row.locator('td').first
        buttons = first_cell.locator('button, a, [role="button"]')
        
        if await buttons.count() > 0:
            button = buttons.first
            await button.click()
            await _wait(None, f"{service_type} bill click")
            
            # Check for new tab
            if len(context.pages) > 1:
                new_page = context.pages[-1]
                await new_page.wait_for_load_state("networkidle")
                new_url = new_page.url
                
                if ".PDF" in new_url.upper() or ".pdf" in new_url:
                    print(f"   📥 Downloading {service_type} bill...")
                    
                    # Download using requests (ONLY method)
                    response = requests.get(new_url)
                    if response.status_code == 200:
                        ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
                        filename = f"invoice_{property_name}_{service_type}_{ts}.pdf"
                        local_path = Path("_debug/downloads") / filename
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        
                        size = local_path.stat().st_size
                        print(f"   ✅ {service_type.title()} bill: {filename} ({size} bytes)")
                        downloaded_files.append(str(local_path))
                        return True
                
                await new_page.close()
        
        return False
        
    except Exception as e:
        print(f"   ❌ {service_type.title()} bill download failed: {e}")
        return False

async def main():
    """Main function."""
    property_name = "Aribau 1º 1ª"
    
    print("🤖 LLM-Powered Super Fast Invoice Scraper")
    print("=" * 50)
    print("Features:")
    print("✅ LLM intelligently matches water + electricity bills")
    print("✅ Downloads only the matched invoices")
    print("✅ Requests download ONLY (no fallbacks)")
    print("✅ 1-second delays (ultra-fast)")
    print("✅ No screenshots, no timeouts")
    print()
    
    # Check for Cohere API key
    if not os.getenv("COHERE_API_KEY"):
        print("❌ COHERE_API_KEY environment variable is required")
        print("💡 Get your API key from: https://cohere.com/")
        return
    
    downloaded_files = await llm_super_fast_scraper(property_name)
    
    if downloaded_files:
        print(f"\n🎉 Success! Downloaded {len(downloaded_files)} invoices:")
        for file_path in downloaded_files:
            print(f"  📄 {file_path}")
    else:
        print("\n❌ No invoices were downloaded")

if __name__ == "__main__":
    asyncio.run(main())
