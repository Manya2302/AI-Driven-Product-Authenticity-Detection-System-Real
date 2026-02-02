#!/bin/bash

# AI Product Authenticity Detection System - Quick Start Script

echo "🚀 Starting AI Product Authenticity Detection System"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check if MongoDB is running
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB is not running. Attempting to start..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start mongod
    else
        echo "❌ Please start MongoDB manually"
        exit 1
    fi
fi

echo "✅ MongoDB is running"

# Setup backend
echo ""
echo "📦 Setting up backend..."
cd backend || exit

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies (this may take a few minutes)..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your configuration"
fi

# Create necessary directories
mkdir -p uploads models logs

echo "✅ Backend setup complete"

# Start backend server in background
echo ""
echo "🚀 Starting backend server on http://localhost:8000"
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd ../frontend || exit

# Check if frontend dependencies are installed (if using node)
if [ -f "package.json" ]; then
    if ! command -v npm &> /dev/null; then
        echo "⚠️  npm not found, skipping frontend dependencies"
    else
        npm install
    fi
fi

# Start frontend server
echo ""
echo "🚀 Starting frontend server on http://localhost:3000"
if command -v python3 &> /dev/null; then
    python3 -m http.server 3000 &
    FRONTEND_PID=$!
fi

echo ""
echo "=================================================="
echo "✅ System started successfully!"
echo ""
echo "📍 Access Points:"
echo "   Frontend:    http://localhost:3000/pages/landing.html"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/api/docs"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Email:    admin@authenticity.ai"
echo "   Password: Admin@123"
echo ""
echo "⚠️  IMPORTANT: Change default credentials in production!"
echo ""
echo "To stop the servers, press Ctrl+C"
echo "=================================================="

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Keep script running
wait
