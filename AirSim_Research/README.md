# AirSim Autonomous Driving Research

이 프로젝트는 Microsoft AirSim을 활용하여 자율주행 알고리즘 및 디지털 트윈 시스템을 연구하기 위한 환경입니다.

## 🚀 시작하기 전 준비사항

1. **AirSim 시뮬레이터 설치**
   - [AirSim GitHub Releases](https://github.com/Microsoft/AirSim/releases)에서 `AirSimNH` 또는 `CityEnviron` 바이너리를 다운로드합니다.
   - 압축을 풀고 `.exe` 파일을 실행합니다.

2. **Python 환경 설정**
   - Python 3.8 이상 권장
   - 필요한 라이브러리 설치:
     ```bash
     pip install airsim msgpack-rpc-python numpy opencv-python
     ```

3. **AirSim 설정 파일**
   - `Documents/AirSim/settings.json` 파일에 차량 모드 설정을 확인해야 합니다.

## 📂 프로젝트 구조

- `scripts/`: 자율주행 제어 스크립트 (`connect_test.py` 등)
- `config/`: 시뮬레이터 설정 및 모델 파라미터
- `data/`: 시뮬레이터에서 수집된 센서 데이터 (카메라, LiDAR 등)

## 🛠️ 주요 목표
- [ ] AirSim-Python API 연결 테스트
- [ ] 카메라 및 LiDAR 센서 데이터 실시간 수집
- [ ] OpenCV를 활용한 장애물 인식
- [ ] 자율주행 로직 구현 (Path Planning & Avoidance)
