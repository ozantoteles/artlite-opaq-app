#!/bin/bash

# Define the source directory and tarball name
SOURCE_DIR="/home/mobaxterm/artlite-opaq-app"
TARBALL_NAME="artlite-opaq-app.tar.gz"
TEMP_DIR="/tmp/artlite-opaq-app-tarball"

# Create a temporary directory
mkdir -p $TEMP_DIR

# Create a tarball excluding .pyc files, __pycache__ directory, .vscode, .git directory, and .gitignore file
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.vscode' --exclude='.git' --exclude='.gitignore' -czf $TEMP_DIR/$TARBALL_NAME -C $(dirname $SOURCE_DIR) $(basename $SOURCE_DIR)

# Loop through each target and copy the tarball
for target in 192.168.1.100 192.168.1.102 192.168.1.104 192.168.1.108 192.168.1.186; do
  scp $TEMP_DIR/$TARBALL_NAME root@$target:/usr/local/
  ssh root@$target "tar -xzf /usr/local/$TARBALL_NAME -C /usr/local/ && rm /usr/local/$TARBALL_NAME"
done

# Clean up the local tarball
rm -r $TEMP_DIR
