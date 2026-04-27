import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
from datetime import datetime
import queue

# ----------------------------------------------------------------
# 1. 설정 및 공유 자원 초기화
# ----------------------------------------------------------------
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "coldchain/truck01/sensor"

st.set_page_config(
    page_title="Cold Chain Real-time Monitor",
    page_icon="🚚",
    layout="wide",
)

# 백그라운드 스레드와 메인 스레드 간 데이터 공유를 위한 큐 (캐시 처리)
@st.cache_resource
def get_msg_queue():
    return queue.Queue()

@st.cache_resource
def get_data_history():
    return []

msg_queue = get_msg_queue()
data_history = get_data_history()

# ----------------------------------------------------------------
# 2. MQTT 콜백 설정
# ----------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        payload['timestamp'] = datetime.now().strftime("%H:%M:%S")
        # st.session_state 대신 전역 큐(msg_queue)에 저장
        msg_queue.put(payload)
    except Exception as e:
        print(f"Error parsing message: {e}")

@st.cache_resource
def start_mqtt_client():
    # 최신 paho-mqtt 2.0 호환성 설정
    try:
        from paho.mqtt.client import CallbackAPIVersion
        client = mqtt.Client(CallbackAPIVersion.VERSION1)
    except:
        client = mqtt.Client()
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    return client

mqtt_client = start_mqtt_client()

# ----------------------------------------------------------------
# 3. UI 구성
# ----------------------------------------------------------------
st.title("🚚 콜드체인 실시간 모니터링 시스템")
st.markdown("---")

# 레이아웃 설정
col1, col2, col3, col4 = st.columns(4)
temp_metric = col1.empty()
humi_metric = col2.empty()
gforce_metric = col3.empty()
status_metric = col4.empty()

st.subheader("🌡️ 온도 변화 (°C)")
temp_chart = st.empty()

st.subheader("💧 습도 변화 (%)")
humi_chart = st.empty()

st.subheader("💥 충격량 변화 (G)")
gforce_chart = st.empty()

st.subheader("📋 최근 수신 로그")
log_container = st.empty()

# ----------------------------------------------------------------
# 4. 실시간 루프 (데이터 업데이트)
# ----------------------------------------------------------------
while True:
    while not msg_queue.empty():
        msg = msg_queue.get()
        data_history.append(msg)
        if len(data_history) > 50:
            data_history.pop(0)

    if len(data_history) > 0:
        latest = data_history[-1]
        
        # 상단 메트릭 업데이트
        temp_metric.metric("현재 온도", f"{latest['temperature']} °C")
        humi_metric.metric("현재 습도", f"{latest['humidity']} %")
        gforce_metric.metric("현재 충격량", f"{latest['g_force']} G")
        
        # 상태 표시
        status = latest['status']
        if "충돌" in status:
            status_metric.error(f"⚠️ {status}")
        elif "흔들림" in status:
            status_metric.warning(f"🚚 {status}")
        else:
            status_metric.success(f"✅ {status}")

        # 데이터프레임 변환
        df = pd.DataFrame(data_history)
        df['temperature'] = df['temperature'].astype(float)
        df['humidity'] = df['humidity'].astype(float)
        df['g_force'] = df['g_force'].astype(float)
        df = df.set_index('timestamp')
        
        # 개별 그래프 업데이트
        temp_chart.line_chart(df['temperature'], color="#FF4B4B")
        humi_chart.line_chart(df['humidity'], color="#0072B2")
        gforce_chart.line_chart(df['g_force'], color="#F0A30A")

        # 로그 업데이트
        log_container.table(df.iloc[::-1][['temperature', 'humidity', 'g_force', 'status']].head(10))

    time.sleep(1)
