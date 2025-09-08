#!/usr/bin/env python3
"""
Streamlit Frontend for Polaroo Utility Bill System
==================================================

A simple Streamlit interface to test the system locally with mock data.
This avoids the Playwright browser automation issues for local testing.

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Polaroo Utility Bill System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def main():
    st.title("⚡ Polaroo Utility Bill System")
    st.markdown("---")
    
    # Check API health
    with st.spinner("Checking API connection..."):
        api_healthy, health_data = check_api_health()
    
    if not api_healthy:
        st.error("❌ API is not running. Please start the server first:")
        st.code("python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    st.success("✅ API is running and healthy!")
    
    # Sidebar
    st.sidebar.title("🧪 Test Options")
    
    # Test selection
    test_option = st.sidebar.selectbox(
        "Choose a test to run:",
        [
            "📊 Monthly Calculation (Mock Data)",
            "📄 Mock Invoice Download",
            "📧 Email Generation",
            "⏳ Email Approval Workflow",
            "📈 Statistics",
            "🌐 Web Interface Link"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Quick Actions")
    
    if st.sidebar.button("🔄 Refresh All Data"):
        st.rerun()
    
    # Main content area
    if test_option == "📊 Monthly Calculation (Mock Data)":
        test_monthly_calculation()
    elif test_option == "📄 Mock Invoice Download":
        test_invoice_download()
    elif test_option == "📧 Email Generation":
        test_email_generation()
    elif test_option == "⏳ Email Approval Workflow":
        test_email_approval_workflow()
    elif test_option == "📈 Statistics":
        test_statistics()
    elif test_option == "🌐 Web Interface Link":
        show_web_interface()

def test_monthly_calculation():
    st.header("📊 Monthly Calculation Test")
    st.markdown("Testing the improved scraper logic with custom date range (last 2 months)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🧮 Calculation Process")
        st.markdown("""
        This test simulates the monthly calculation process:
        1. **Improved Scraper Logic**: Uses custom date range for last 2 months instead of "Last month"
        2. **Data Processing**: Processes utility data with room-based allowances
        3. **Overage Calculation**: Identifies properties with overages
        """)
    
    with col2:
        if st.button("🚀 Run Calculation", type="primary"):
            with st.spinner("Running calculation..."):
                try:
                    response = requests.post(f"{BASE_URL}/api/calculate", json={"auto_save": False})
                    if response.status_code == 200:
                        result = response.json()
                        if result["success"]:
                            st.success("✅ Calculation completed successfully!")
                            
                            # Store results in session state
                            st.session_state.calculation_data = result["data"]
                            
                            # Display summary
                            summary = result["data"]["summary"]
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Total Properties", summary["total_properties"])
                            with col2:
                                st.metric("Properties with Overages", summary["properties_with_overages"])
                            with col3:
                                st.metric("Total Extra (€)", f"€{summary['total_extra']:.2f}")
                            with col4:
                                st.metric("Calculation Date", summary["calculation_date"][:10])
                            
                            # Display properties table
                            if summary["total_properties"] > 0:
                                st.markdown("### 📋 Properties Overview")
                                properties_df = pd.DataFrame(result["data"]["properties"])
                                st.dataframe(properties_df, use_container_width=True)
                        else:
                            st.error(f"❌ Calculation failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ Request failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Show stored results if available
    if "calculation_data" in st.session_state:
        st.markdown("### 📊 Last Calculation Results")
        data = st.session_state.calculation_data
        
        # Summary metrics
        summary = data["summary"]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Electricity Cost", f"€{summary['total_electricity_cost']:.2f}")
        with col2:
            st.metric("Total Water Cost", f"€{summary['total_water_cost']:.2f}")
        with col3:
            st.metric("Total Extra", f"€{summary['total_extra']:.2f}")
        
        # Properties with overages
        overages = [p for p in data["properties"] if p["total_extra"] > 0]
        if overages:
            st.markdown("### ⚠️ Properties with Overages")
            overages_df = pd.DataFrame(overages)
            st.dataframe(overages_df, use_container_width=True)
        else:
            st.success("🎉 No properties with overages found!")

def test_invoice_download():
    st.header("📄 Mock Invoice Download Test")
    st.markdown("Testing the invoice download functionality with mock data")
    
    # Property selection
    property_name = st.text_input("Property Name", value="Aribau 1º 1ª", help="Enter a property name to test invoice download")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Invoice Download Process")
        st.markdown("""
        This test simulates downloading invoices from Polaroo:
        1. **Navigation**: Goes to Invoices section in Polaroo
        2. **Search**: Searches for the property name
        3. **Download**: Downloads 2 electricity + 1 water invoice
        4. **Storage**: Saves files with 10-minute expiry
        """)
    
    with col2:
        if st.button("📥 Download Invoices", type="primary"):
            with st.spinner(f"Downloading invoices for {property_name}..."):
                try:
                    response = requests.post(f"{BASE_URL}/api/invoices/download", json={
                        "property_name": property_name
                    })
                    if response.status_code == 200:
                        result = response.json()
                        if result["success"]:
                            st.success("✅ Invoice download successful!")
                            
                            # Display invoice details
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### ⚡ Electricity Invoice")
                                elec_invoice = result.get("electricity_invoice", {})
                                if elec_invoice:
                                    st.json(elec_invoice)
                                else:
                                    st.info("No electricity invoice data")
                            
                            with col2:
                                st.markdown("#### 💧 Water Invoice")
                                water_invoice = result.get("water_invoice", {})
                                if water_invoice:
                                    st.json(water_invoice)
                                else:
                                    st.info("No water invoice data")
                        else:
                            st.error(f"❌ Invoice download failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ Request failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Test real invoice download
    st.markdown("---")
    st.markdown("### 🌐 Real Invoice Download Test")
    st.markdown("⚠️ **Note**: This requires real Polaroo credentials and will attempt to download actual invoices")
    
    if st.button("🔗 Test Real Invoice Download", type="secondary"):
        with st.spinner(f"Testing real invoice download for {property_name}..."):
            try:
                response = requests.post(f"{BASE_URL}/api/invoices/download-real", json={
                    "property_name": property_name
                })
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        st.success(f"✅ Successfully downloaded {result['total_files']} invoices!")
                        
                        # Display downloaded files
                        if result.get("downloaded_files"):
                            st.markdown("#### 📁 Downloaded Files")
                            files_df = pd.DataFrame(result["downloaded_files"])
                            st.dataframe(files_df, use_container_width=True)
                    else:
                        st.warning(f"⚠️ {result.get('message', 'No invoices found')}")
                else:
                    st.error(f"❌ Request failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def test_email_generation():
    st.header("📧 Email Generation Test")
    st.markdown("Testing email generation for properties with overages")
    
    # Check if we have calculation data
    if "calculation_data" not in st.session_state:
        st.warning("⚠️ Please run the Monthly Calculation test first to get property data.")
        return
    
    # Property selection
    overages = [p for p in st.session_state.calculation_data["properties"] if p["total_extra"] > 0]
    
    if not overages:
        st.success("🎉 No properties with overages found!")
        return
    
    property_options = {f"{p['name']} (€{p['total_extra']:.2f})": p['name'] for p in overages}
    selected_property = st.selectbox("Select Property with Overages", list(property_options.keys()))
    property_name = property_options[selected_property]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📧 Email Generation Process")
        st.markdown("""
        This test generates personalized emails for properties with overages:
        1. **Invoice Download**: Downloads electricity and water invoices
        2. **Template Processing**: Uses email templates from Excel file
        3. **Personalization**: Generates personalized subject and body
        4. **Approval Queue**: Queues email for manual approval
        """)
    
    with col2:
        if st.button("📧 Generate Email", type="primary"):
            with st.spinner(f"Generating email for {property_name}..."):
                try:
                    response = requests.post(f"{BASE_URL}/api/email/generate", json={
                        "property_name": property_name,
                        "require_approval": True
                    })
                    if response.status_code == 200:
                        result = response.json()
                        if result["success"]:
                            st.success("✅ Email generated successfully!")
                            
                            # Display email details
                            st.markdown("#### 📧 Email Details")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Email ID", result.get("email_id", "N/A"))
                                st.metric("Status", result.get("status", "N/A"))
                            
                            with col2:
                                st.metric("Total Extra", f"€{result.get('total_extra', 0):.2f}")
                                st.metric("Invoice Downloaded", "✅" if result.get("invoice_downloaded") else "❌")
                            
                            # Store email ID for approval workflow
                            st.session_state.last_email_id = result.get("email_id")
                        else:
                            st.error(f"❌ Email generation failed: {result.get('message', 'Unknown error')}")
                    else:
                        st.error(f"❌ Request failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def test_email_approval_workflow():
    st.header("⏳ Email Approval Workflow Test")
    st.markdown("Testing the email approval and sending process")
    
    # Get pending approvals
    with st.spinner("Loading pending approvals..."):
        try:
            response = requests.get(f"{BASE_URL}/api/email/pending-approvals")
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    pending_emails = result["emails"]
                    
                    if not pending_emails:
                        st.info("ℹ️ No emails pending approval")
                        return
                    
                    st.success(f"✅ Found {len(pending_emails)} emails pending approval")
                    
                    # Display pending emails
                    for i, email in enumerate(pending_emails):
                        with st.expander(f"📧 Email {i+1}: {email['preview']['property_name']}"):
                            preview = email["preview"]
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📋 Email Details")
                                st.write(f"**Property:** {preview['property_name']}")
                                st.write(f"**Email:** {preview['email_address']}")
                                st.write(f"**Subject:** {preview['subject']}")
                                st.write(f"**Total Extra:** €{preview['total_extra']:.2f}")
                            
                            with col2:
                                st.markdown("#### ⚡ Actions")
                                col_approve, col_reject = st.columns(2)
                                
                                with col_approve:
                                    if st.button(f"✅ Approve", key=f"approve_{i}"):
                                        approve_email(email["email_id"])
                                
                                with col_reject:
                                    if st.button(f"❌ Reject", key=f"reject_{i}"):
                                        reject_email(email["email_id"])
                else:
                    st.error("❌ Failed to load pending approvals")
            else:
                st.error(f"❌ Request failed: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Show sent emails
    st.markdown("---")
    st.markdown("### 📤 Sent Emails")
    
    if st.button("📋 Load Sent Emails"):
        with st.spinner("Loading sent emails..."):
            try:
                response = requests.get(f"{BASE_URL}/api/email/sent")
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        sent_emails = result["emails"]
                        
                        if not sent_emails:
                            st.info("ℹ️ No emails sent yet")
                        else:
                            st.success(f"✅ Found {len(sent_emails)} sent emails")
                            
                            # Display sent emails
                            sent_df = pd.DataFrame(sent_emails)
                            st.dataframe(sent_df, use_container_width=True)
                    else:
                        st.error("❌ Failed to load sent emails")
                else:
                    st.error(f"❌ Request failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def approve_email(email_id):
    """Approve an email."""
    try:
        response = requests.post(f"{BASE_URL}/api/email/approve", json={
            "email_id": email_id,
            "action": "approve"
        })
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                st.success("✅ Email approved and sent!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ Approval failed: {result.get('message', 'Unknown error')}")
        else:
            st.error(f"❌ Request failed: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_email(email_id):
    """Reject an email."""
    reason = st.text_input("Rejection reason:", key=f"reject_reason_{email_id}")
    if st.button("Confirm Rejection", key=f"confirm_reject_{email_id}"):
        try:
            response = requests.post(f"{BASE_URL}/api/email/approve", json={
                "email_id": email_id,
                "action": "reject",
                "reason": reason or "Rejected by operator"
            })
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    st.success("✅ Email rejected!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Rejection failed: {result.get('message', 'Unknown error')}")
            else:
                st.error(f"❌ Request failed: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def test_statistics():
    st.header("📈 System Statistics")
    st.markdown("View email and invoice system statistics")
    
    if st.button("📊 Load Statistics", type="primary"):
        with st.spinner("Loading statistics..."):
            try:
                response = requests.get(f"{BASE_URL}/api/email/statistics")
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        st.success("✅ Statistics loaded successfully!")
                        
                        email_stats = result["email_statistics"]
                        invoice_stats = result["invoice_statistics"]
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📧 Email Statistics")
                            st.metric("Total Emails", email_stats["total_emails"])
                            st.metric("Sent Emails", email_stats["sent_emails"])
                            st.metric("Pending Approvals", email_stats["pending_approvals"])
                            st.metric("Mode", "Offline (Testing)" if email_stats["offline_mode"] else "Production")
                        
                        with col2:
                            st.markdown("#### 📄 Invoice Statistics")
                            st.metric("Total Properties", invoice_stats["total_properties"])
                            st.metric("Total Invoices", invoice_stats["total_invoices"])
                            st.metric("Electricity Invoices", invoice_stats["electricity_invoices"])
                            st.metric("Water Invoices", invoice_stats["water_invoices"])
                        
                        # Display raw data
                        st.markdown("#### 📋 Raw Statistics Data")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.json(email_stats)
                        
                        with col2:
                            st.json(invoice_stats)
                    else:
                        st.error("❌ Failed to load statistics")
                else:
                    st.error(f"❌ Request failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_web_interface():
    st.header("🌐 Web Interface")
    st.markdown("Access the full web interface for comprehensive testing")
    
    st.markdown("### 🔗 Web Interface Link")
    st.markdown(f"**URL:** [http://localhost:8000](http://localhost:8000)")
    
    st.markdown("### 🎯 Web Interface Features")
    st.markdown("""
    The web interface provides:
    - **📊 Dashboard**: Visual overview of utility costs and overages
    - **📋 Tables**: Detailed property data and overage calculations
    - **📈 Charts**: Visual representation of cost distribution
    - **📧 Email Management**: Full email workflow with approval system
    - **📥 Export**: CSV and Excel export functionality
    - **🧪 Testing**: Real invoice download testing
    """)
    
    st.markdown("### 🚀 Quick Start Guide")
    st.markdown("""
    1. **Calculate Report**: Click "Calculate Monthly Report" to test the improved scraper logic
    2. **View Results**: Check the Overview and Overages tabs for processed data
    3. **Email Management**: Go to Email Management tab to test invoice downloading
    4. **Test Real Downloads**: Use "Test Real Invoice Download" for actual Polaroo testing
    5. **Export Data**: Use the Export tab to download results
    """)
    
    if st.button("🌐 Open Web Interface", type="primary"):
        st.markdown("Opening web interface in new tab...")
        st.markdown(f'<meta http-equiv="refresh" content="0; url=http://localhost:8000">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
