#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// [설정] 본인의 환경에 맞게 수정
const char* ssid = "225";
const char* password = "123698745";
const String serverName = "http://192.168.0.5:5000/data"; 

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastTime = 0;
unsigned long timerDelay = 10000; // 10초마다 전송

void setup() {
  Serial.begin(115200);
  dht.begin();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected. IP: " + WiFi.localIP().toString());
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {
    if (WiFi.status() == WL_CONNECTED) {
      
      float h = dht.readHumidity();
      float t = dht.readTemperature();

      if (isnan(h) || isnan(t)) {
        Serial.println("Failed to read from DHT sensor!");
      } else {
        StaticJsonDocument<128> doc;
        doc["device_id"] = "ESP32_TEMP_01";
        doc["temperature"] = t;
        doc["humidity"] = h;
        // GPS 정보는 없으므로 null 전송 또는 항목 제외
        doc["latitude"] = nullptr;
        doc["longitude"] = nullptr;

        String jsonOutput;
        serializeJson(doc, jsonOutput);

        HTTPClient http;
        http.begin(serverName);
        http.addHeader("Content-Type", "application/json");
        
        int httpResponseCode = http.POST(jsonOutput);
        Serial.print("HTTP Response: ");
        Serial.println(httpResponseCode); // 201이면 성공
        http.end();
      }
    }
    lastTime = millis();
  }
}