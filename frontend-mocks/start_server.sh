#!/bin/bash
# Start script for Termux

echo "🚀 Starting LLMplate Mocks Server..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    pkg install python -y
fi

# Make serve script executable
chmod +x serve_mocks.py

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the frontend-mocks directory
cd "$DIR"

# Start the server
python3 serve_mocks.py