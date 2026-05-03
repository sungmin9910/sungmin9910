# 🚚 MQTT 기반 실시간 콜드체인 모니터링 대시보드

ESP32와 각종 센서(MPU6050, DHT11)로부터 수집된 데이터를 MQTT 통신을 통해 실시간으로 시각화하는 파이썬 기반 대시보드 프로젝트입니다.

## 📋 프로젝트 개요
신선 식품 유통(Cold Chain) 과정에서 발생하는 **온도, 습도 변화**와 외부 충격에 의한 **G-Force(충격량)**를 실시간으로 모니터링하여 화물의 안전 상태를 확인합니다.

## 🛠️ 주요 구성
- **Device**: ESP32-S3 (Arduino framework)
- **Sensors**: MPU6050 (가속도/자이로), DHT11 (온습도)
- **Communication**: MQTT (Broker: `broker.emqx.io`)
- **Dashboard**: Python (Streamlit), Pandas, Paho-MQTT

## 🚀 대시보드 주요 기능
- **실시간 메트릭**: 현재 온도, 습도, 충격량 수치 표시
- **환경 데이터 그래프**: 온도와 습도의 변화 추이를 하나의 차트로 비교
- **충격량 추적**: 물리적 충격을 독립적인 그래프로 모니터링
- **상태 알림**: 차량의 이동/정지 및 충돌 발생 시 즉시 상태 배지 업데이트 (녹색/황색/적색)
- **데이터 로그**: 최근 수신된 10개의 데이터 상세 내역 표시

## 💻 로컬 실행 방법
1. **필수 라이브러리 설치**:
   ```bash
   pip install streamlit paho-mqtt pandas
   ```
2. **대시보드 실행**:
   ```bash
   streamlit run dashboard.py
   ```

## 🌐 외부 공유 (Streamlit Cloud 배포)
이 대시보드는 Streamlit Cloud를 통해 전 세계 어디서든 접속 가능한 웹사이트로 배포할 수 있습니다.

1. **GitHub 업로드**: `dashboard.py`, `requirements.txt` 파일을 저장소에 업로드합니다.
2. **Streamlit Cloud 연결**: [Streamlit Cloud](https://streamlit.io/cloud)에 로그인 후 GitHub 저장소를 연동합니다.
3. **배포**: 저장소와 메인 파일(`dashboard.py`)을 선택하고 **Deploy** 버튼을 누릅니다.

## 🔌 하드웨어 동작 방식
- ESP32에 전원만 인가하면 설정된 WiFi에 자동으로 접속합니다.
- MQTT 브로커에 접속하여 1초마다 센서 데이터를 JSON 형식으로 발행(Publish)합니다.
- 대시보드는 해당 토픽을 구독(Subscribe)하여 실시간으로 UI를 갱신합니다.
