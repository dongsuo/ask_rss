#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up RSS Feed Processor API...${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}
pip install -r requirements.txt

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p logs
datasets

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update the .env file with your configuration.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Make scripts executable
chmod +x start_server.sh

# Print completion message
echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "\nTo start the server, run: ${YELLOW}./start_server.sh${NC}"
echo -e "To run tests: ${YELLOW}python -m pytest tests/${NC}"
echo -e "To run the example: ${YELLOW}python example_usage.py${NC}"
echo -e "\nDon't forget to activate the virtual environment with: ${YELLOW}source venv/bin/activate${NC}"
