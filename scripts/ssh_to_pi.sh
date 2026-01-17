#!/bin/bash

# SSH connection script to Raspberry Pi

# Default values
USERNAME="pi"
HOSTNAME="raspberrypi.local"
PASSWORD="raspberry"

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is not installed."
    echo "Install it with: sudo apt-get install sshpass"
    exit 1
fi

# SSH connection with bash shell using password
echo "Connecting to $USERNAME@$HOSTNAME..."
sshpass -p "$PASSWORD" ssh "$USERNAME@$HOSTNAME"