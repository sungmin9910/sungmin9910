#!/bin/bash
# install_cuda_libs.sh - Manual installation of cuDSS and cuSPARSELt for JetPack 6.2
# This script automates the fixes we applied to resolve 'libcudss.so.0' and 'libcusparseLt.so.0' missing errors.

echo "--- [1/2] Installing cuDSS (0.7.1.4) ---"
wget https://developer.download.nvidia.com/compute/cudss/redist/libcudss/linux-aarch64/libcudss-linux-aarch64-0.7.1.4_cuda12-archive.tar.xz
tar xf libcudss-linux-aarch64-0.7.1.4_cuda12-archive.tar.xz
sudo cp -a libcudss-linux-aarch64-0.7.1.4_cuda12-archive/include/* /usr/local/cuda/include/
sudo cp -a libcudss-linux-aarch64-0.7.1.4_cuda12-archive/lib/* /usr/local/cuda/lib64/
rm -rf libcudss-linux-aarch64-0.7.1.4_cuda12-archive*

echo "--- [2/2] Installing cuSPARSELt (0.6.2.3) ---"
wget https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-aarch64/libcusparse_lt-linux-aarch64-0.6.2.3-archive.tar.xz
tar xf libcusparse_lt-linux-aarch64-0.6.2.3-archive.tar.xz
sudo cp -a libcusparse_lt-linux-aarch64-0.6.2.3-archive/include/* /usr/local/cuda/include/
sudo cp -a libcusparse_lt-linux-aarch64-0.6.2.3-archive/lib/* /usr/local/cuda/lib64/
rm -rf libcusparse_lt-linux-aarch64-0.6.2.3-archive*

echo "--- Updating Linker Cache ---"
sudo ldconfig

echo "Done. Please restart your python script or virtual environment."
