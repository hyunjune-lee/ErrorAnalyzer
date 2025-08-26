#!/bin/bash

echo "🚀 Starting Error Analyzer PoC..."
echo ""

# Check if database exists
if [ ! -f "error_analyzer.db" ]; then
    echo "📊 Initializing database (first time)..."
    python init_db.py
    echo ""
fi

echo "🔧 Starting FastAPI server..."
echo "📱 Dashboard will be available at: http://localhost:8000/ui"
echo "🔗 API endpoints at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run.py