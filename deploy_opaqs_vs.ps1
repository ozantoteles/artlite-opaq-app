# Set the source directory and the tarball name
$sourceDir = "D:\Work\plm\Workground\artlite-opaq-app"
$tarballName = "artlite-opaq-app.tar.gz"
$tempDir = "D:\Work\plm\Workground\temp-tarball"

# Create a temporary directory
New-Item -ItemType Directory -Force -Path $tempDir

# Create a tarball excluding .pyc files, __pycache__ directory, .git directory, .gitignore, and .vscode
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' --exclude='.gitignore' --exclude='.vscode' -czf "$tempDir\$tarballName" -C (Split-Path $sourceDir -Parent) (Split-Path $sourceDir -Leaf)

# Define the target machines
$targets = @("192.168.1.100", "192.168.1.102", "192.168.1.104", "192.168.1.108", "192.168.1.186")

# Loop through each target and copy the tarball
foreach ($target in $targets) {
    $destination = "root@${target}:/usr/local"
    scp "$tempDir\$tarballName" $destination
    ssh root@${target} "tar -xzf /usr/local/$tarballName -C /usr/local/ && rm /usr/local/$tarballName"
}

# Clean up the local tarball
Remove-Item -Recurse -Force $tempDir
