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

st.subheader("📈 센서 데이터 추이")
chart_container = st.empty()

st.subheader("📋 최근 수신 로그")
log_container = st.empty()

# ----------------------------------------------------------------
# 4. 실시간 루프 (데이터 업데이트)
# ----------------------------------------------------------------
# Streamlit은 스크립트가 끝까지 실행되면 멈추므로 무한 루프를 통해 업데이트 유지
while True:
    new_data_received = False
    
    # 큐에서 새로운 메시지 모두 꺼내기
    while not msg_queue.empty():
        msg = msg_queue.get()
        data_history.append(msg)
        
        # 최대 50개 데이터만 유지
        if len(data_history) > 50:
            data_history.pop(0)
        new_data_received = True

    if len(data_history) > 0:
        latest = data_history[-1]
        
        # 상단 메트릭 업데이트
        temp_metric.metric("온도 (DHT11)", f"{latest['temperature']} °C")
        humi_metric.metric("습도 (DHT11)", f"{latest['humidity']} %")
        gforce_metric.metric("충격량 (G-Force)", f"{latest['g_force']} G")
        
        # 상태에 따른 강조 표시
        status = latest['status']
        if "충돌" in status:
            status_metric.error(f"⚠️ {status}")
        elif "흔들림" in status:
            status_metric.warning(f"🚚 {status}")
        else:
            status_metric.success(f"✅ {status}")

        # 차트 데이터 준비 및 그리기
        df = pd.DataFrame(data_history)
        df['temperature'] = df['temperature'].astype(float)
        df['humidity'] = df['humidity'].astype(float)
        df['g_force'] = df['g_force'].astype(float)
        
        chart_container.line_chart(df.set_index('timestamp')[['temperature', 'humidity', 'g_force']])

        # 로그 업데이트 (최근 10개)
        log_container.table(df.iloc[::-1][['timestamp', 'temperature', 'humidity', 'g_force', 'status']].head(10))

    time.sleep(1)  # 1초마다 화면 갱신
