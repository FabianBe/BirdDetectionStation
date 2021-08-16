#!/usr/bin/env bash

set -e

echo 'Update package manager'
sudo apt update

echo 'Install prerequirements'
sudo apt install -y git cmake alsa-utils alsa-base libportaudio2 libffi-dev libatlas-base-dev gfortran python3-dev python3-venv python3-cffi python3-scipy nodejs npm 

echo 'Create virtual environment > python3 -m venv ./bird_detection_station/.venv '
python3 -m venv ./bird_detection_station/.venv 

echo 'Activate virtual enviornment > source ./bird_detection_station/.venv/bin/activate'
source ./bird_detection_station/.venv/bin/activate

echo 'Install Python packages > pip install --no-cache-dir -r ./bird_detection_station/requirements.txt'
pip install --no-cache-dir -r ./bird_detection_station/requirements.txt

echo 'Install npm dependencies > npm install --unsafe-perm --prefix ./bird_classification'
sudo npm install --unsafe-perm --prefix ./bird_classification

echo 'Install tensorflow > npm rebuild @tensorflow/tfjs-node --build-from-source --prefix ./bird_classification'
sudo npm rebuild @tensorflow/tfjs-node --build-from-source --prefix ./bird_classification

echo 'Compile Typescript files > npm run-script build --prefix ./bird_classification'
sudo npm run-script build --prefix ./bird_classification

echo 'Create systemd units'
cat <<EOT > /etc/systemd/system/bird_station.service
[Unit]
Description=Python bird station service

[Service]
WorkingDirectory=$(pwd)/bird_detection_station
ExecStart=$(pwd)/bird_detection_station/.venv/bin/python -m bird_detection.main --serve-in-foreground
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOT

sudo systemctl enable bird_station.service

cat <<EOT > /etc/systemd/system/bird_detection.service
[Unit]
Description=node bird detection service

[Service]
WorkingDirectory=$(pwd)/bird_classification
ExecStart=/usr/bin/npm start

Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOT

sudo systemctl enable bird_detection.service

echo "Installation successful. The pi is going to restart"
sudo shutdown -r now