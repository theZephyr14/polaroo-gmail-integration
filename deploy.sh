#!/bin/bash

# Utility Bill Calculator Deployment Script
# This script helps deploy the application to various platforms

set -e

echo "⚡ Utility Bill Calculator - Deployment Script"
echo "=============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to deploy to Railway
deploy_railway() {
    echo "🚂 Deploying to Railway..."
    
    if ! command_exists railway; then
        echo "❌ Railway CLI not found. Installing..."
        npm install -g @railway/cli
    fi
    
    echo "📋 Please configure your environment variables in Railway dashboard:"
    echo "   - POLAROO_EMAIL"
    echo "   - POLAROO_PASSWORD"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_SERVICE_KEY"
    echo "   - STORAGE_BUCKET"
    echo ""
    
    railway login
    railway up
    
    echo "✅ Railway deployment initiated!"
}

# Function to deploy to Render
deploy_render() {
    echo "🎨 Deploying to Render..."
    echo "📋 Please follow these steps:"
    echo "1. Go to https://render.com"
    echo "2. Connect your GitHub repository"
    echo "3. Create a new Web Service"
    echo "4. Configure build settings:"
    echo "   - Build Command: pip install -r requirements.txt && playwright install chromium && playwright install-deps"
    echo "   - Start Command: uvicorn src.api:app --host 0.0.0.0 --port \$PORT"
    echo "5. Set environment variables in Render dashboard"
    echo "6. Deploy"
    echo ""
    echo "🔗 Your app will be available at: https://your-app-name.onrender.com"
}

# Function to deploy to Heroku
deploy_heroku() {
    echo "🦸 Deploying to Heroku..."
    
    if ! command_exists heroku; then
        echo "❌ Heroku CLI not found. Please install from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    read -p "Enter your Heroku app name: " app_name
    
    heroku create $app_name
    heroku buildpacks:add heroku/python
    heroku buildpacks:add https://github.com/heroku/heroku-buildpack-google-chrome
    
    echo "📋 Setting environment variables..."
    read -p "Enter your Polaroo email: " polaroo_email
    read -s -p "Enter your Polaroo password: " polaroo_password
    echo
    read -p "Enter your Supabase URL: " supabase_url
    read -s -p "Enter your Supabase service key: " supabase_key
    echo
    
    heroku config:set POLAROO_EMAIL="$polaroo_email"
    heroku config:set POLAROO_PASSWORD="$polaroo_password"
    heroku config:set SUPABASE_URL="$supabase_url"
    heroku config:set SUPABASE_SERVICE_KEY="$supabase_key"
    heroku config:set STORAGE_BUCKET="polaroo"
    
    git push heroku main
    
    echo "✅ Heroku deployment completed!"
    echo "🔗 Your app is available at: https://$app_name.herokuapp.com"
}

# Function to run locally
run_local() {
    echo "🏠 Running locally..."
    
    if [ ! -f ".env" ]; then
        echo "📝 Creating .env file..."
        cat > .env << EOF
POLAROO_EMAIL=your_email@example.com
POLAROO_PASSWORD=your_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
STORAGE_BUCKET=polaroo
EOF
        echo "⚠️  Please update .env file with your actual credentials"
    fi
    
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium
    playwright install-deps
    
    echo "🚀 Starting application..."
    cd src
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
}

# Main menu
echo "Choose your deployment option:"
echo "1) 🚂 Deploy to Railway (Recommended)"
echo "2) 🎨 Deploy to Render"
echo "3) 🦸 Deploy to Heroku"
echo "4) 🏠 Run locally"
echo "5) 📋 Show deployment info"
echo "6) ❌ Exit"

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        deploy_railway
        ;;
    2)
        deploy_render
        ;;
    3)
        deploy_heroku
        ;;
    4)
        run_local
        ;;
    5)
        echo ""
        echo "📋 Deployment Information"
        echo "========================"
        echo ""
        echo "🔧 Required Environment Variables:"
        echo "   POLAROO_EMAIL=your_email@example.com"
        echo "   POLAROO_PASSWORD=your_password"
        echo "   SUPABASE_URL=your_supabase_url"
        echo "   SUPABASE_SERVICE_KEY=your_supabase_key"
        echo "   STORAGE_BUCKET=polaroo"
        echo ""
        echo "📁 Key Files:"
        echo "   - src/api.py (FastAPI backend)"
        echo "   - src/static/index.html (Frontend)"
        echo "   - src/polaroo_scrape.py (Scraper)"
        echo "   - src/polaroo_process.py (Data processing)"
        echo "   - requirements.txt (Dependencies)"
        echo ""
        echo "🚀 Quick Start Commands:"
        echo "   pip install -r requirements.txt"
        echo "   playwright install chromium"
        echo "   cd src && uvicorn api:app --reload"
        echo ""
        echo "📖 For detailed instructions, see README.md"
        ;;
    6)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

