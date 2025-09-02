# Deploy to Render (Free Tier)

## Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (recommended) or email
3. Connect your GitHub account if using GitHub

## Step 2: Upload Your Code
Since you don't have Git installed, you can:

### Option A: Use GitHub Desktop (Easiest)
1. Download GitHub Desktop: https://desktop.github.com/
2. Create a new repository
3. Add all your files
4. Push to GitHub
5. Connect Render to your GitHub repo

### Option B: Use Render's Web Interface
1. Create a new Web Service on Render
2. Choose "Build and deploy from a Git repository"
3. Upload your code as a ZIP file

## Step 3: Configure Environment Variables
In Render dashboard, add these environment variables:

```
POLAROO_EMAIL=your_polaroo_email
POLAROO_PASSWORD=your_polaroo_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
STORAGE_BUCKET=polaroo-reports
STORAGE_PREFIX=monthly-reports/
```

## Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy
3. Your app will be available at: `https://your-app-name.onrender.com`

## Free Tier Limits
- 750 hours/month (enough for always-on)
- Automatic sleep after 15 minutes of inactivity
- 512MB RAM
- Perfect for your utility calculator!

## Alternative: Railway
If Render doesn't work, try Railway:
1. Go to https://railway.app
2. Sign up with GitHub
3. Connect your repository
4. Add environment variables
5. Deploy!

Both platforms will solve the AsyncIO issue because they run in clean environments.
