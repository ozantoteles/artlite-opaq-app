# Set the source directory and the tarball name
$sourceDir = "D:\Work\plm\Workground\artlite-opaq-app"
$tarball = "D:\Work\plm\Workground\artlite-opaq-app.tar.gz"

# Create a tarball excluding .pyc files, __pycache__ directory, and .git directory
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='.gitignore' --exclude='.vscode' -czf $tarball -C (Split-Path $sourceDir -Parent) (Split-Path $sourceDir -Leaf)

# Define the target machines
$targets = @("192.168.1.108", "192.168.1.109", "192.168.1.111", "192.168.1.117", "192.168.1.118")

# Loop through each target and copy the tarball
foreach ($target in $targets) {
    $destination = "root@${target}:/usr/local"
    scp $tarball $destination
    ssh root@${target} "tar -xzf /usr/local/artlite-opaq-app.tar.gz -C /usr/local/ && rm /usr/local/artlite-opaq-app.tar.gz"
}

# Clean up the local tarball
Remove-Item $tarball
