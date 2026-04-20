#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// -----------------------------------------
// 1. 와이파이 및 MQTT 설정 (여기를 수정하세요)
// -----------------------------------------
const char* ssid = "225";         // 와이파이 이름 (2.4GHz)
const char* password = "123698745"; // 와이파이 비밀번호

const char* mqtt_server = "test.mosquitto.org"; // 모스퀴토 공개 테스트 서버
const int mqtt_port = 1883;
const char* mqtt_topic = "coldchain/truck01/sensor"; // 우리가 보낼 데이터의 제목(방 이름)

// -----------------------------------------
// 객체 생성
// -----------------------------------------
Adafruit_MPU6050 mpu;
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi ");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // 끊기면 재연결 시도하는 로직
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  // 센서 초기화 (기본 SDA: 21, SCL: 22)
  Wire.begin(); 
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) { delay(10); }
  }
  
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // 와이파이 및 MQTT 설정
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 1초마다 데이터 센싱 및 전송
  unsigned long now = millis();
  if (now - lastMsg > 1000) {
    lastMsg = now;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    // 충격량 연산
    float total_accel = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
    float g_force = total_accel / 9.80665; 

    String status = "안전 (정지 상태)";
    if (g_force > 2.0) {
      status = "강한 충돌!! (2G 초과)";
    } else if (g_force > 1.3 || g_force < 0.7) {
      status = "흔들림 / 이동 중";
    }

    // 서버로 보낼 JSON 깡통 만들기
    StaticJsonDocument<200> doc;
    // 소수점 1~2자리로 끊어서 넣기 위해 String 형식 사용
    doc["temperature"] = String(temp.temperature, 1);
    doc["g_force"] = String(g_force, 2);
    doc["status"] = status;

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    // 로그 출력 및 서버로 발사(Publish)
    Serial.print("🚀 발송 완료: ");
    Serial.println(jsonBuffer);
    
    client.publish(mqtt_topic, jsonBuffer);
  }
}
