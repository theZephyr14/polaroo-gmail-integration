# Gmail Draft Generator

A comprehensive solution for creating Gmail drafts with PDF attachments for utility bill management.

## 🚀 Features

- **Draft Creation**: Creates Gmail drafts instead of sending emails directly
- **PDF Attachments**: Automatically attaches PDFs from Supabase storage
- **Batch Processing**: Handle multiple recipients from Excel files
- **Template System**: Personalized email content generation
- **Manual Review**: Review and edit drafts before sending
- **Gmail API Integration**: Reliable API-based approach

## 📁 Files Created

1. **`gmail_draft_generator.py`** - Core draft generator for single recipients
2. **`gmail_batch_draft_generator.py`** - Batch processing from Excel files
3. **`run_draft_generator.py`** - User-friendly menu interface

## 🔧 Setup Requirements

### 1. Install Python Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pandas requests
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json` to project folder

### 3. File Structure

```
your-project/
├── gmail_draft_generator.py          # Core draft generator
├── gmail_batch_draft_generator.py    # Batch processing
├── run_draft_generator.py           # Menu interface
├── credentials.json                 # Gmail API credentials
├── Book1.xlsx                      # Recipient data (for batch mode)
├── token.json                      # Auto-generated OAuth token
└── src/
    └── pdf_storage.py              # Existing PDF storage system
```

## 📊 Excel File Format (for batch mode)

**Required columns:**
- `property_name`: Name of the property
- `email_address`: Recipient email address

**Optional columns:**
- `total_extra`: Amount owed
- `electricity_amount`: Electricity bill amount
- `water_amount`: Water bill amount
- `notes`: Additional notes

## 🎯 Usage

### Option 1: Menu Interface (Recommended)
```bash
python run_draft_generator.py
```

### Option 2: Single Draft
```bash
python gmail_draft_generator.py
```

### Option 3: Batch Drafts
```bash
python gmail_batch_draft_generator.py
```

## 🔄 How It Works

1. **Authentication**: Uses OAuth 2.0 to authenticate with Gmail API
2. **PDF Download**: Downloads relevant PDFs from Supabase storage
3. **Draft Creation**: Creates Gmail drafts with:
   - Personalized subject and content
   - PDF attachments
   - Proper recipient information
4. **Manual Review**: User can review/edit drafts in Gmail before sending

## ✅ Advantages Over Browser Automation

- **More Reliable**: No browser dependencies or UI changes
- **Faster**: Direct API calls, no page loading
- **Secure**: Official OAuth authentication
- **No Captchas**: Google recognizes legitimate API usage
- **Better Error Handling**: Proper API responses
- **Draft Review**: Manual control before sending

## 🛠️ Troubleshooting

### Gmail API Not Available
- Install required packages: `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
- Check credentials.json file exists

### Pandas Not Available (for batch mode)
- Install pandas: `pip install pandas`

### No PDFs Found
- Check Supabase configuration in `src/pdf_storage.py`
- Verify property name matches Supabase records

### OAuth Issues
- Delete `token.json` and re-authenticate
- Check OAuth consent screen configuration
- Ensure Gmail API is enabled

## 🔗 Integration with Existing System

This solution integrates with your existing codebase:
- Uses `src/pdf_storage.py` for PDF management
- Compatible with existing email templates
- Maintains same property naming conventions
- Works with current Supabase setup

## 💡 Next Steps

1. Run `python run_draft_generator.py` to start
2. Complete Gmail API setup if needed
3. Test with a single recipient first
4. Use batch mode for multiple recipients
5. Review all drafts in Gmail before sending

## 🔒 Security Notes

- OAuth tokens are stored locally in `token.json`
- Credentials are handled by Google's official libraries
- No passwords or sensitive data in code
- Drafts are created in your Gmail account for review
