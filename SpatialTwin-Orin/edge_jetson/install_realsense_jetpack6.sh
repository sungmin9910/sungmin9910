#!/bin/bash
# install_realsense_jetpack6.sh - Build librealsense with RSUSB Backend

# 의존성 설치 확인
sudo apt update
sudo apt install -y libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev

# 작업 디렉토리 생성
cd ~
if [ -d "librealsense" ]; then
    echo "Existing librealsense directory found. Updating..."
    cd librealsense && git pull
else
    git clone https://github.com/IntelRealSense/librealsense.git
    cd librealsense
fi

# 빌드 설정 (RSUSB 백엔드 사용 - 커널 패치 불필요)
mkdir -p build && cd build
cmake .. \
    -DFORCE_RSUSB_BACKEND=ON \
    -DBUILD_PYTHON_BINDINGS:bool=true \
    -DCMAKE_BUILD_TYPE=release \
    -DBUILD_EXAMPLES=true \
    -DBUILD_WITH_CUDA:bool=true

# 빌드 및 설치 (젯슨 오린 나노의 멀티코어 활용)
echo "빌드를 시작합니다. 이 작업은 약 30분 이상 소요될 수 있습니다..."
make -j$(nproc)
sudo make install

# udev 규칙 설정
sudo cp ../config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && udevadm trigger

# 파이썬 경로 설정 안내
echo "-------------------------------------------------------"
echo "RealSense SDK 설치가 완료되었습니다!"
echo "Bash 설정에 다음 문구를 추가하면 좋습니다 (필요 시):"
echo "export PYTHONPATH=\$PYTHONPATH:/usr/local/lib"
echo ""
echo "이제 'realsense-viewer'를 입력하여 카메라가 인식되는지 테스트해보세요."
echo "-------------------------------------------------------"
