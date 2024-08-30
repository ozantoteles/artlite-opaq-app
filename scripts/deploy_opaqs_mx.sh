#!/bin/bash
 
# Define the source directory and tarball name
SOURCE_DIR="/home/mobaxterm/artlite-opaq-app"
TARBALL_NAME="artlite-opaq-app.tar.gz"
TEMP_DIR="/tmp/artlite-opaq-app-tarball"
 
# Create a temporary directory
mkdir -p $TEMP_DIR
 
# Create a tarball excluding .pyc files, __pycache__ directory, .vscode, .git directory, and .gitignore file
echo "Creating tarball..."
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.vscode' --exclude='.git' --exclude='.gitignore' -czf $TEMP_DIR/$TARBALL_NAME -C $(dirname $SOURCE_DIR) $(basename $SOURCE_DIR)
 
# Get the size of the tarball for progress calculation
TARBALL_SIZE=$(stat -c %s $TEMP_DIR/$TARBALL_NAME)
 
# Check if pv is installed, otherwise use a simple scp
if command -v pv >/dev/null 2>&1; then
    COPY_CMD="pv -s $TARBALL_SIZE $TEMP_DIR/$TARBALL_NAME | ssh -o ForwardX11=no root@%s 'cat > /usr/local/$TARBALL_NAME'"
else
    echo "pv command not found, proceeding without progress bar."
    COPY_CMD="scp $TEMP_DIR/$TARBALL_NAME root@%s:/usr/local/"
fi
 
# Loop through each target and copy the tarball
for target in 192.168.1.110 192.168.1.128; do
#for target in 192.168.1.125 192.168.1.116 192.168.1.104 192.168.1.108 192.168.1.109 192.168.1.110 192.168.1.114 192.168.1.115 192.168.1.118 192.168.1.120 192.168.1.121 192.168.1.122 192.168.1.123 192.168.1.127 192.168.1.128 192.168.1.129 192.168.1.130 192.168.1.131 192.168.1.132 192.168.1.186 192.168.1.126 192.168.1.100; do
#for target in 192.168.1.110 192.168.1.104 192.168.1.186 192.168.1.102 192.168.1.125 192.168.1.122 192.168.1.126 192.168.1.109 192.168.1.100 192.168.1.127 192.168.1.128 192.168.1.114 192.168.1.115 192.168.1.120 192.168.1.121 192.168.1.123 192.168.1.129 192.168.1.130 192.168.1.118 192.168.1.131 192.168.1.132; do
#for target in  192.168.1.102 192.168.1.128 192.168.1.127 192.168.1.128; do
  echo "Copying to $target..."
  eval $(printf "$COPY_CMD" "$target")
  echo "Extracting on $target..."
  ssh -o ForwardX11=no root@$target "tar -xzf /usr/local/$TARBALL_NAME -C /usr/local/ && rm /usr/local/$TARBALL_NAME"
  echo "Done with $target."
  #ssh -o ForwardX11=no root@$target "systemctl restart artlite-opaq-app.service"
  #echo 'Systemd service restarted.'

done
 
# Clean up the local tarball
rm -r $TEMP_DIR
 
echo "All tasks completed."
 