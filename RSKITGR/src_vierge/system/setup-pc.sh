#!/bin/bash

# Check if the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Try using sudo."
    exit 1
fi

# Check that exactly 3 arguments are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <NEW_HOSTNAME> <tunnel_user_on_server> <SSH_port_number_on_server>"
    exit 1
fi

NEW_HOSTNAME="$1"
TUNNEL_USER="$2"
SSH_PORT="$3"

# Validate the hostname
# Only allow letters, numbers, hyphens and underscores, max 63 characters
if [[ ! "$NEW_HOSTNAME" =~ ^[a-zA-Z0-9_-]{1,63}$ ]]; then
    echo "Error: Invalid hostname. Only letters, numbers, '-' and '_' are allowed (max 63 chars)."
    exit 1
fi

# Change hostname immediately
hostnamectl set-hostname "$NEW_HOSTNAME"

# Update /etc/hosts
sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/" /etc/hosts

# Output the parameters for confirmation
echo "Hostname successfully changed to: $NEW_HOSTNAME"
echo "Tunnel user on server: $TUNNEL_USER"
echo "SSH port on server: $SSH_PORT"

echo "Start Tunnel installation..."
(cd /home/user/minimal_novnc/tunnel && ./install_tunnel.sh $TUNNEL_USER $SSH_PORT)
