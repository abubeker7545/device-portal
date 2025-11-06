#!/bin/bash

echo "========================================"
echo "🚀 Starting Device Registration Services"
echo "========================================"
echo

echo "📦 Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

echo
echo "🔧 Installing dependencies..."
pip3 install -r requirements.txt

echo
echo "🌐 Starting Flask Web App (Port 8080)..."
python3 app.py &

echo
echo "🤖 Starting Telegram Bot Webhook Server (Port 8081)..."
sleep 3
python3 webhook_server.py &

echo
echo "✅ Both services are starting..."
echo
echo "📍 Web Portal: http://localhost:8080"
echo "🤖 Bot Webhook: http://localhost:8081"
echo
echo "Press Ctrl+C to stop all services"
wait