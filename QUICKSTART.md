# 🚀 Error Analyzer PoC - Quick Start Guide

## Option A: Super Quick Start (Recommended)
```bash
pip install -r requirements.txt
./start.sh
```

## Option B: Step by Step
```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Initialize Database (First Time)
python init_db.py

# 3. Run the Application
python run.py
```

## 4. Access the Dashboard
Open your browser and go to: **http://localhost:8000/ui**

## 5. Try the Features

### Manual Pipeline Execution
- Click the "Manual Trigger Pipeline" button in the dashboard
- Watch the pipeline progress in real-time
- See new error groups appear after analysis

### Explore Error Groups
- **Active Issues** tab: Real errors that need attention
- **Non-Issues** tab: Errors marked as not important
- Toggle any error between the tabs using the switch at the bottom of each card

### Filter and Sort
- **Date Filters**: Use quick filters (1H, 24H, 7D) or custom date ranges
- **Project Filters**: Filter by project names (NPay-Service, Shopping-API, Auth-Center)
- **Sort Options**: Risk Score, Last Seen, Occurrences

### Examine Details
- Click on any error card to expand and see:
  - AI analysis (Root Cause, Impact, Solutions)
  - Original log signature
  - Risk score visualization
  - Occurrence trends

## 6. API Endpoints

Test the REST API directly:

```bash
# Get all error groups
curl http://localhost:8000/api/groups

# Get pipeline status  
curl http://localhost:8000/api/pipeline-status

# Trigger pipeline manually
curl -X POST http://localhost:8000/trigger-pipeline

# Toggle non-issue status
curl -X POST http://localhost:8000/api/groups/1/toggle-non-issue \
  -H "Content-Type: application/json" \
  -d '{"is_non_issue": true}'
```

## 7. Customization

### Connect to NELO API
Edit `.env` file to enable NELO integration:
```bash
# Change log source to NELO
LOG_SOURCE_TYPE=nelo

# Configure NELO API (your actual keys)
NELO_ACCESS_KEY=your_actual_access_key
NELO_SECRET_KEY=your_actual_secret_key
NELO_GROUP_ID=6370

# Optional: Adjust pipeline interval
PIPELINE_INTERVAL_SECONDS=300
```

The system will automatically:
- Fetch error logs from NELO every pipeline run
- Fallback to sample data if NELO is unavailable
- Show NELO connection status in the dashboard

### Add Your Own Sample Logs
Edit `sample_logs.json` with your log format:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "logLevel": "ERROR", 
  "logger": "com.your.service.MyService",
  "application": "YourApp",
  "projectName": "YourProject",
  "body": "Your error message",
  "stackTrace": ["..."],
  "metadata": {...}
}
```

### Connect Real AI API
Set environment variables in `.env`:
```bash
AI_API_URL=https://api.openai.com/v1/chat/completions
AI_API_KEY=your_key_here
```

Then implement real AI logic in `app/services/analysis_service.py`.

## 📊 What You'll See

- **Pipeline Status**: Real-time progress tracking
- **Risk Scores**: 0-100 visualization with color coding
- **Trend Sparklines**: Recent occurrence patterns  
- **Grouping Methods**: STACKTRACE vs DRAIN algorithm
- **Interactive Filtering**: Multiple filters and sorting options
- **AI Analysis**: Automated root cause analysis and solutions

The system automatically processes your logs every 60 seconds, groups similar errors intelligently, and provides AI-powered insights to help you focus on what matters most!

🎉 **Enjoy exploring your Error Analyzer PoC Dashboard!**