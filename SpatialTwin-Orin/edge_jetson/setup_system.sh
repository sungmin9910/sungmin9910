#!/bin/bash
# setup_system.sh - SpatialTwin-Orin Basic Setup for JetPack 6.2

echo "--- [1/3] System Update & Upgrade ---"
sudo apt update && sudo apt upgrade -y

echo "--- [2/3] Installing Essential Build Tools ---"
sudo apt install -y git cmake python3-pip libssl-dev libusb-1.0-0-dev \
pkg-config libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev

echo "--- [3/3] Installing System Monitoring Tools (jtop) ---"
sudo pip3 install -U jetson-stats

echo "-------------------------------------------------------"
echo "설치가 완료되었습니다!"
echo "1. 'sudo reboot'를 실행하여 시스템을 재부팅해 주세요."
echo "2. 재부팅 후 'jtop' 명령어를 입력하여 시스템 상태를 확인할 수 있습니다."
echo "-------------------------------------------------------"
