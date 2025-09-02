# Deploy to Railway (Free Tier)

## Step 1: Install Git
1. Go to https://git-scm.com/download/win
2. Download and install Git for Windows
3. Restart your terminal/PowerShell
4. Verify with: `git --version`

## Step 2: Initialize Git Repository
```bash
# In your project directory
git init
git add .
git commit -m "Initial commit: Polaroo Utility Calculator"
```

## Step 3: Create GitHub Repository
1. Go to https://github.com
2. Sign up/Login
3. Click "New repository"
4. Name it: `polaroo-utility-calculator`
5. Make it **Public** (required for free Railway)
6. Don't initialize with README (we already have files)
7. Click "Create repository"

## Step 4: Push to GitHub
```bash
# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/polaroo-utility-calculator.git
git branch -M main
git push -u origin main
```

## Step 5: Deploy to Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `polaroo-utility-calculator` repository
6. Railway will automatically detect it's a Python app

## Step 6: Configure Environment Variables
In Railway dashboard, go to your project → Variables tab, add:

```
POLAROO_EMAIL=your_polaroo_email
POLAROO_PASSWORD=your_polaroo_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
STORAGE_BUCKET=polaroo-reports
STORAGE_PREFIX=monthly-reports/
```

## Step 7: Deploy!
1. Railway will automatically build and deploy
2. Your app will be available at: `https://your-app-name.railway.app`
3. Share this link with your ops team!

## Railway Free Tier Benefits
- ✅ Always-on (no sleep)
- ✅ Custom domain support
- ✅ Automatic HTTPS
- ✅ 512MB RAM
- ✅ 1GB storage
- ✅ Perfect for your utility calculator!

## Troubleshooting
- If build fails, check the logs in Railway dashboard
- Make sure all environment variables are set
- The app will be available at the Railway-provided URL
