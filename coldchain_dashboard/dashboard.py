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
    page_title="Cold Chain Premium Monitor",
    page_icon="🚚",
    layout="wide",
)

# 커스텀 CSS로 디자인 강화
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_stdio=True)

# 백그라운드 스레드와 메인 스레드 간 데이터 공유를 위한 큐
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
        # 데이터가 문자열로 올 경우를 대비해 숫자로 변환
        for key in ['temperature', 'humidity', 'lux', 'g_force', 'speed', 'lat', 'lng', 'yaw', 'pitch', 'roll']:
            if key in payload:
                try:
                    payload[key] = float(payload[key])
                except:
                    pass
        msg_queue.put(payload)
    except Exception as e:
        print(f"Error parsing message: {e}")

@st.cache_resource
def start_mqtt_client():
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
st.title("🚚 프리미엄 콜드체인 실시간 통합 관제")
st.markdown(f"**상태:** 데이터 수신 대기 중... (Topic: `{MQTT_TOPIC}`)")

# 레이아웃 설정
m1, m2, m3, m4, m5 = st.columns(5)
temp_metric = m1.empty()
humi_metric = m2.empty()
lux_metric = m3.empty()
gforce_metric = m4.empty()
speed_metric = m5.empty()

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📍 차량 현재 위치 (GPS)")
    map_container = st.empty()
    
    st.subheader("💥 충격량 및 속도 변화")
    gforce_chart = st.empty()

with col_right:
    st.subheader("🌡️ 환경 데이터 모니터링 (온도/습도/조도)")
    env_chart = st.empty()
    
    st.subheader("📋 최근 시스템 로그")
    log_container = st.empty()

# ----------------------------------------------------------------
# 4. 실시간 루프 (데이터 업데이트)
# ----------------------------------------------------------------
while True:
    new_data_received = False
    while not msg_queue.empty():
        msg = msg_queue.get()
        data_history.append(msg)
        new_data_received = True
        if len(data_history) > 100:
            data_history.pop(0)

    if len(data_history) > 0:
        latest = data_history[-1]
        device_type = latest.get('device', 'unknown').upper()
        
        # 상단 메트릭 업데이트
        temp_metric.metric("온도", f"{latest.get('temperature', 0):.1f} °C")
        humi_metric.metric("습도", f"{latest.get('humidity', 0):.1f} %")
        lux_metric.metric("조도", f"{latest.get('lux', 0):.0f} lx")
        gforce_metric.metric("충격량", f"{latest.get('g_force', 0):.2f} G")
        speed_metric.metric("속도", f"{latest.get('speed', 0):.1f} km/h")
        
        # 지도 업데이트
        lat = latest.get('lat', 0)
        lng = latest.get('lng', 0)
        if lat != 0 and lng != 0:
            map_data = pd.DataFrame({'lat': [lat], 'lon': [lng]})
            map_container.map(map_data, zoom=15)
        else:
            map_container.info("GPS 신호를 기다리는 중입니다...")

        # 데이터프레임 변환
        df = pd.DataFrame(data_history)
        df = df.set_index('timestamp')
        
        # 환경 그래프 (온도, 습도, 조도는 스케일이 다르므로 나누거나 조절 필요)
        # 여기서는 온도/습도만 표시하고 조도는 별도로 보거나 스케일링
        env_chart.line_chart(df[['temperature', 'humidity']])
        
        # 충격량 그래프
        gforce_chart.line_chart(df[['g_force', 'speed']])

        # 로그 업데이트
        display_cols = ['device', 'temperature', 'humidity', 'lux', 'g_force', 'status']
        available_cols = [c for c in display_cols if c in df.columns]
        log_container.dataframe(df.iloc[::-1][available_cols].head(10), use_container_width=True)

    time.sleep(1)
