# 🚀 Quick Deployment Guide

## **Why Not Streamlit?**

While your original Streamlit app works well for development, for **production hosting** we've created a more scalable solution:

### **Streamlit Limitations:**
- ❌ Resource intensive (runs full Python environment)
- ❌ Limited customization options
- ❌ Not ideal for production web applications
- ❌ Higher hosting costs

### **Our Solution Benefits:**
- ✅ **FastAPI Backend**: Lightweight, fast, production-ready
- ✅ **HTML Frontend**: Customizable, responsive, professional
- ✅ **Multiple Hosting Options**: Railway, Render, Heroku, etc.
- ✅ **Cost Effective**: Lower resource requirements
- ✅ **Scalable**: Can handle multiple users efficiently

## **🏆 Recommended: Railway (Easiest)**

```bash
# 1. Run the deployment script
./deploy.sh

# 2. Choose option 1 (Railway)
# 3. Follow the prompts
```

**Why Railway?**
- 🚀 **Zero configuration** - detects settings automatically
- 💰 **Free tier** available
- 🔄 **Auto-deploy** from GitHub
- 📊 **Built-in monitoring**
- 🔒 **Secure environment variables**

## **🎨 Alternative: Render**

```bash
# 1. Go to https://render.com
# 2. Connect your GitHub repo
# 3. Create Web Service
# 4. Use these settings:
Build Command: pip install -r requirements.txt && playwright install chromium && playwright install-deps
Start Command: uvicorn src.api:app --host 0.0.0.0 --port $PORT
```

## **🦸 Heroku (Legacy)**

```bash
# 1. Install Heroku CLI
# 2. Run: ./deploy.sh
# 3. Choose option 3
```

## **🔧 Environment Variables**

Set these in your hosting platform:

```env
POLAROO_EMAIL=your_email@example.com
POLAROO_PASSWORD=your_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
STORAGE_BUCKET=polaroo
```

## **📱 What Your Ops Team Will See**

1. **Professional Web Interface** at your hosted URL
2. **Sidebar Configuration** for allowances
3. **One-Click Calculation** button
4. **Real-time Results** with charts and tables
5. **Export Options** for CSV/Excel reports

## **⚡ Quick Start**

```bash
# Clone and deploy in 5 minutes:
git clone <your-repo>
cd polaroo-ingest
./deploy.sh
# Choose Railway (option 1)
# Set environment variables
# Done! 🎉
```

## **🔗 Your App URL**

After deployment, your ops team can access:
- **Railway**: `https://your-app-name.railway.app`
- **Render**: `https://your-app-name.onrender.com`
- **Heroku**: `https://your-app-name.herokuapp.com`

## **📊 Monthly Workflow**

1. **Ops team visits** your hosted URL
2. **Adjusts allowances** if needed (€100 electricity, €50 water)
3. **Clicks "Calculate Monthly Report"**
4. **Waits 30-60 seconds** for processing
5. **Reviews results** in multiple views
6. **Exports reports** for billing

## **🛠️ Support**

- **Logs**: Check your hosting platform's dashboard
- **Issues**: Verify environment variables
- **Updates**: Push to GitHub for auto-deploy

---

**🎯 Result**: Professional, scalable web application that your ops team can use monthly without any technical knowledge!

