# 🧪 Offline Email System Testing

This document explains how to test the new email and invoice management system in offline mode.

## 🎯 What's New

The system now includes:

1. **Email Generation System** - Creates personalized emails for utility bill overages
2. **Invoice Download System** - Downloads electricity and water invoices (simulated in offline mode)
3. **Email Approval Workflow** - Manual approval process for sending emails
4. **Email Management UI** - New tab in the web interface for managing emails

## 🚀 Quick Start

### 1. Run the System

```bash
python run_offline_system.py
```

This will start the web server at `http://localhost:8000`

### 2. Test the Email System

1. **Calculate Report**: Click "Calculate Monthly Report" to process utility data
2. **View Overages**: Go to the "Overages" tab to see properties with overages
3. **Create Emails**: 
   - Click "Create Email" button next to any property with overages
   - Or click "Generate All Emails" in the Email Management tab
4. **Approve Emails**: Go to "Email Management" tab → "Pending Approvals" → Preview and approve emails

## 📧 Email Workflow

### Step 1: Generate Emails
- System identifies properties with overages
- Downloads mock invoices for each property
- Generates personalized emails using templates

### Step 2: Email Approval
- Emails are queued for manual approval
- Ops team can preview each email
- Click "Approve & Send" or "Reject" with reason

### Step 3: Email Sending
- Approved emails are sent (simulated in offline mode)
- System tracks email status and statistics

## 🛠️ System Components

### Backend Components

- **`src/email_system/email_generator.py`** - Generates personalized emails
- **`src/email_system/invoice_downloader.py`** - Downloads invoices (offline simulation)
- **`src/email_system/email_sender.py`** - Handles email sending and approval
- **`src/email_system/template_manager.py`** - Manages email templates

### API Endpoints

- `POST /api/email/generate` - Generate email for specific property
- `POST /api/email/generate-bulk` - Generate emails for all overages
- `GET /api/email/pending-approvals` - Get emails pending approval
- `POST /api/email/approve` - Approve or reject email
- `GET /api/email/sent` - Get sent emails
- `GET /api/email/statistics` - Get system statistics

### Frontend Features

- **Email Management Tab** - New tab for managing email operations
- **Property Selection** - Clickable "Create Email" buttons in overages table
- **Email Preview Modal** - Full email preview before sending
- **Approval Workflow** - Approve/reject interface for ops team

## 📁 File Structure

```
├── email_templates.xlsx          # Email templates and tenant contacts
├── src/email_system/             # Email system components
│   ├── __init__.py
│   ├── email_generator.py
│   ├── invoice_downloader.py
│   ├── email_sender.py
│   └── template_manager.py
├── src/api.py                    # Enhanced with email endpoints
├── src/static/index.html         # Enhanced with email management UI
├── test_email_system.py          # Test script for email components
├── run_offline_system.py         # System startup script
└── _debug/invoices/              # Mock invoice storage
```

## 🧪 Testing

### Run Component Tests

```bash
python test_email_system.py
```

This tests all email system components individually.

### Manual Testing Workflow

1. **Start System**: `python run_offline_system.py`
2. **Open Browser**: Go to `http://localhost:8000`
3. **Calculate Report**: Click "Calculate Monthly Report"
4. **Test Email Generation**: 
   - Go to "Overages" tab
   - Click "Create Email" for any property
   - Go to "Email Management" tab
   - Click "Pending Approvals"
   - Preview and approve emails
5. **Check Statistics**: Click "Statistics" to see system metrics

## 📊 Features in Offline Mode

### What Works
- ✅ Email generation with templates
- ✅ Mock invoice downloads
- ✅ Email approval workflow
- ✅ Email preview and management
- ✅ Statistics and tracking
- ✅ 5-second delays between operations
- ✅ Error handling and recovery

### What's Simulated
- 🔄 Email sending (no actual emails sent)
- 🔄 Invoice downloads (creates mock PDF files)
- 🔄 Payment links (example URLs)
- 🔄 SMTP configuration (not used in offline mode)

## 🔧 Configuration

### Email Templates

Edit `email_templates.xlsx` to:
- Add new properties and email addresses
- Customize email subjects and body templates
- Update tenant contact information

### System Settings

The system runs in offline mode by default. To enable production features:

1. Set `offline_mode=False` in the email system components
2. Configure SMTP settings in `EmailSender`
3. Implement real Polaroo invoice downloading
4. Set up Supabase for invoice storage

## 🚨 Troubleshooting

### Common Issues

1. **"No calculation results available"**
   - Run "Calculate Monthly Report" first
   - Ensure you have sample data in `_debug/downloads/`

2. **"No template found for property"**
   - Check `email_templates.xlsx` has the property name
   - System will use default template if property not found

3. **"Email generation failed"**
   - Check property has overages (total_extra > 0)
   - Verify template file exists and is readable

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export PYTHONPATH=src
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## 📈 Next Steps

1. **Test with Real Data**: Use actual Polaroo reports
2. **Configure SMTP**: Set up real email sending
3. **Database Integration**: Connect to Supabase for persistence
4. **Production Deployment**: Deploy to Railway/Render
5. **User Training**: Train ops team on approval workflow

## 🎉 Success Criteria

The system is working correctly when:

- ✅ Properties with overages show "Create Email" buttons
- ✅ Emails are generated with correct calculations
- ✅ Email preview shows proper content and attachments
- ✅ Approval workflow allows approve/reject actions
- ✅ Statistics show correct counts and metrics
- ✅ 5-second delays work between bulk operations
- ✅ Error handling works for edge cases

---

**Ready to test?** Run `python run_offline_system.py` and start exploring! 🚀
