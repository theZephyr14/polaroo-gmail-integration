#!/usr/bin/env python3
"""
LLM-Powered Invoice Matcher
===========================

Uses Cohere LLM to intelligently match water bills with electricity bills
based on overlapping billing periods.
"""

import cohere
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Add src to path
sys.path.append('src')

class LLMInvoiceMatcher:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM matcher with Cohere API key."""
        if api_key:
            self.api_key = api_key
        else:
            # Try to import from config
            try:
                from src.config import COHERE_API_KEY
                self.api_key = COHERE_API_KEY
            except ImportError:
                self.api_key = os.getenv("COHERE_API_KEY")
        
        if not self.api_key:
            raise ValueError("COHERE_API_KEY not found. Please set it in environment or config.")
        
        self.co = cohere.Client(self.api_key)
    
    def match_invoices(self, invoices: List[Dict]) -> Dict:
        """
        Use LLM to match water bills with electricity bills based on billing periods.
        
        Args:
            invoices: List of invoice dictionaries with service, initial_date, final_date
            
        Returns:
            Dictionary with matched invoices and reasoning
        """
        
        # Prepare the prompt
        prompt = self._create_matching_prompt(invoices)
        
        try:
            response = self.co.generate(
                model="command",
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1,
                stop_sequences=["---"]
            )
            
            result = response.generations[0].text.strip()
            return self._parse_llm_response(result)
            
        except Exception as e:
            print(f"❌ LLM matching failed: {e}")
            return self._fallback_matching(invoices)
    
    def _create_matching_prompt(self, invoices: List[Dict]) -> str:
        """Create a prompt for the LLM to match invoices."""
        
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        prompt = f"""You are an expert at matching utility bills for billing periods. Today's date is {current_date}.

INVOICE MATCHING RULES:
1. ONLY consider Water and Electricity bills (IGNORE Gas completely)
2. Water bills are BI-MONTHLY (every 2 months)
3. Electricity bills are MONTHLY (every month)
4. For a 2-month billing period, we need: 1 water bill + 2 electricity bills
5. Find the most recent water bill first, then find 2 electricity bills that overlap with that water bill period
6. Look for electricity bills where the final_date falls within the water bill period

INVOICES TO MATCH:
"""
        
        for i, invoice in enumerate(invoices, 1):
            service = invoice.get('service', 'Unknown')
            if service in ['Water', 'Electricity']:  # Only show relevant services
                prompt += f"""
Invoice {i}:
- Service: {service}
- Period: {invoice.get('initial_date', 'N/A')} to {invoice.get('final_date', 'N/A')}
- Row: {invoice.get('row_index', 'N/A')}
"""
        
        prompt += """

TASK: 
1. Find the most recent WATER bill (highest final_date among water bills only)
2. Find 2 ELECTRICITY bills where the final_date falls within the water bill period
3. Return the row indices of the selected invoices
4. IGNORE all Gas bills completely

RESPONSE FORMAT:
WATER_BILL: [row_index]
ELECTRICITY_BILLS: [row_index1, row_index2]
REASONING: [explanation of the matching logic]

Example:
WATER_BILL: 3
ELECTRICITY_BILLS: [7, 6]
REASONING: Water bill from 24/04/2025 to 25/06/2025 is the most recent water bill. Electricity bills from 17/04/2025 to 16/05/2025 (final_date 16/05/2025) and 17/05/2025 to 16/06/2025 (final_date 16/06/2025) both have final dates within the water bill period.

---
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse the LLM response into structured data."""
        try:
            print(f"🔍 LLM Response: {response}")
            
            lines = response.strip().split('\n')
            result = {
                'water_bill': None,
                'electricity_bills': [],
                'reasoning': '',
                'success': False
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('WATER_BILL:'):
                    try:
                        water_str = line.split(':')[1].strip()
                        # Remove brackets if present
                        water_str = water_str.strip('[]')
                        result['water_bill'] = int(water_str)
                    except:
                        pass
                elif line.startswith('ELECTRICITY_BILLS:'):
                    try:
                        bills_str = line.split(':')[1].strip()
                        # Remove brackets and split by comma
                        bills_str = bills_str.strip('[]')
                        if bills_str:
                            result['electricity_bills'] = [int(x.strip()) for x in bills_str.split(',')]
                    except:
                        pass
                elif line.startswith('REASONING:'):
                    result['reasoning'] = line.split(':', 1)[1].strip()
            
            result['success'] = result['water_bill'] is not None and len(result['electricity_bills']) >= 1
            
            return result
            
        except Exception as e:
            print(f"❌ Error parsing LLM response: {e}")
            return {'success': False, 'error': str(e)}
    
    def _fallback_matching(self, invoices: List[Dict]) -> Dict:
        """Fallback matching logic if LLM fails."""
        print("🔄 Using fallback matching logic...")
        
        # Simple fallback: find first water bill and first 2 electricity bills
        water_bill = None
        electricity_bills = []
        
        for invoice in invoices:
            service = invoice.get('service', '').lower()
            if 'water' in service and water_bill is None:
                water_bill = invoice.get('row_index')
            elif 'electricity' in service and len(electricity_bills) < 2:
                electricity_bills.append(invoice.get('row_index'))
        
        return {
            'water_bill': water_bill,
            'electricity_bills': electricity_bills,
            'reasoning': 'Fallback logic: first water bill + first 2 electricity bills',
            'success': water_bill is not None and len(electricity_bills) >= 1
        }

def test_llm_matcher():
    """Test the LLM matcher with sample data."""
    
    # Sample invoices based on your table (matching the image exactly)
    sample_invoices = [
        {'service': 'Electricity', 'initial_date': '17/07/2025', 'final_date': '16/08/2025', 'row_index': 0},
        {'service': 'Electricity', 'initial_date': '17/07/2025', 'final_date': '17/07/2025', 'row_index': 1},
        {'service': 'Electricity', 'initial_date': '17/06/2025', 'final_date': '16/07/2025', 'row_index': 2},
        {'service': 'Water', 'initial_date': '24/04/2025', 'final_date': '25/06/2025', 'row_index': 3},
        {'service': 'Gas', 'initial_date': '06/05/2025', 'final_date': '02/07/2025', 'row_index': 4},
        {'service': 'Gas', 'initial_date': '11/03/2025', 'final_date': '05/05/2025', 'row_index': 5},
        {'service': 'Electricity', 'initial_date': '17/05/2025', 'final_date': '16/06/2025', 'row_index': 6},
        {'service': 'Electricity', 'initial_date': '17/04/2025', 'final_date': '16/05/2025', 'row_index': 7},
        {'service': 'Water', 'initial_date': '24/02/2025', 'final_date': '24/04/2025', 'row_index': 8},
    ]
    
    try:
        matcher = LLMInvoiceMatcher()
        result = matcher.match_invoices(sample_invoices)
        
        print("🤖 LLM Invoice Matching Results:")
        print("=" * 40)
        print(f"✅ Success: {result['success']}")
        print(f"🌊 Water Bill Row: {result['water_bill']}")
        print(f"⚡ Electricity Bill Rows: {result['electricity_bills']}")
        print(f"💭 Reasoning: {result['reasoning']}")
        
        if result['success']:
            print("\n📋 Selected Invoices:")
            for invoice in sample_invoices:
                if invoice['row_index'] in [result['water_bill']] + result['electricity_bills']:
                    print(f"  Row {invoice['row_index']}: {invoice['service']} ({invoice['initial_date']} to {invoice['final_date']})")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    test_llm_matcher()
