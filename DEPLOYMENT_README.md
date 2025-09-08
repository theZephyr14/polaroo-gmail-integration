# 🚀 Polaroo Gmail Integration System - Production Deployment

## 📋 **System Overview**

This is the integrated Polaroo Utility Bill Calculator with Gmail Draft Generator functionality. The system provides:

- **Web Interface**: Beautiful dashboard for utility bill calculations
- **Gmail Integration**: One-click Gmail draft creation with PDF attachments
- **Data Persistence**: Calculations survive page reloads
- **Book1.xlsx Integration**: Multiple recipient support with CC functionality
- **PDF Attachments**: Automatic invoice downloads from Supabase

## 🌐 **Live Deployment**

- **Production URL**: [Your Render URL will be here]
- **Health Check**: `/api/health`
- **Main Interface**: `/`
- **Gmail Draft Interface**: `/gmail-draft`

## 🔧 **Environment Setup**

### **Required Environment Variables**
None required for basic functionality.

### **Required Files for Gmail Integration**
- `credentials.json` - Gmail API OAuth credentials
- `Book1.xlsx` - Recipient email addresses

## 📊 **Key Features**

### **1. Persistent Calculations**
- Data saved to localStorage (24-hour expiry)
- Survives page reloads and browser sessions
- Shows calculation age in header

### **2. Enhanced Overages Tab**
- Clickable property names
- Dual email options (Old Email + Gmail Draft)
- Visual indicators for properties with overages

### **3. Gmail Draft Integration**
- One-click draft creation
- Automatic PDF attachments from Supabase
- Multiple recipients from Book1.xlsx
- New tab workflow for seamless experience

### **4. Book1.xlsx Integration**
Expected format:
```
| name         | rooms | mail                    |
|--------------|-------|-------------------------|
| Aribau 1º 1ª | 1.0   | kevinparakh@yahoo.co.uk |
| Aribau 1º 2ª | 1.0   | tenant2@example.com     |
```

## 🔗 **API Endpoints**

### **Core Functionality**
- `GET /` - Main web interface
- `POST /api/calculate` - Run monthly calculations
- `GET /api/results/latest` - Get latest calculation results
- `GET /api/health` - Health check

### **Gmail Integration**
- `POST /api/gmail/create-draft` - Create Gmail draft
- `POST /api/book1/emails` - Get recipients from Excel
- `GET /gmail-draft` - Gmail draft interface

### **Email Management**
- `POST /api/email/generate` - Generate email (old system)
- `GET /api/email/pending-approvals` - Get pending emails
- `POST /api/email/approve` - Approve/reject emails

## 🧪 **Testing the Live System**

### **1. Basic Functionality**
1. Visit the main URL
2. Click "Calculate Monthly Report"
3. Check Overview and Overages tabs
4. Refresh page to test persistence

### **2. Gmail Integration (Without Setup)**
1. Go to Overages tab
2. Click property name → New tab opens
3. Click "Gmail Draft" button → Shows credential error (expected)

### **3. Gmail Integration (With Setup)**
1. Upload `credentials.json` to Render
2. First OAuth setup will require manual browser interaction
3. Subsequent drafts created automatically

## 🔒 **Security Notes**

- Gmail API credentials not included in repository
- OAuth tokens handled securely by Google libraries
- No sensitive data exposed in client-side code
- CORS configured for production domains

## 📈 **Performance**

- **Frontend**: Bootstrap 5 + Vanilla JS (fast loading)
- **Backend**: FastAPI (high performance)
- **Storage**: localStorage for persistence
- **APIs**: Async/await for non-blocking operations

## 🛠️ **Maintenance**

### **Log Monitoring**
Check Render logs for:
- Gmail API errors
- PDF download issues
- Book1.xlsx parsing problems

### **Data Updates**
- Update Book1.xlsx for new recipients
- Refresh Gmail credentials when expired
- Monitor Supabase storage usage

## 🎯 **User Workflow**

1. **Access System** → Visit production URL
2. **Calculate Report** → Click "Calculate Monthly Report"
3. **View Overages** → Go to Overages tab
4. **Create Drafts** → Click property name or "Gmail Draft" button
5. **Review & Send** → Gmail opens with draft ready to send

## 🔄 **Deployment Updates**

To deploy updates:
1. Commit changes to Git
2. Push to GitHub
3. Render auto-deploys from main branch
4. Monitor deployment logs

---

**🎉 Ready for Production Use!**
