#!/bin/bash
# Jetson JetPack Version & System Info Checker

echo "--- Jetson System Information ---"
# Check JetPack Version
if [ -f /etc/nv_tegra_release ]; then
    cat /etc/nv_tegra_release
fi

# Check L4T Version
if command -v jtop &> /dev/null; then
    jtop --version
else
    echo "jtop not installed. You can install it with: sudo pip3 install jetson-stats"
fi

# Check JetPack via apt
sudo apt-cache show nvidia-jetpack | grep Version

# Check Python Version
python3 --version

# Check OpenCV
python3 -c "import cv2; print('OpenCV Version:', cv2.__version__)"

# Check CUDA
if [ -d /usr/local/cuda ]; then
    /usr/local/cuda/bin/nvcc --version
else
    echo "CUDA not found in /usr/local/cuda"
fi
