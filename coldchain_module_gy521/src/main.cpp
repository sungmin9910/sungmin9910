#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
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
Adafruit_MPU6050 mpu;
Adafruit_SHT4x sht4 = Adafruit_SHT4x();
BH1750 lightMeter;
TinyGPSPlus gps;

// GPS는 Serial2 사용 (RX: 16, TX: 17)
#define GPS_SERIAL Serial2

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

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
    String clientId = "ESP32-GY521-";
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
  GPS_SERIAL.begin(9600, SERIAL_8N1, 16, 17); // GPS 초기화
  
  Wire.begin(); 

  // 1. MPU6050 초기화
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
  } else {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }

  // 2. SHT4x 초기화
  if (!sht4.begin()) {
    Serial.println("Couldn't find SHT4x sensor");
  } else {
    sht4.setPrecision(SHT4X_HIGH_PRECISION);
    sht4.setHeater(SHT4X_NO_HEATER);
  }

  // 3. BH1750 초기화
  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Error initialising BH1750");
  }

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // GPS 데이터 파싱
  while (GPS_SERIAL.available() > 0) {
    gps.encode(GPS_SERIAL.read());
  }

  // 1초마다 데이터 센싱 및 전송
  unsigned long now = millis();
  if (now - lastMsg > 1000) {
    lastMsg = now;

    // 가속도 및 충격량 계산
    sensors_event_t a, g, temp_mpu;
    mpu.getEvent(&a, &g, &temp_mpu);
    float total_accel = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
    float g_force = total_accel / 9.80665; 

    // SHT45 온습도
    sensors_event_t humidity, temp_sht;
    sht4.getEvent(&humidity, &temp_sht);

    // BH1750 조도
    float lux = lightMeter.readLightLevel();

    // 상태 판별
    String status = "안전";
    if (g_force > 2.0) status = "강한 충돌!!";
    else if (g_force > 1.3 || g_force < 0.7) status = "이동/진동";

    // JSON 구성
    StaticJsonDocument<512> doc;
    doc["device"] = "gy521";
    doc["temperature"] = String(temp_sht.temperature, 2);
    doc["humidity"] = String(humidity.relative_humidity, 2);
    doc["lux"] = String(lux, 1);
    doc["g_force"] = String(g_force, 2);
    
    if (gps.location.isValid()) {
      doc["lat"] = String(gps.location.lat(), 6);
      doc["lng"] = String(gps.location.lng(), 6);
      doc["speed"] = String(gps.speed.kmph(), 1);
    } else {
      doc["lat"] = "0.0";
      doc["lng"] = "0.0";
    }
    
    doc["status"] = status;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);
    Serial.println(jsonBuffer);
    client.publish(mqtt_topic, jsonBuffer);
  }
}
