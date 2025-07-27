#!/bin/bash

echo "🚀 Smart Backtester Launcher"
echo "=============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Install requirements if needed
echo "📦 Checking dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Launch Streamlit app
echo "🌐 Launching Smart Backtester..."
echo "📊 Open your browser to: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py
