#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SHT4x.h>
#include <BH1750.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// -----------------------------------------
// 1. 와이파이 및 MQTT 설정
// -----------------------------------------
const char* ssid = "225";
const char* password = "123698745";
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;
const char* mqtt_topic = "coldchain/truck01/sensor";

// -----------------------------------------
// 객체 및 핀 설정
// -----------------------------------------
Adafruit_SHT4x sht4 = Adafruit_SHT4x();
BH1750 lightMeter;
TinyGPSPlus gps;

// 센서별 시리얼 설정
#define GPS_SERIAL Serial2  // RX: 16, TX: 17 (고정)
#define GY25_SERIAL Serial1 // RX: 13, TX: 12 (커스텀 맵핑)

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
float yaw, pitch, roll;

void setup_wifi() {
  delay(10);
  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32-GY25-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("connected!");
      // GY-25 자동 출력 모드로 설정
      GY25_SERIAL.write(0xA5);
      GY25_SERIAL.write(0x52);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// GY-25 시리얼 데이터 파싱
void parseGY25() {
  static uint8_t buffer[8];
  static uint8_t counter = 0;

  while (GY25_SERIAL.available()) {
    uint8_t c = GY25_SERIAL.read();
    
    if (counter == 0 && c != 0xAA) continue; // 헤더 대기
    
    buffer[counter++] = c;
    
    if (counter == 8) {
      if (buffer[7] == 0x55) {
        int16_t y_raw = (buffer[1] << 8) | buffer[2];
        int16_t p_raw = (buffer[3] << 8) | buffer[4];
        int16_t r_raw = (buffer[5] << 8) | buffer[6];
        
        yaw = y_raw / 100.0;
        pitch = p_raw / 100.0;
        roll = r_raw / 100.0;
      }
      counter = 0;
    }
  }
}

void setup() {
  Serial.begin(115200);
  GPS_SERIAL.begin(9600, SERIAL_8N1, 16, 17);
  GY25_SERIAL.begin(115200, SERIAL_8N1, 13, 12); // GY-25는 대개 115200 (안되면 9600 확인)
  
  Wire.begin(); 

  // 1. SHT4x 초기화
  if (!sht4.begin()) {
    Serial.println("Couldn't find SHT4x sensor");
  } else {
    sht4.setPrecision(SHT4X_HIGH_PRECISION);
    sht4.setHeater(SHT4X_NO_HEATER);
  }

  // 2. BH1750 초기화
  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Error initialising BH1750");
  }

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  // GY-25 초기 설정 (자동 출력 모드)
  GY25_SERIAL.write(0xA5);
  GY25_SERIAL.write(0x52);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 센서 데이터 수신
  while (GPS_SERIAL.available() > 0) gps.encode(GPS_SERIAL.read());
  parseGY25();

  // 1초마다 데이터 센싱 및 전송
  unsigned long now = millis();
  if (now - lastMsg > 1000) {
    lastMsg = now;

    // SHT45 온습도
    sensors_event_t humidity, temp_sht;
    sht4.getEvent(&humidity, &temp_sht);

    // BH1750 조도
    float lux = lightMeter.readLightLevel();

    // JSON 구성
    StaticJsonDocument<512> doc;
    doc["device"] = "gy25";
    doc["temperature"] = String(temp_sht.temperature, 2);
    doc["humidity"] = String(humidity.relative_humidity, 2);
    doc["lux"] = String(lux, 1);
    
    // 각도 정보 추가
    doc["yaw"] = String(yaw, 2);
    doc["pitch"] = String(pitch, 2);
    doc["roll"] = String(roll, 2);
    
    if (gps.location.isValid()) {
      doc["lat"] = String(gps.location.lat(), 6);
      doc["lng"] = String(gps.location.lng(), 6);
      doc["speed"] = String(gps.speed.kmph(), 1);
    } else {
      doc["lat"] = "0.0";
      doc["lng"] = "0.0";
    }
    
    // GY-25는 각도로 상태 판별 (예: 45도 이상 기울어지면 전복 위험)
    String status = "안전 (수평)";
    if (abs(pitch) > 30.0 || abs(roll) > 30.0) status = "⚠️ 전복/기울어짐 위험!";

    doc["status"] = status;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);
    Serial.println(jsonBuffer);
    client.publish(mqtt_topic, jsonBuffer);
  }
}
