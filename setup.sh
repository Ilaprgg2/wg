#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to prompt for yes/no
confirm() {
    while true; do
        read -p "$(echo -e "${YELLOW}$1 (y/n): ${NC}")" yn
        case $yn in
            [Yy]* ) return 0;;  # true
            [Nn]* ) return 1;;  # false
            * ) echo -e "${RED}Please answer yes or no.${NC}";;
        esac
    done
}

# Default values
REPO_URL="https://github.com/Ilaprgg2/wg.git"
PACKAGES="fastapi python-dotenv uvicorn schedule"

echo -e "${BLUE}Starting setup script${NC}"

# Install Python3, pip, WireGuard, and WireGuard tools
echo -e "${BLUE}Updating and installing packages${NC}"
sudo apt update
sudo apt install -y python3 python3-pip wireguard wireguard-tools

# Install Python packages
echo -e "${BLUE}Installing Python packages${NC}"
pip3 install $PACKAGES

# Clone the GitHub repository
echo -e "${BLUE}Cloning repository${NC}"
git clone $REPO_URL
repo_name=$(basename $REPO_URL .git)
cd $repo_name

# Prompt for API_KEY and MAIN_SERVER
read -p "$(echo -e "${YELLOW}Enter your API_KEY: ${NC}")" API_KEY
read -p "$(echo -e "${YELLOW}Enter your MAIN_SERVER (like this: http://1.1.1.1:4432  DO NOT PUT AN ENDING SLASH /): ${NC}")" MAIN_SERVER

# Create .env file
echo -e "${BLUE}Creating .env file${NC}"
cat << EOF > .env
API_KEY=$API_KEY
MAIN_SERVER=$MAIN_SERVER
EOF

# WireGuard setup
if confirm "Do you want to restore from backup?"; then
    echo -e "${BLUE}User chose to restore from backup${NC}"
    if [ -f "../db.db" ]; then
        cp ../db.db .
        echo -e "${GREEN}Copied db.db to current directory${NC}"
        read -p "$(echo -e "${YELLOW}Enter interface private key: ${NC}")" private_key
        read -p "$(echo -e "${YELLOW}Enter interface port: ${NC}")" port
    else
        echo -e "${RED}Backup file (db.db) not found in the parent directory. Proceeding without backup.${NC}"
        read -p "$(echo -e "${YELLOW}Enter interface port: ${NC}")" port
        private_key=$(wg genkey)
    fi
else
    echo -e "${BLUE}User chose not to restore from backup${NC}"
    read -p "$(echo -e "${YELLOW}Enter interface port: ${NC}")" port
    private_key=$(wg genkey)
fi

# Create WireGuard configuration
echo -e "${BLUE}Creating WireGuard configuration${NC}"
cat << EOF | sudo tee /etc/wireguard/wgg.conf
[Interface]
Address = 11.0.0.1/24
SaveConfig = true
PostUp = iptables -I INPUT -p udp --dport $port -j ACCEPT; iptables -I FORWARD -i eth0 -o %i -j ACCEPT; iptables -I FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D INPUT -p udp --dport $port -j ACCEPT; iptables -D FORWARD -i eth0 -o %i -j ACCEPT; iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
ListenPort = $port
PrivateKey = $private_key
EOF

# Start WireGuard
echo -e "${BLUE}Starting WireGuard${NC}"
sudo wg-quick up wgg

# Run the appropriate Python file
echo -e "${BLUE}Running Python setup script${NC}"
if [ -f "db.db" ]; then
    python3 restore.py
else
    python3 setup_database.py
fi

# Create api.service
echo -e "${BLUE}Creating api.service${NC}"
cat << EOF | sudo tee /etc/systemd/system/api.service
[Unit]
Description=API Service
After=network.target

[Service]
Type=idle
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/uvicorn api:app --host 0.0.0.0 --port 5390 --app-dir=$(pwd)
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create stats.service
echo -e "${BLUE}Creating stats.service${NC}"
cat << EOF | sudo tee /etc/systemd/system/stats.service
[Unit]
Description=wg stats
After=network.target

[Service]
Type=idle
User=root
WorkingDirectory=$(pwd)
ExecStart=python3 -u stats.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the services
echo -e "${BLUE}Enabling and starting services${NC}"
sudo systemctl daemon-reload
sudo systemctl enable api.service stats.service
sudo systemctl start api.service stats.service

# Get server's IPv4 address
server_ip=$(curl -s ipinfo.io/ip)

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Private key: ${NC}$private_key"
echo -e "${YELLOW}API key: ${NC}$API_KEY"
echo -e "${YELLOW}Add this in address section of Telegram bot (DO NOT PUT HTTP:// AND DO NOT PUT AN ENDING / ):  ${NC}$server_ip:5390"

echo -e "${GREEN}Run 'journalctl -fu api -n 100' and 'journalctl -fu stats -n 100' for logs${NC}"