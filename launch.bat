@echo off
REM Handshake Proxy - Flash Drive Launcher
REM Windows batch script to launch anti-detection proxy scraper

setlocal enabledelayedexpansion

echo.
echo ========================================
echo    HANDSHAKE PROXY - FLASH DRIVE MODE
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version

REM Create required directories
if not exist "logs" mkdir logs
if not exist "output" mkdir output

REM Check if config.json exists
if not exist "config.json" (
    echo [ERROR] config.json not found
    echo Please ensure config.json is in the same directory as this script
    pause
    exit /b 1
)

echo [INFO] Configuration file found

REM Install dependencies if needed
echo [INFO] Checking Python dependencies...
pip install -q requests beautifulsoup4 urllib3 2>nul

if errorlevel 1 (
    echo [WARNING] Failed to install some dependencies via pip
    echo Attempting to continue...
)

REM Run main.py
echo.
echo [INFO] Starting HandshakeProxy...
echo.

python python/main.py

if errorlevel 1 (
    echo [ERROR] HandshakeProxy exited with error code %errorlevel%
)

echo.
echo [INFO] HandshakeProxy completed
echo [INFO] Results saved to: output/scraped_data.json
echo.
pause
