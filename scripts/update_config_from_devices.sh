#!/bin/bash

# Configuration
CONFIG_FILE="config.json"
DEVICES=("192.168.1.100" "192.168.1.109" "192.168.1.126" "192.168.1.127" "192.168.1.128")
SSH_USER="root"

# Ensure config file exists
if [ ! -f "$CONFIG_FILE" ]; then
  echo "{}" > $CONFIG_FILE
fi

# Function to execute a command over SSH
ssh_execute() {
  local target=$1
  local command=$2
  ssh $SSH_USER@$target "$command"
}

# Function to clean and extract JSON from the raw output
extract_json() {
  local raw_output=$1
  local json_output

  # Use sed to capture everything from the first '{' to the last '}'
  json_output=$(echo "$raw_output" | sed -n '/{/{:a;N;/}/!ba;s/.*\({.*}\).*/\1/p}')

  echo "$json_output"
}

# Function to merge device config with the local config file
merge_config() {
  local remote_config=$1

  # Print raw remote config for debugging
  echo "Raw remote config: '$remote_config'"

  # Extract the valid JSON part
  remote_config=$(extract_json "$remote_config")

  # Print extracted JSON for debugging
  echo "Extracted JSON config: '$remote_config'"

  # Validate the remote JSON before merging
  echo "$remote_config" | jq . > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    # Merge the remote config with the local config using jq
    jq -s '.[0] * .[1]' <(cat "$CONFIG_FILE") <(echo "$remote_config") > tmp.$$.json && mv tmp.$$.json "$CONFIG_FILE"
    echo "Local config merged with remote config."
  else
    echo "Invalid JSON received from remote device. Skipping merge."
  fi
}

# Loop through each device
for device in "${DEVICES[@]}"; do
  echo "Connecting to $device..."

  # Run the unique_address_generator.py script and retrieve the full config on the remote device
  remote_config=$(ssh_execute $device "python3.10 /usr/local/artlite-opaq-app/scripts/unique_address_generator.py && cat /usr/local/artlite-opaq-app/config/device_config.json")

  if [ $? -eq 0 ]; then
    echo "Retrieved config from $device."
    merge_config "$remote_config"
  else
    echo "Failed to retrieve config from $device."
  fi
done

echo "Script finished."
