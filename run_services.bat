@echo off
echo ========================================
echo 🚀 Starting Device Registration Services
echo ========================================
echo.

echo 📦 Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo 🔧 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🌐 Starting Flask Web App (Port 8080)...
start cmd /k "python app.py"

echo.
echo 🤖 Starting Telegram Bot Webhook Server (Port 8081)...
timeout /t 3 /nobreak >nul
start cmd /k "python webhook_server.py"

echo.
echo ✅ Both services are starting...
echo.
echo 📍 Web Portal: http://localhost:8080
echo 🤖 Bot Webhook: http://localhost:8081
echo.
echo Press any key to close this window...
pause >nul