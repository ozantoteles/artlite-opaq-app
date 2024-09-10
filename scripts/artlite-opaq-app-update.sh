#!/bin/bash
set -x

# Log file path
LOGFILE="/var/log/artlite-opaq-setup.log"

# Redirect stdout and stderr to the log file
exec > >(tee -a ${LOGFILE})
exec 2>&1

# Directory where the app will be installed
ARTLITE_Opaq_DIR="/usr/local/artlite-opaq-app"

echo "Starting Artlite Opaq APP update..."

# Ensure target directory exists, create it if it doesn't
echo "Checking if directory exists..."
[ ! -d "$ARTLITE_Opaq_DIR" ] && mkdir -p "$ARTLITE_Opaq_DIR"

# Download the repository from GitHub for artlite-opaq-app
echo "Downloading the Artlite Opaq APP repository from GitHub..."
wget -q https://github.com/ozantoteles/artlite-opaq-app/archive/refs/heads/master.zip -O /tmp/artlite-opaq-app.zip
echo "Artlite Opaq APP repository downloaded."

# Extract the repository to /usr/local
echo "Extracting Artlite Opaq APP repository..."
unzip -o /tmp/artlite-opaq-app.zip -d /usr/local/
# Overwrite the existing directory with cp
cp -rf /usr/local/artlite-opaq-app-master/* $ARTLITE_Opaq_DIR/
rm -rf /usr/local/artlite-opaq-app-master
rm /tmp/artlite-opaq-app.zip
echo "Artlite Opaq APP repository extracted to $ARTLITE_Opaq_DIR."

# Set up the systemd service for Artlite Opaq APP
echo "Restarting the Artlite Opaq APP service..."
systemctl daemon-reload
systemctl restart artlite-opaq-app.service
echo "Artlite Opaq APP service restarted."

echo "Artlite Opaq APP update completed."
