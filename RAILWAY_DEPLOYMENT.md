# 🚂 Railway Deployment Instructions

## ✅ Code is Ready!

Your utility bill calculator is now **Railway-ready**! Here's what we've accomplished:

### **Fixed Issues:**
- ✅ **Import errors** - Fixed all relative imports
- ✅ **Dependencies** - Added missing `requests` library
- ✅ **Dockerfile** - Optimized for Railway deployment
- ✅ **Railway config** - Proper `railway.json` setup
- ✅ **Static files** - HTML frontend properly configured
- ✅ **Git ignore** - Excludes unnecessary files

### **Files Created/Updated:**
- `src/api.py` - FastAPI backend (fixed imports)
- `src/static/index.html` - Professional web frontend
- `Dockerfile` - Railway-optimized container
- `railway.json` - Railway deployment config
- `requirements.txt` - All dependencies included
- `.gitignore` - Proper exclusions

## 🚀 Deploy to Railway (2 Options)

### **Option 1: Railway CLI (Recommended)**

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Initialize Git (if not done):**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Utility Bill Calculator"
   ```

3. **Deploy to Railway:**
   ```bash
   railway login
   railway init
   railway up
   ```

4. **Set Environment Variables in Railway Dashboard:**
   ```
   POLAROO_EMAIL=your_email@example.com
   POLAROO_PASSWORD=your_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   STORAGE_BUCKET=polaroo
   ```

### **Option 2: Railway Web Interface**

1. **Push to GitHub:**
   - Create a GitHub repository
   - Push your code: `git push origin main`

2. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables:**
   - In Railway dashboard, go to Variables tab
   - Add all required environment variables

## 🔧 Environment Variables Required

Set these in Railway dashboard:

```env
POLAROO_EMAIL=your_email@example.com
POLAROO_PASSWORD=your_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
STORAGE_BUCKET=polaroo
```

## 📱 What Your Ops Team Will Get

After deployment, your ops team will have:

1. **Professional Web Interface** at `https://your-app.railway.app`
2. **One-Click Calculation** - Just click "Calculate Monthly Report"
3. **Real-time Results** - Beautiful charts and tables
4. **Export Options** - CSV and Excel downloads
5. **Mobile Friendly** - Works on all devices

## 🎯 Monthly Workflow

1. **Ops team visits** your Railway URL
2. **Adjusts allowances** if needed (€100 electricity, €50 water)
3. **Clicks "Calculate Monthly Report"**
4. **Waits 30-60 seconds** for automated processing
5. **Reviews results** in multiple views
6. **Exports reports** for billing

## 🛠️ Troubleshooting

If deployment fails:

1. **Check Railway logs** in the dashboard
2. **Verify environment variables** are set correctly
3. **Ensure all dependencies** are in `requirements.txt`
4. **Check Dockerfile** syntax

## 🎉 Success!

Once deployed, you'll have a **professional, scalable web application** that your ops team can use monthly without any technical knowledge!

**Your app URL will be:** `https://your-app-name.railway.app`
