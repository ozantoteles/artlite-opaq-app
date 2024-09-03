#!/bin/bash
 

 
# Function to handle the operations for a single target
process_target() {
  local target=$1
  #echo "Copying to $target..."
  #eval $(printf "$COPY_CMD" "$target")
  #echo "Extracting on $target..."
  #ssh -o ForwardX11=no root@$target "tar -xzf /usr/local/$TARBALL_NAME -C /usr/local/ && rm /usr/local/$TARBALL_NAME"
  #echo "Done with $target."
  echo "Setting up bootdelay to 0 on $target..."
  ssh -o ForwardX11=no root@$target "fw_setenv bootdelay 0"
  ssh -o ForwardX11=no root@$target "fw_printenv bootdelay"
  echo "Setting up bootdelay done on $target"
}

# Loop through each target and copy the tarball in parallel
for target in 192.168.1.100 192.168.1.104 192.168.1.108 192.168.1.109 192.168.1.110 192.168.1.114 192.168.1.115 192.168.1.116 192.168.1.118 192.168.1.120 192.168.1.121 192.168.1.122 192.168.1.123 192.168.1.125 192.168.1.126 192.168.1.127 192.168.1.128 192.168.1.129 192.168.1.130 192.168.1.131 192.168.1.132 192.168.1.186; do
  process_target $target 
done

# Wait for all background processes to complete
wait

# Clean up the local tarball
rm -r $TEMP_DIR
 
echo "All tasks completed."
