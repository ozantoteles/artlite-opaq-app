#!/bin/bash

# Define the source directory and tarball name
SOURCE_DIR="/home/mobaxterm/ARTLITE-OPAQ-APP/artlite-opaq-app"
TARBALL_NAME="artlite-opaq-app.tar.gz"
TEMP_DIR="/tmp/artlite-opaq-app-tarball"

echo "Creating a tarball from the source directory..."
# Create a tarball excluding .pyc files, __pycache__ directory, .vscode, .git directory, and .gitignore file
mkdir -p $TEMP_DIR
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.vscode' --exclude='.git' --exclude='.gitignore' -czf $TEMP_DIR/$TARBALL_NAME -C $(dirname $SOURCE_DIR) $(basename $SOURCE_DIR)
echo "Tarball created: $TEMP_DIR/$TARBALL_NAME"

# Create the service file
SERVICE_FILE_PATH="$SOURCE_DIR/artlite-opaq-app.service"
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
WorkingDirectory=/usr/local/artlite-opaq-app
ExecStartPre=/bin/sleep 120
ExecStartPre=/bin/systemctl stop cair-app.service
ExecStart=/usr/bin/python3.10 /usr/local/artlite-opaq-app/src/main.py
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
EOL

echo "Service file created: $SERVICE_FILE_PATH"

# Function to execute commands over SSH
function ssh_execute {
  local target=$1
  local command=$2
  echo "Executing command on $target: $command"
  ssh root@$target "$command"
}

# Loop through each target
for target in 192.168.1.100 192.168.1.102 192.168.1.104 192.168.1.108 192.168.1.122 192.168.1.186; do
  echo "Copying tarball and service file to $target..."
  # Copy the tarball and service file to the remote target
  scp $TEMP_DIR/$TARBALL_NAME root@$target:/usr/local/
  scp $SERVICE_FILE_PATH root@$target:/usr/local/artlite-opaq-app.service

  echo "Running setup commands on $target..."
  # Commands to execute on the remote target
  ssh_execute $target "
    echo 'Checking for get-pip.py...'
    # Download get-pip.py if not already available
    if [ ! -f /home/root/get-pip.py ]; then
      echo 'Downloading get-pip.py...'
      wget -q https://bootstrap.pypa.io/get-pip.py -O /home/root/get-pip.py
    else
      echo 'get-pip.py already exists.'
    fi

    echo 'Checking for pip installation...'
    # Install pip for Python 3.10 if not already installed
    if ! python3.10 -m pip --version &>/dev/null; then
      echo 'Installing pip...'
      python3.10 /home/root/get-pip.py
    else
      echo 'pip is already installed.'
    fi

    echo 'Checking for pyserial installation...'
    # Install pyserial if not already installed
    if ! python3.10 -m pip show pyserial &>/dev/null; then
      echo 'Installing pyserial...'
      python3.10 -m pip install pyserial
    else
      echo 'pyserial is already installed.'
    fi

    echo 'Extracting tarball...'
    # Extract the tarball and remove it
    tar -xzf /usr/local/$TARBALL_NAME -C /usr/local/ && rm /usr/local/$TARBALL_NAME
    echo 'Tarball extracted and removed.'

    echo 'Running unique address generator...'
    # Run the unique address generator script
    python3.10 /usr/local/artlite-opaq-app/scripts/unique_address_generator.py
    echo 'Unique address generation complete.'

    echo 'Setting up systemd service...'
    # Copy the service file to systemd directory and enable/start the service
    cp /usr/local/artlite-opaq-app.service /lib/systemd/system/
    systemctl daemon-reload
    systemctl enable artlite-opaq-app.service
    systemctl start artlite-opaq-app.service
    echo 'Systemd service setup complete.'
  "
done

# Clean up the local tarball
echo 'Cleaning up local tarball...'
rm -r $TEMP_DIR
echo 'Local cleanup complete.'
