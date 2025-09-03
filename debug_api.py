#!/usr/bin/env python3
"""
Debug script to test the API locally and see what's happening with the filtering
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api import calculate_monthly_report, CalculationRequest
from src.polaroo_process import USER_ADDRESSES

async def test_calculation():
    print("🔍 [DEBUG] Testing calculation locally...")
    print(f"🔍 [DEBUG] USER_ADDRESSES has {len(USER_ADDRESSES)} properties")
    print(f"🔍 [DEBUG] First 5 USER_ADDRESSES: {USER_ADDRESSES[:5]}")
    
    # Create a test request
    request = CalculationRequest(
        month="2025-08",
        year=2025
    )
    
    try:
        result = await calculate_monthly_report(request)
        print(f"✅ [DEBUG] Calculation completed successfully!")
        print(f"📊 [DEBUG] Result type: {type(result)}")
        print(f"📊 [DEBUG] Result success: {result.success}")
        print(f"📊 [DEBUG] Result message: {result.message}")
        print(f"📊 [DEBUG] Result data: {result.data is not None}")
        
        if result.success and result.data:
            data = result.data
            print(f"📊 [DEBUG] Data keys: {data.keys()}")
            
            if 'properties' in data:
                properties = data['properties']
            print(f"📊 [DEBUG] Found {len(properties)} properties in result")
            
            if properties:
                print(f"📊 [DEBUG] First 3 properties:")
                for i, prop in enumerate(properties[:3]):
                    print(f"  {i+1}. {prop['name']}")
                    print(f"    - elec_cost: {prop['elec_cost']}, water_cost: {prop['water_cost']}")
                    print(f"    - total_extra: {prop['total_extra']}")
                    print(f"    - allowance: {prop['allowance']}")
            
            # Check if all returned properties are in USER_ADDRESSES
            returned_names = [p['name'] for p in properties]
            in_book1 = [name for name in returned_names if name in USER_ADDRESSES]
            not_in_book1 = [name for name in returned_names if name not in USER_ADDRESSES]
            
            print(f"📊 [DEBUG] Properties in book1: {len(in_book1)}")
            print(f"📊 [DEBUG] Properties NOT in book1: {len(not_in_book1)}")
            
            if not_in_book1:
                print(f"⚠️ [DEBUG] Properties NOT in book1: {not_in_book1[:5]}")
        
            if 'summary' in data:
                summary = data['summary']
            print(f"📊 [DEBUG] Summary:")
            print(f"  - total_properties: {summary.get('total_properties', 'N/A')}")
            print(f"  - total_extra: {summary.get('total_extra', 'N/A')}")
            print(f"  - properties_with_overages: {summary.get('properties_with_overages', 'N/A')}")
            print(f"  - filter_applied: {summary.get('filter_applied', 'N/A')}")
            print(f"  - total_properties_processed: {summary.get('total_properties_processed', 'N/A')}")
        
    except Exception as e:
        print(f"❌ [DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_calculation())
