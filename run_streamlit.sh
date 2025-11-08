#!/bin/bash
# Quick start script for Streamlit app

echo "🚀 Starting Agent Axios Streamlit Tester"
echo "========================================"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit dependencies..."
    pip install -r streamlit_requirements.txt
fi

echo "✅ Launching Streamlit app..."
echo ""
echo "📍 Make sure the backend is running:"
echo "   cd agent-axios-backend && python run.py"
echo ""
echo "🌐 App will open at: http://localhost:8501"
echo ""

streamlit run streamlit_app.py
