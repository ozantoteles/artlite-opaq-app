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

# Function to execute commands over SSH
function ssh_execute {
  local target=$1
  local command=$2
  echo "Executing command on $target: $command"
  ssh root@$target "$command"
}

# Loop through each target
#for target in 192.168.1.136; do
for target in 192.168.1.100 192.168.1.104 192.168.1.108 192.168.1.109 192.168.1.110 192.168.1.114 192.168.1.115 192.168.1.116 192.168.1.118 192.168.1.120 192.168.1.121 192.168.1.122 192.168.1.123 192.168.1.125 192.168.1.126 192.168.1.127 192.168.1.128 192.168.1.129 192.168.1.130 192.168.1.131 192.168.1.132 192.168.1.186; do
  echo "Copying tarball to $target..."
  # Copy the tarball to the remote target
  scp $TEMP_DIR/$TARBALL_NAME root@$target:/usr/local/

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
  "
done

# Clean up the local tarball
echo 'Cleaning up local tarball...'
rm -r $TEMP_DIR
echo 'Local tarball cleanup complete.'
