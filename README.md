# ⚡ Utility Bill Calculator

A professional web application for automated monthly utility bill analysis and excess charge calculation. This system scrapes utility data from Polaroo, processes it, and provides detailed insights for property management operations.

## 🏗️ Architecture

### **System Components**

1. **FastAPI Backend** (`src/api.py`)
   - RESTful API endpoints for utility calculations
   - Automated Polaroo report scraping
   - Data processing and analysis
   - Database integration (Supabase)

2. **Modern Web Frontend** (`src/static/index.html`)
   - Responsive Bootstrap-based UI
   - Real-time data visualization with Chart.js
   - Interactive dashboards and reports
   - Export functionality (CSV/Excel)

3. **Data Processing Engine** (`src/polaroo_process.py`)
   - Utility data parsing and calculation
   - Excess charge computation
   - Property filtering and analysis

4. **Automated Scraper** (`src/polaroo_scrape.py`)
   - Headless browser automation with Playwright
   - Secure login and report download
   - Error handling and retry logic

## 🚀 Deployment Options

### **Option 1: Railway (Recommended)**

Railway is perfect for this application due to its simplicity and reliability.

1. **Fork/Clone** this repository
2. **Connect** to Railway:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and deploy
   railway login
   railway init
   railway up
   ```

3. **Configure Environment Variables** in Railway dashboard:
   ```
   POLAROO_EMAIL=your_email@example.com
   POLAROO_PASSWORD=your_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   STORAGE_BUCKET=polaroo
   ```

4. **Deploy**: Railway automatically detects the `railway.json` configuration

### **Option 2: Render**

1. **Connect** your GitHub repository to Render
2. **Create** a new Web Service
3. **Configure** build settings:
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Start Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
4. **Set** environment variables in Render dashboard
5. **Deploy**

### **Option 3: Heroku**

1. **Install** Heroku CLI
2. **Create** Heroku app:
   ```bash
   heroku create your-app-name
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/heroku/heroku-buildpack-google-chrome
   ```

3. **Set** environment variables:
   ```bash
   heroku config:set POLAROO_EMAIL=your_email@example.com
   heroku config:set POLAROO_PASSWORD=your_password
   heroku config:set SUPABASE_URL=your_supabase_url
   heroku config:set SUPABASE_SERVICE_KEY=your_supabase_key
   heroku config:set STORAGE_BUCKET=polaroo
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### **Option 4: DigitalOcean App Platform**

1. **Connect** your GitHub repository
2. **Create** new App
3. **Select** Python environment
4. **Configure** build settings:
   - **Build Command**: `pip install -r requirements.txt && playwright install chromium && playwright install-deps`
   - **Run Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
5. **Set** environment variables
6. **Deploy**

### **Option 5: AWS Elastic Beanstalk**

1. **Create** Elastic Beanstalk environment
2. **Upload** application bundle
3. **Configure** environment variables
4. **Deploy**

## 🔧 Local Development

### **Prerequisites**
- Python 3.10+
- Node.js (for Railway CLI if using Railway)

### **Setup**

1. **Clone** the repository:
   ```bash
   git clone <your-repo-url>
   cd polaroo-ingest
   ```

2. **Install** dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   playwright install-deps
   ```

3. **Create** `.env` file:
   ```env
   POLAROO_EMAIL=your_email@example.com
   POLAROO_PASSWORD=your_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   STORAGE_BUCKET=polaroo
   ```

4. **Run** the application:
   ```bash
   cd src
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access** the application at `http://localhost:8000`

## 📊 Features

### **Core Functionality**
- ✅ **Automated Scraping**: Downloads latest utility reports from Polaroo
- ✅ **Smart Processing**: Calculates excess charges based on configurable allowances
- ✅ **Data Storage**: Archives reports and results in Supabase
- ✅ **Real-time Analysis**: Instant calculation and visualization
- ✅ **Export Capabilities**: CSV and Excel report generation

### **User Interface**
- 🎨 **Modern Design**: Professional, responsive interface
- 📱 **Mobile Friendly**: Works on all devices
- 📈 **Interactive Charts**: Visual data representation
- 🔍 **Detailed Tables**: Comprehensive property analysis
- ⚡ **Fast Performance**: Optimized for quick calculations

### **Data Management**
- 💾 **Automatic Archiving**: All reports saved to database
- 📋 **Historical Tracking**: Maintains calculation history
- 🔒 **Secure Storage**: Environment-based credential management
- 📊 **Data Export**: Multiple format support

## 🔐 Security & Configuration

### **Environment Variables**
```env
# Polaroo Credentials
POLAROO_EMAIL=your_email@example.com
POLAROO_PASSWORD=your_password

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
STORAGE_BUCKET=polaroo

# PDF Invoice Storage (separate bucket for invoices)
PDF_BUCKET=polaroo-invoices
PDF_PREFIX=invoices
PDF_EXPIRY_MINUTES=10

# Optional Settings
REPORT_DATE=YYYY-MM-DD  # Specific report date (optional)
```

### **Security Best Practices**
- ✅ Environment variables for sensitive data
- ✅ CORS configuration for production
- ✅ Input validation with Pydantic
- ✅ Error handling and logging
- ✅ Secure file handling

## 📈 Usage Workflow

### **Monthly Operations Process**

1. **Access** the web application
2. **Configure** allowances in the sidebar:
   - Electricity allowance (default: €100)
   - Water allowance (default: €50)
3. **Click** "Calculate Monthly Report"
4. **Wait** for automated processing:
   - Report download from Polaroo
   - Data processing and calculation
   - Database storage (if enabled)
5. **Review** results in multiple views:
   - Overview table
   - Overages analysis
   - Interactive charts
   - Export options
6. **Export** reports for billing purposes

## 🛠️ API Endpoints

### **Core Endpoints**
- `GET /` - Main application interface
- `POST /api/calculate` - Run monthly calculation
- `GET /api/results/latest` - Get latest results
- `GET /api/export/csv` - Export CSV report
- `GET /api/export/excel` - Export Excel report
- `GET /api/health` - Health check

### **API Documentation**
Access interactive API docs at `/docs` when running locally.

## 🔄 Maintenance

### **Regular Tasks**
- Monitor application logs
- Update Polaroo credentials if needed
- Review and adjust allowances
- Backup database regularly
- Update dependencies periodically

### **Troubleshooting**
- Check environment variables
- Verify Polaroo credentials
- Monitor Supabase connection
- Review application logs

## 📞 Support

For issues or questions:
1. Check the application logs
2. Verify environment configuration
3. Test with sample data
4. Contact the development team

---

**Built with ❤️ for efficient property management operations**

