#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

apt update
apt install -y rsync nginx terminator
sudo apt install python-is-python3
sudo apt install can-utils
sudo apt install net-tools -y
sudo apt install openssh-server -y
sudo snap install --classic code
sudo apt install docker-compose -y

# install all files
cp -R etc usr /

# set executable flag for scripts
chmod a+x /usr/sbin/*

# Reload udev rules
udevadm control --reload-rules && udevadm trigger

# Install services
systemctl enable ros.service
systemctl start ros.service

