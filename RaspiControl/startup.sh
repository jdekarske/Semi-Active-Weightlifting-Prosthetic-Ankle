#!/bin/sh
# startup.sh
#enable bluetooth
#sudo systemctl start bluetooth

#sleep 1

#turn on bluetooth
echo  'power on\ndiscoverable on\nquit' | bluetoothctl

sleep 1

#start script
cd /home/pi/semi-active-weightlifting-prosthetic-ankle/RaspiControl
sudo python menu.py

