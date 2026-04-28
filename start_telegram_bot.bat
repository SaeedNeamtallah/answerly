@echo off
REM RAGMind Telegram Bot Startup Script

echo ========================================
echo    RAGMind Telegram Bot
echo ========================================
echo.

REM Activate virtual environment
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run start_backend.bat first to create it.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Check if bot token is configured
echo Checking configuration...
python -c "from telegram_bot.config import bot_settings; assert bot_settings.telegram_bot_token != 'your_telegram_bot_token_here', 'Please configure TELEGRAM_BOT_TOKEN in .env file'" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Telegram bot token not configured!
    echo Please set TELEGRAM_BOT_TOKEN in the .env file
    echo.
    pause
    exit /b 1
)

REM Start bot
echo Starting Telegram bot...
echo.
python -m telegram_bot.bot
