# 🎯 **Complete User Journey Guide**
## Polaroo Gmail Integration System

---

## 📋 **System Overview**

This system automatically:
1. **Downloads** utility reports from Polaroo (3 months of data)
2. **Calculates** overages based on water billing cycles (Jul-Aug for September)
3. **Generates** Gmail drafts with PDF invoices for properties with overages
4. **Manages** recipients from Book1.xlsx (TO/CC functionality)

---

## 🚀 **Step-by-Step User Journey**

### **Step 1: User Opens the Web Application**

**👤 What User Sees:**
- Clean, professional dashboard with "Polaroo Utility Calculator" title
- Bootstrap-styled interface with navigation tabs
- "Calculate Monthly Report" button prominently displayed
- Empty tables waiting for data

**🔧 What Happens in Background:**
```
🌐 FastAPI server loads at https://polaroo-gmail-integration.onrender.com
📂 Static files served from src/static/index.html
🔗 API endpoints initialized and ready
📊 localStorage checked for previous calculation data
```

---

### **Step 2: User Clicks "Calculate Monthly Report"**

**👤 What User Sees:**
- Button changes to "Calculating..." with loading spinner
- Progress indicator appears
- Status messages show calculation progress

**🔧 What Happens in Background:**
```
🚀 [API] Starting monthly calculation request...
📥 [API] Step 1/3: Downloading report from Polaroo...

🧠 [SMART_DATE] Using intelligent water billing cycle logic...
🚰 [WATER_CYCLE] Current water billing cycle: Jul-Aug (Months: [7, 8])
💡 [SMART_LOGIC] Will download 3 months data and focus on Jul-Aug billing cycle

🌐 [BROWSER] Launching browser...
🥷 [STEALTH] Adding anti-detection measures...
🔐 [STEP 1/4] Starting login process...
```

---

### **Step 3: Polaroo Scraping Process**

**👤 What User Sees:**
- "Downloading report from Polaroo..." message
- May take 30-60 seconds

**🔧 What Happens in Background:**
```
🌐 [LOGIN] Navigated to: https://app.polaroo.com/login
📧 [LOGIN] Filling email...
🔑 [LOGIN] Filling password...
✅ [LOGIN] Sign in button clicked, waiting for redirect...
✅ [DASHBOARD] Dashboard fully loaded!

📊 [STEP 2/4] Opening Report page...
✅ [REPORT] Successfully navigated to Report page

📅 [STEP 3/4] Setting smart date range for water billing cycle...
📅 [SIMPLE_DATE] Trying to select 'Last 3 Months'...
✅ [SMART_DATE] Successfully set to 'Last 3 Months'

📥 [STEP 4/4] Starting download process...
✅ [DOWNLOAD] Found visible Download button, clicking...
✅ [DOWNLOAD] Download menu opened successfully!
💾 [SAVED] polaroo_report_20250908T104753Z.xlsx (1.2MB)
☁️ [UPLOAD] Uploading to Supabase...
```

---

### **Step 4: Data Processing & Water Cycle Logic**

**👤 What User Sees:**
- "Processing data..." message
- Smart filtering being applied

**🔧 What Happens in Background:**
```
✅ [API] Report downloaded: polaroo_report_20250908T104753Z.xlsx (1,234,567 bytes)
🚰 [WATER_CYCLE] Filtering data for Jul-Aug billing cycle
💡 [SMART_LOGIC] Downloaded 3 months data, will focus on Jul-Aug period

📊 [API] Step 2/3: Processing Excel data...
📈 [EXCEL] Reading Excel file with pandas...
🏠 [PROPERTIES] Found 145 properties in report
📋 [BOOK1] Loading Book1.xlsx for property filtering...
✅ [BOOK1] Found 12 properties matching Book1.xlsx

🧮 [CALCULATION] Calculating overages for Jul-Aug billing cycle...
💰 [OVERAGES] Found 5 properties with overages:
   - Aribau 1º 1ª: €133.76 overage
   - Property 2: €45.30 overage
   - Property 3: €67.89 overage
```

---

### **Step 5: Results Display**

**👤 What User Sees:**
- **Summary Tab**: 
  - Total properties: 12
  - Properties with overages: 5
  - Total overage amount: €247.95
  - Calculation date and time
  - "Last calculated X minutes ago" (persists on reload)

- **Properties Tab**:
  - Table showing all 12 properties from Book1.xlsx
  - Columns: Property Name, Electricity Cost, Water Cost, Total Extra, Allowance
  - Color-coded rows (red for overages)

- **Overages Tab**:
  - Filtered table showing only 5 properties with overages
  - **Clickable property names** (cursor changes to pointer)
  - **"Gmail Draft" buttons** in Actions column

**🔧 What Happens in Background:**
```
📊 [API] Total properties processed: 145
📊 [API] Book1 properties found: 12
📊 [API] Book1 property names: ["Aribau 1º 1ª", "Property 2", ...]
✅ [API] Calculation completed successfully!

💾 [FRONTEND] Saving calculation results to localStorage
⏰ [FRONTEND] Setting 24-hour expiry timestamp
🎨 [FRONTEND] Rendering tables with Bootstrap styling
🔄 [FRONTEND] Data persists even if page is refreshed
```

---

### **Step 6: User Clicks Property Name (Option 1)**

**👤 What User Sees:**
- New browser tab opens
- Gmail draft creation page loads
- Property-specific interface

**🔧 What Happens in Background:**
```
🆕 [FRONTEND] Opening new tab: /gmail-draft?property=Aribau 1º 1ª
📄 [API] Serving gmail_draft.html
🔍 [API] Property parameter received: "Aribau 1º 1ª"
📊 [API] Loading property data from latest calculation results
```

---

### **Step 7: User Clicks "Gmail Draft" Button (Option 2)**

**👤 What User Sees:**
- "Creating Gmail draft..." loading message
- Progress indicators
- Success message with draft details

**🔧 What Happens in Background:**
```
📧 [GMAIL_DRAFT] Creating Gmail draft for Aribau 1º 1ª...
📋 [BOOK1] Loading recipients from Book1.xlsx...
✅ [BOOK1] Found 1 emails for 'Aribau 1º 1ª'
   - TO: kevinparakh@yahoo.co.uk

📎 [PDF_DOWNLOAD] Downloading PDFs from Supabase...
📄 [PDF] Found 3 relevant invoices:
   - electricity_jul_2025.pdf
   - electricity_aug_2025.pdf  
   - water_jul_aug_2025.pdf

🔐 [GMAIL_API] Setting up Gmail API connection...
✅ [GMAIL_API] Credentials validated
📝 [GMAIL_API] Creating draft email...
```

---

### **Step 8: Gmail Draft Creation**

**👤 What User Sees:**
- Success message: "Gmail draft created successfully!"
- Draft details:
  - Property: Aribau 1º 1ª
  - Recipient: kevinparakh@yahoo.co.uk
  - Attachments: 3 PDF files
  - Gmail URL link provided
- "Open Gmail Drafts" button

**🔧 What Happens in Background:**
```
📧 [EMAIL_CONTENT] Generating personalized email:
   Subject: "Utility Bill Overage - Aribau 1º 1ª - Jul-Aug 2025"
   
   Body:
   "Dear Property Manager,
   
   This property has exceeded the utility allowance for Jul-Aug 2025:
   - Total Overage: €133.76
   - Billing Period: Jul-Aug 2025
   - Water Billing Cycle: Complete
   
   Please find attached invoices for review.
   
   Best regards,
   Polaroo Utility Management"

📎 [ATTACHMENTS] Attaching 3 PDF files to draft
✅ [GMAIL_DRAFT] Draft created with ID: draft_abc123xyz
🔗 [GMAIL_URL] Draft accessible at: https://mail.google.com/mail/u/0/#drafts/draft_abc123xyz

🧹 [CLEANUP] Removing temporary PDF files
📊 [RESPONSE] Returning success response to frontend
```

---

### **Step 9: User Opens Gmail**

**👤 What User Sees:**
- Gmail opens in new tab/window
- Draft email is ready in Drafts folder
- Email has:
  - Professional subject line
  - Personalized content with overage details
  - 3 PDF attachments (electricity + water invoices)
  - Recipient pre-filled (TO: kevinparakh@yahoo.co.uk)

**🔧 What Happens in Background:**
```
🌐 [GMAIL] User navigates to Gmail drafts
📧 [GMAIL] Draft email loads with all content
📎 [GMAIL] PDF attachments ready for download/preview
✅ [READY] User can review, edit, and send the email
```

---

### **Step 10: Data Persistence & Reload**

**👤 What User Sees:**
- If user refreshes the main page, all data remains
- "Last calculated 15 minutes ago" message
- All tables and calculations preserved
- No need to recalculate

**🔧 What Happens in Background:**
```
💾 [FRONTEND] localStorage.getItem('polaroo_calculation_data')
⏰ [FRONTEND] Checking timestamp: within 24-hour window
📊 [FRONTEND] Restoring calculation results
🎨 [FRONTEND] Re-rendering all tables and summaries
✅ [PERSISTENT] Full functionality maintained without re-scraping
```

---

## 🎯 **Key Features Demonstrated**

### **1. Smart Water Cycle Logic**
- **Current Month**: September 2025
- **Target Billing Cycle**: Jul-Aug 2025 (most recent complete cycle)
- **Download Strategy**: Last 3 months data → Filter to Jul-Aug period

### **2. Intelligent Date Selection**
- **Primary**: Try "Last 3 Months" option (simple)
- **Fallback**: Try "Last Month" option  
- **Final Fallback**: Custom date range with calendar interface

### **3. Data Persistence**
- **localStorage**: 24-hour cache of calculation results
- **Auto-restore**: Page reloads don't lose data
- **Timestamp**: Shows when data was last calculated

### **4. Email Management**
- **Book1.xlsx Integration**: Automatic recipient lookup
- **TO/CC Logic**: Primary recipient + additional CCs
- **PDF Attachments**: Relevant invoices automatically attached
- **Professional Templates**: Branded email content

### **5. Error Handling**
- **Scraper Failures**: Clear error messages (no mock data)
- **Missing Recipients**: Graceful fallbacks
- **PDF Issues**: Continues without attachments if needed
- **API Failures**: User-friendly error messages

---

## 🔧 **Technical Architecture**

### **Frontend (src/static/index.html)**
- **Bootstrap 5**: Professional UI framework
- **Chart.js**: Data visualization
- **localStorage**: Client-side data persistence
- **Async JavaScript**: Non-blocking API calls

### **Backend (src/api.py)**
- **FastAPI**: Modern Python web framework
- **Playwright**: Browser automation for Polaroo
- **pandas**: Excel data processing
- **Gmail API**: Draft creation and management

### **Data Flow**
```
User → Frontend → FastAPI → Playwright → Polaroo → Excel Processing → 
Water Cycle Logic → Book1.xlsx → Gmail API → Draft Creation → User
```

---

## 🎉 **Success Metrics**

✅ **Automated**: No manual data entry required  
✅ **Intelligent**: Smart water billing cycle detection  
✅ **Persistent**: Data survives page reloads  
✅ **Professional**: Branded email templates  
✅ **Efficient**: Bulk processing with individual customization  
✅ **User-Friendly**: One-click draft generation  
✅ **Robust**: Comprehensive error handling  

---

**🚀 The system is now production-ready and deployed at:**
**https://polaroo-gmail-integration.onrender.com**
