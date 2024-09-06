#!/bin/bash
set -x

# Log file path
LOGFILE="/var/log/artlite-opaq-setup.log"

# Redirect stdout and stderr to the log file
exec > >(tee -a ${LOGFILE} )
exec 2>&1

# Directories where the apps will be installed
ARTLITE_Opaq_DIR="/usr/local/artlite-opaq-app"
BLE_CONFIGURATOR_DIR="/usr/local/artlite-opaq-ble-configurator-app"

echo "Starting Artlite Opaq APP and BLE Configurator setup..."

# Attempt to move sshd.socket file, but don't fail the script if it fails
mv /lib/systemd/system/sshd.socket\@disabled /lib/systemd/system/sshd.socket || true

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

# Download the repository from GitHub for BLE Configurator
echo "Downloading the Artlite Opaq BLE Configurator repository from GitHub..."
wget -q https://github.com/ozantoteles/artlite-opaq-ble-configurator-app/archive/refs/heads/master.zip -O /tmp/artlite-opaq-ble-configurator-app.zip
echo "Artlite Opaq BLE Configurator repository downloaded."

# Extract the repository to /usr/local
echo "Extracting BLE Configurator repository..."
unzip -o /tmp/artlite-opaq-ble-configurator-app.zip -d /usr/local/
# Overwrite the existing directory with cp
cp -rf /usr/local/artlite-opaq-ble-configurator-app-master/* $BLE_CONFIGURATOR_DIR/
rm -rf /usr/local/artlite-opaq-ble-configurator-app-master
rm /tmp/artlite-opaq-ble-configurator-app.zip
echo "Artlite Opaq BLE Configurator repository extracted to $BLE_CONFIGURATOR_DIR."


# Create the service file for Artlite Opaq APP
SERVICE_FILE_PATH="/lib/systemd/system/artlite-opaq-app.service"
echo "Creating the systemd service file for Artlite Opaq APP at $SERVICE_FILE_PATH..."
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
WorkingDirectory=$ARTLITE_Opaq_DIR
ExecStartPre=/bin/sleep 120
ExecStartPre=/bin/systemctl stop cair-app.service
ExecStart=/usr/bin/python3.10 $ARTLITE_Opaq_DIR/src/main.py
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
EOL
echo "Systemd service file for Artlite Opaq APP created."

# Create the service file for BLE Configurator
BLE_SERVICE_FILE_PATH="/lib/systemd/system/artlite-opaq-ble-configurator-app.service"
echo "Creating the systemd service file for BLE Configurator at $BLE_SERVICE_FILE_PATH..."
cat <<EOL > $BLE_SERVICE_FILE_PATH
[Unit]
Description=Artlite Opaq BLE Configurator APP
RequiresMountsFor=/run
After=artlite-opaq-app.service

[Service]
Type=simple
Restart=always
RestartSec=3
User=root
Group=root
PermissionsStartOnly=true
StandardError=journal
StandardOutput=journal
WorkingDirectory=$BLE_CONFIGURATOR_DIR
ExecStart=/usr/bin/python $BLE_CONFIGURATOR_DIR/src/main.py

[Install]
WantedBy=multi-user.target
EOL
echo "Systemd service file for BLE Configurator created."

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

# Run the unique address generator script for Artlite Opaq APP
echo "Running unique address generator for Artlite Opaq APP..."
python3.10 $ARTLITE_Opaq_DIR/scripts/unique_address_generator.py
echo "Unique address generation complete."

# Set up the systemd service for Artlite Opaq APP
echo "Setting up the systemd service for Artlite Opaq APP..."
systemctl daemon-reload
systemctl enable artlite-opaq-app.service
systemctl start artlite-opaq-app.service
echo "Systemd service setup for Artlite Opaq APP complete."

# Set up the systemd service for BLE Configurator
echo "Setting up the systemd service for BLE Configurator..."
systemctl enable artlite-opaq-ble-configurator-app.service
systemctl start artlite-opaq-ble-configurator-app.service
echo "Systemd service setup for BLE Configurator complete."

# Set bootdelay to 0
echo "Setting bootdelay to 0..."
fw_setenv bootdelay 0
fw_printenv bootdelay
echo "Bootdelay set to 0."

echo "Artlite Opaq APP and BLE Configurator setup complete."
