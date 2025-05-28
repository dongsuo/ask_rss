#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create logs directory if it doesn't exist
mkdir -p logs

# Get current timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/server_${TIMESTAMP}.log"

# Start the server
echo -e "${GREEN}Starting RSS Feed Processor API server...${NC}"
echo -e "Logs will be written to: ${YELLOW}${LOG_FILE}${NC}"
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop the server\n"

# Run the server with uvicorn
echo -e "${GREEN}Starting server with PYTHONPATH: ${PYTHONPATH}${NC}"
echo -e "Current directory: $(pwd)"

# Run the server using the module syntax
python -m uvicorn rss_processor.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --workers 1 \
    --timeout-keep-alive 60 \
    --no-access-log 2>&1 | tee "${LOG_FILE}"

# If the server exits, show a message
echo -e "\n${YELLOW}Server stopped.${NC}"
echo -e "Log file: ${YELLOW}${LOG_FILE}${NC}"
