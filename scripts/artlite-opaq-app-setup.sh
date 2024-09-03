#!/bin/bash

# Log file path
LOGFILE="/var/log/artlite-opaq-app-setup.log"

# Redirect stdout and stderr to the log file
exec > >(tee -a ${LOGFILE} )
exec 2>&1

# Directory where the app will be installed
INSTALL_DIR="/usr/local/artlite-opaq-app"

echo "Starting Artlite Opaq APP setup..." 

# Download the repository from GitHub
echo "Downloading the repository from GitHub..."
wget -q https://github.com/ozantoteles/artlite-opaq-app/archive/refs/heads/master.zip -O /tmp/artlite-opaq-app.zip
echo "Repository downloaded."

# Extract the repository to /usr/local
echo "Extracting repository..."
unzip -o /tmp/artlite-opaq-app.zip -d /usr/local/
mv /usr/local/artlite-opaq-app-master $INSTALL_DIR
rm /tmp/artlite-opaq-app.zip
echo "Repository extracted to $INSTALL_DIR."

# Create the service file
SERVICE_FILE_PATH="/lib/systemd/system/artlite-opaq-app.service"
echo "Creating the systemd service file at $SERVICE_FILE_PATH..."
cat <<EOL > $SERVICE_FILE_PATH
[Unit]
Description=Artlite Opaq APP
RequiresMountsFor=/run
After=cair-app.service

[Service]
Type=simple
Restart=always
RestartSec=3
User=root
Group=root
PermissionsStartOnly=true
StandardError=journal
StandardOutput=journal
WorkingDirectory=$INSTALL_DIR
ExecStartPre=/bin/sleep 120
ExecStartPre=/bin/systemctl stop cair-app.service
ExecStart=/usr/bin/python3.10 $INSTALL_DIR/src/main.py
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
EOL
echo "Systemd service file created."

# Install necessary Python packages
echo "Checking and installing necessary Python packages..."

# Download get-pip.py if not already available
if [ ! -f /home/root/get-pip.py ]; then
  echo "Downloading get-pip.py..."
  wget -q https://bootstrap.pypa.io/get-pip.py -O /home/root/get-pip.py
  echo "get-pip.py downloaded."
else
  echo "get-pip.py already exists."
fi

# Install pip for Python 3.10 if not already installed
if ! python3.10 -m pip --version &>/dev/null; then
  echo "Installing pip..."
  python3.10 /home/root/get-pip.py
  echo "pip installed."
else
  echo "pip is already installed."
fi

# Install pyserial if not already installed
if ! python3.10 -m pip show pyserial &>/dev/null; then
  echo "Installing pyserial..."
  python3.10 -m pip install pyserial
  echo "pyserial installed."
else
  echo "pyserial is already installed."
fi

# Install pyserial-asyncio if not already installed
if ! python3.10 -m pip show pyserial-asyncio &>/dev/null; then
  echo "Installing pyserial-asyncio..."
  python3.10 -m pip install pyserial-asyncio
  echo "pyserial-asyncio installed."
else
  echo "pyserial-asyncio is already installed."
fi

# Install pymodbus if not already installed
if ! python3.10 -m pip show pymodbus &>/dev/null; then
  echo "Installing pymodbus..."
  python3.10 -m pip install pymodbus
  echo "pymodbus installed."
else
  echo "pymodbus is already installed."
fi

# Install pyudev if not already installed
if ! python3.10 -m pip show pyudev &>/dev/null; then
  echo "Installing pyudev..."
  python3.10 -m pip install pyudev
  echo "pyudev installed."
else
  echo "pyudev is already installed."
fi

# Run the unique address generator script
echo "Running unique address generator..."
python3.10 $INSTALL_DIR/scripts/unique_address_generator.py
echo "Unique address generation complete."

# Set up the systemd service
echo "Setting up the systemd service..."
systemctl daemon-reload
systemctl enable artlite-opaq-app.service
systemctl start artlite-opaq-app.service
echo "Systemd service setup complete."

# Set bootdelay to 0
echo "Setting bootdelay to 0..."
fw_setenv bootdelay 0
fw_printenv bootdelay
echo "Bootdelay set to 0."

echo "Artlite Opaq APP setup complete."
