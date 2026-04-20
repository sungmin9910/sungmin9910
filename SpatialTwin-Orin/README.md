# 🌐 SpatialTwin-Orin (Jetson Edge AI Digital Twin)

NVIDIA Jetson Orin Nano Developer Kit의 강력한 Vision AI 추론과 멀티 센서 퓨전을 활용하여, 물리적 공간의 기하학적 정보와 사람/사물의 상태를 실시간으로 가상 3D 공간에 복제하는 **시맨틱 공간 디지털 트윈(Semantic Spatial Digital Twin)** 시스템입니다.

---

## 🚀 주요 기능 (Key Features)

- **Edge AI 시맨틱 감지**: TensorRT로 최적화된 YOLO 모델을 통해 보드 자체에서 실시간으로 사물 및 인물 인식 (지연시간 최소화)
- **실시간 기하학 동기화**: RGB-D 카메라와 LiDAR 센서 데이터를 융합해 물리적 공간의 구조를 3D 웹(Three.js) 상에 동기화
- **복합 환경 로깅**: 공간의 온도, 습도, 대기질(Gas) 등 환경 센서를 I2C로 제어하여 트윈 데이터에 병합
- **초저지연 통신 레이어**: 대용량 Vision 데이터를 서버로 보내지 않고, 엣지(Jetson)에서 메타데이터(좌표, 객체 종류, 상태)만 추출하여 MQTT로 전송해 대역폭 극강 최적화

---

## 🏗️ 시스템 아키텍처 (Architecture)

1. **Edge Node (NVIDIA Jetson Orin Nano)**
   - **Sensors**: Intel RealSense D435i (Depth 카메라), RPLIDAR (공간 맵핑용), BME680 (환경 센서)
   - **Core**: ROS 2 환경 하에 SLAM 맵핑 + TensorRT 객체 인식
2. **Backend (Server & DB)**
   - FastAPI (Python) + InfluxDB (시계열 환경 데이터) + Redis (실시간 좌표 Pub/Sub)
3. **Digital Twin Monitoring (Web)**
   - React + Three.js + WebGL을 이용한 실시간 3D 공간 렌더링 (사물 이동 실시간 반영)

---

## 📁 디렉토리 구조 (Directory Structure)

```text
.
├── backend/                # 디지털 트윈 서버 및 백엔드 전송
│   ├── main.py             # FastAPI 기반 실시간 트윈 엔진
│   └── twin_dashboard/     # React + Three.js 3D 프론트엔드
├── edge_jetson/            # Jetson Orin Nano 인퍼런스/센서 로직
│   ├── ai_vision/          # TensorRT/YOLO 최적화 파이프라인
│   ├── sensor_fusion/      # ROS2 기반 LiDAR & RealSense 매핑 노드
│   └── mqtt_publisher.py   # 초경량 메타데이터 통신 로직
├── docs/                   # 프로젝트 통합 상세 문서 (관리 표준)
│   ├── 01_Planning/        # 디지털 트윈 아키텍처 기획 및 하드웨어 사양
│   ├── 02_Hardware/        # Jetson Orin 핀맵, 전원 관리, 센서 연결도
│   ├── 03_Software/        # Edge-to-Cloud 데이터 동기화 알고리즘
│   ├── 04_Implementation/  # 시맨틱 데이터 오차율 보정 및 현장 테스트
│   └── 05_Research/        # 시스템 지연율 분석 및 학회 논문/포스터
├── README.md               # 프로젝트 메인 인덱스 및 퀵스타트 가이드
└── .gitignore              
```

---

## 📝 상세 문서 (Full Documentation)

### 01. Planning (기획 및 분석)
- [01_공간_디지털트윈_기획안.md](docs/01_Planning/01_공간_디지털트윈_기획안.md)
- [02_시스템_사양_및_예산.md](docs/01_Planning/02_시스템_사양_및_예산.md)

### 02. Hardware (하드웨어 엔지니어링 및 센서)
- [01_Orin_Nano_핀맵_가이드.md](docs/02_Hardware/01_Orin_Nano_핀맵_가이드.md)
- [02_센서_결선도_및_BOM.md](docs/02_Hardware/02_센서_결선도_및_BOM.md)
- [03_마운팅_하우징_설계.md](docs/02_Hardware/03_마운팅_하우징_설계.md)

### 03. Software (Edge AI & 백엔드 논리)
- [01_TensorRT_최적화_보고서.md](docs/03_Software/01_TensorRT_최적화_보고서.md)
- [02_ROS2_센서퓨전_아키텍처.md](docs/03_Software/02_ROS2_센서퓨전_아키텍처.md)
- [03_초저지연_통신_프로토콜.md](docs/03_Software/03_초저지연_통신_프로토콜.md)

### 04. Implementation (구현 및 실험 검증)
- [01_환경_객체_동기화_테스트.md](docs/04_Implementation/01_환경_객체_동기화_테스트.md)
- [02_발열_및_전력_최적화.md](docs/04_Implementation/02_발열_및_전력_최적화.md)

### 05. Research & Conference (실험 결과 및 논문)
- [01_논문_초록_draft.md](docs/05_Research/01_논문_초록_draft.md)
- [02_학술대회_포스터원고.md](docs/05_Research/02_학술대회_포스터원고.md)

---

## 👤 제작자 (Contributors)
- **연구자 (Research Lead)** - Hardware & System Engineering
- **Antigravity AI (Google DeepMind)** - System Architecture & Code Generation
