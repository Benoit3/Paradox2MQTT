# Paradox2MQTT
MQTT interface for Paradox PRT3 module written in python 

Today, allow to get status of Area and Zone, so trigger utility keys, but not to ARM & DISARM Area

TODO: documentation, feature to ARM & DISARM

Need python3-serial: sudo apt-get install python3-serial

To test and run it:
- set parameters in conf file
- python3 Paradox2MQTT.py


To run as a service on raspbian:

as root, copy and adapt Paradox2MQTT.service to /etc/systemd/system/ directory

sudo chmod 644 /etc/systemd/system/Paradox2MQTT.service

chmod +x /home/pi/Diematic32MQTT/Paradox2MQTT.py

sudo systemctl daemon-reload

sudo systemctl enable Paradox2MQTT.service

sudo systemctl start Paradox2MQTT.service
