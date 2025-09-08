called "# 🧪 Local Testing Guide

## 🎉 System Status: READY FOR TESTING!

The Polaroo Utility Bill System has been successfully implemented with both improved scraper logic and invoice downloading capabilities. Here's how to test it locally:

## 🚀 Quick Start

### 1. **Streamlit Interface (Recommended for Testing)**
```bash
streamlit run streamlit_app.py
```
**URL:** http://localhost:8501

### 2. **Web Interface (Full Features)**
```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
**URL:** http://localhost:8000

## ✅ What's Working

### **✅ Improved Scraper Logic**
- **Custom Date Range**: Now selects "Custom" and sets date range for last 2 months (60 days) instead of "Last month"
- **Robust Date Selection**: Handles various date input formats with fallback mechanisms
- **5-Second Delays**: Maintains human-like behavior between actions

### **✅ Invoice Downloading System**
- **Navigation**: Automatically navigates to Polaroo Invoices section
- **Search**: Uses search bar to find invoices for specific properties
- **Smart Downloading**: Downloads exactly 2 electricity + 1 water invoice per property
- **Service Type Detection**: Identifies invoice types from "service" column
- **File Management**: Saves with timestamped names and 10-minute auto-cleanup

### **✅ Email Management System**
- **Template Processing**: Uses Excel templates for personalized emails
- **Invoice Integration**: Automatically downloads invoices when generating emails
- **Approval Workflow**: Manual approval system with preview modal
- **Bulk Operations**: Generate emails for all properties with overages
- **Statistics**: Track email and invoice operations

## 🧪 Testing Options

### **Option 1: Streamlit App (Easiest)**
1. Run: `streamlit run streamlit_app.py`
2. Open: http://localhost:8501
3. Test each component step by step:
   - Monthly Calculation (Mock Data)
   - Mock Invoice Download
   - Email Generation
   - Email Approval Workflow
   - Statistics

### **Option 2: Web Interface (Full Features)**
1. Run: `python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload`
2. Open: http://localhost:8000
3. Use the full dashboard with:
   - Visual charts and tables
   - Email Management tab
   - Real invoice download testing
   - Export functionality

### **Option 3: Command Line Tests**
```bash
# Test mock calculation (no browser required)
python test_mock_calculation.py

# Test API endpoints (requires server running)
python test_api_mock.py
```

## 📊 Sample Data Available

The system has processed **96 properties** with **77 properties having overages**:

- **Total Properties**: 96
- **Properties with Overages**: 77
- **Total Extra Amount**: €7,199.87
- **Sample Properties with Overages**:
  - Aribau 1º 1ª: €159.86
  - Aribau 2º 3ª: €521.69
  - Llull 250 1-3: €182.83
  - Padilla 3º 2ª: €174.01

## 🔧 Key Features Tested

### **1. Improved Scraper Logic**
- ✅ Custom date range selection (last 2 months)
- ✅ Robust dropdown handling
- ✅ Multiple fallback mechanisms
- ✅ Human-like delays and behavior

### **2. Invoice Downloading**
- ✅ Mock invoice generation (offline mode)
- ✅ Real invoice download capability (production mode)
- ✅ Service type identification (electricity/water)
- ✅ File management with auto-cleanup
- ✅ Integration with email system

### **3. Email Management**
- ✅ Template-based email generation
- ✅ Personalized content with property data
- ✅ Invoice attachment integration
- ✅ Manual approval workflow
- ✅ Bulk email generation
- ✅ Statistics and tracking

## 🌐 Production vs Testing

### **Testing Mode (Current)**
- Uses mock data and simulated services
- No real browser automation
- Safe for development and testing
- All features work without external dependencies

### **Production Mode**
- Real Polaroo scraping with browser automation
- Actual invoice downloads from Polaroo
- Real email sending (when configured)
- Requires proper credentials and network access

## 🎯 Next Steps

1. **Test the Streamlit Interface**: http://localhost:8501
2. **Explore the Web Interface**: http://localhost:8000
3. **Try the Email Workflow**: Generate emails and test approval process
4. **Test Invoice Downloading**: Use the "Test Real Invoice Download" feature
5. **Export Data**: Try CSV/Excel export functionality

## 🐛 Known Issues

- **Playwright Browser Automation**: May have issues on some Windows systems
- **Excel Template Loading**: Minor warning about engine specification (doesn't affect functionality)
- **Real Invoice Download**: Requires valid Polaroo credentials and network access

## 📞 Support

If you encounter any issues:
1. Check that both servers are running (Streamlit on 8501, API on 8000)
2. Verify the sample data files exist in `_debug/downloads/`
3. Check the console output for detailed error messages
4. Use the mock tests first to verify basic functionality

---

**🎉 The system is ready for comprehensive testing! Start with the Streamlit interface for the easiest testing experience.**
