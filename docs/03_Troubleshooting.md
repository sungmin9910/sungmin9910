# 🛠️ Jetson Orin Nano 환경 구축 트러블슈팅 가이드

JetPack 6.2 (Ubuntu 22.04) 환경에서 RealSense D455와 YOLOv8을 구축하며 겪은 주요 문제와 해결 방법을 정리합니다.

## 1. 메모리 부족으로 인한 빌드 멈춤 (OutOfMemory)
`librealsense`를 소스 빌드할 때 젯슨의 기본 8GB 램이 부족하여 시스템이 멈추는 현상이 발생했습니다.

- **해결방법**: 4GB 가상 메모리(Swap)를 생성하여 컴파일 안정성을 확보했습니다.
```bash
sudo fallocate -l 4G /swapfile_temp
sudo chmod 600 /swapfile_temp
sudo mkswap /swapfile_temp
sudo swapon /swapfile_temp
```
- **빌드 옵션**: `make -j2`를 사용하여 CPU 부하를 조절했습니다.

## 2. CUDA 컴파일러(nvcc) 경로 인식 오류
CMake 설정 중 `No CMAKE_CUDA_COMPILER could be found` 에러가 발생했습니다.

- **해결방법**: CUDA 환경 변수를 명시적으로 설정해주었습니다.
```bash
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

## 3. PyTorch 실행 시 부족한 공유 라이브러리 (libcudss, libcusparseLt)
가상 환경에서 PyTorch를 실행할 때 특정 `.so` 파일을 찾지 못하는 `ImportError`가 발생했습니다.

- **해결방법**: NVIDIA 공식 서버에서 해당 라이브러리 아카이브를 내려받아 `/usr/local/cuda/` 경로에 수동으로 복사했습니다.
- **관련 스크립트**: `edge_jetson/install_cuda_libs.sh` 참조

## 4. RealSense 카메라 권한 문제
`rs-enumerate-devices` 실행 시 카메라를 인식하지 못하거나 권한 에러가 발생했습니다.

- **해결방법**: `udev` 규칙을 복사하고 시스템에 적용했습니다.
```bash
sudo cp ~/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && udevadm trigger
```

---
> [!TIP]
> 젯슨에서 새로운 가상 환경을 만들 때는 반드시 `python3 -m venv <name>` 이후 `source <name>/bin/activate` 절차를 지켜야 하며, PyTorch 설치 시 젯슨 전용 인덱스(`https://pypi.jetson-ai-lab.io/jp6/cu126`)를 사용해야 합니다.
