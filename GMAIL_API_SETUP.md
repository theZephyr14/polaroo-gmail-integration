# Gmail API Setup Guide

## 🎯 **Why Use Gmail API Instead of Browser Automation?**

✅ **More Reliable** - No browser dependencies or UI changes
✅ **Faster** - Direct API calls, no loading pages
✅ **Secure** - Official OAuth authentication
✅ **No Captchas** - Google recognizes legitimate API usage
✅ **Better Error Handling** - Proper API responses
✅ **Rate Limiting** - Built-in quota management

## 🔧 **Setup Steps**

### 1. Install Required Packages
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Name it something like "Email Automation"

### 3. Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on it and press **Enable**

### 4. Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ Create Credentials** > **OAuth client ID**
3. Choose **Desktop application**
4. Name it "Email Bot"
5. Download the JSON file
6. Rename it to `credentials.json` and put it in your project folder

### 5. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace)
3. Fill in the required fields:
   - App name: "Email Automation Bot"
   - User support email: Your email
   - Developer contact: Your email
4. Add your email to **Test users** section
5. Save

## 🚀 **Running the Demo**

```bash
python gmail_api_demo.py
```

### First Run:
1. Browser will open for OAuth consent
2. Log in with your Gmail account
3. Grant permissions to send emails
4. Token will be saved for future runs

### Subsequent Runs:
- No browser needed!
- Uses saved token automatically
- Refreshes token if expired

## 📁 **File Structure**
```
your-project/
├── gmail_api_demo.py          # Main demo script
├── credentials.json           # OAuth credentials (download from Google)
├── token.json                 # Auto-generated token (don't commit to git)
├── email_templates.xlsx       # Email templates
└── src/email_system/          # Email generation system
```

## 🔒 **Security Notes**

- **Never commit `credentials.json` or `token.json` to version control**
- Add them to `.gitignore`
- Use environment variables for production
- Consider using service accounts for server deployments

## 🎛️ **Configuration Options**

### Dry Run Mode (Default)
```python
demo.run_demo(dry_run=True)  # Test without sending
```

### Live Mode
```python
demo.run_demo(dry_run=False)  # Actually send emails
```

### Custom Sender
```python
demo.run_demo(sender_email="kevin@nodeliving.es")
```

## 📊 **Rate Limits**

Gmail API has generous quotas:
- **250 quota units per user per second**
- **1 billion quota units per day**
- Sending an email = 100 quota units
- **~10 million emails per day** (theoretical max)

## 🐛 **Troubleshooting**

### "credentials.json not found"
- Download OAuth credentials from Google Cloud Console
- Make sure file is named exactly `credentials.json`

### "Access blocked" during OAuth
- Add your email to test users in OAuth consent screen
- Make sure Gmail API is enabled

### "Token expired"
- Delete `token.json` and run again
- Will re-authenticate automatically

### "Quota exceeded"
- Very unlikely with normal usage
- Check quotas in Google Cloud Console

## 🔄 **Alternative: Service Account (For Production)**

For server deployments, consider using a service account:

1. Create service account in Google Cloud Console
2. Enable domain-wide delegation
3. Use service account key instead of OAuth

This allows sending emails without user interaction.

## 📈 **Advantages Over Browser Automation**

| Feature | Browser Automation | Gmail API |
|---------|-------------------|-----------|
| Speed | Slow (5-10s per email) | Fast (<1s per email) |
| Reliability | Breaks with UI changes | Stable API |
| Authentication | Manual login required | OAuth token |
| Rate Limits | Risk of being blocked | Official quotas |
| Error Handling | Hard to detect failures | Proper API responses |
| Maintenance | High (UI changes) | Low (stable API) |

## 🎉 **Ready to Use!**

Once set up, the Gmail API approach is much more professional and reliable than browser automation. Perfect for production use!
