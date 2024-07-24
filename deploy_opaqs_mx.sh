#!/bin/bash

# Create a tarball excluding .pyc files, __pycache__ directory, and .git directory
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.vscode' --exclude='.git' --exclude='.gitignore' -czf artlite-opaq-app.tar.gz -C /home/mobaxterm artlite-opaq-app

for target in 192.168.1.108 192.168.1.109 192.168.1.111 192.168.1.117 192.168.1.118; do
  scp artlite-opaq-app.tar.gz root@$target:/usr/local/
  ssh root@$target "tar -xzf /usr/local/artlite-opaq-app.tar.gz -C /usr/local/ && rm /usr/local/artlite-opaq-app.tar.gz"
done

# Clean up the local tarball
rm artlite-opaq-app.tar.gz
