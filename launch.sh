#!/bin/bash
# Handshake Proxy - Linux/Mac Flash Drive Launcher

echo ""
echo "========================================"
echo "    HANDSHAKE PROXY - FLASH DRIVE MODE"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8+ via:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "[INFO] Python found: $(python3 --version)"

# Create required directories
mkdir -p logs
mkdir -p output

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "[ERROR] config.json not found"
    echo "Please ensure config.json is in the same directory as this script"
    exit 1
fi

echo "[INFO] Configuration file found"

# Install dependencies
echo "[INFO] Installing Python dependencies..."
pip3 install -q requests beautifulsoup4 urllib3 2>/dev/null

if [ $? -ne 0 ]; then
    echo "[WARNING] Failed to install some dependencies"
    echo "Attempting to continue..."
fi

# Run main.py
echo ""
echo "[INFO] Starting HandshakeProxy..."
echo ""

python3 python/main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[INFO] HandshakeProxy completed successfully"
    echo "[INFO] Results saved to: output/scraped_data.json"
else
    echo ""
    echo "[ERROR] HandshakeProxy exited with error"
fi

echo ""
