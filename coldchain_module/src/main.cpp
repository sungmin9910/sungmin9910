#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

#define I2C_SDA 21
#define I2C_SCL 22

void setup() {
  Serial.begin(115200);
  while (!Serial)
    delay(10); // will pause Zero, Leonardo, etc until serial console opens

  Serial.println("Adafruit MPU6050 test!");

  // Initialize I2C with specified pins
  Wire.begin(I2C_SDA, I2C_SCL);

  // Initialize MPU6050
  if (!mpu.begin(0x68, &Wire, 0)) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
  case MPU6050_RANGE_2_G:
    Serial.println("+-2G");
    break;
  case MPU6050_RANGE_4_G:
    Serial.println("+-4G");
    break;
  case MPU6050_RANGE_8_G:
    Serial.println("+-8G");
    break;
  case MPU6050_RANGE_16_G:
    Serial.println("+-16G");
    break;
  }
  
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
  case MPU6050_RANGE_250_DEG:
    Serial.println("+- 250 deg/s");
    break;
  case MPU6050_RANGE_500_DEG:
    Serial.println("+- 500 deg/s");
    break;
  case MPU6050_RANGE_1000_DEG:
    Serial.println("+- 1000 deg/s");
    break;
  case MPU6050_RANGE_2000_DEG:
    Serial.println("+- 2000 deg/s");
    break;
  }

  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
  case MPU6050_BAND_260_HZ:
    Serial.println("260 Hz");
    break;
  case MPU6050_BAND_184_HZ:
    Serial.println("184 Hz");
    break;
  case MPU6050_BAND_94_HZ:
    Serial.println("94 Hz");
    break;
  case MPU6050_BAND_44_HZ:
    Serial.println("44 Hz");
    break;
  case MPU6050_BAND_21_HZ:
    Serial.println("21 Hz");
    break;
  case MPU6050_BAND_10_HZ:
    Serial.println("10 Hz");
    break;
  case MPU6050_BAND_5_HZ:
    Serial.println("5 Hz");
    break;
  }

  Serial.println("");
  delay(100);
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 1. 총 가속도(백터의 크기) 계산
  // X, Y, Z축 값을 하나로 합쳐서 센서 전체가 받는 힘을 계산합니다.
  float total_accel = sqrt(pow(a.acceleration.x, 2) + pow(a.acceleration.y, 2) + pow(a.acceleration.z, 2));
  
  // 2. 충격량(G-Force)으로 변환 (지구 표면의 기본 중력은 1G = 약 9.8m/s^2)
  float g_force = total_accel / 9.80665; 

  // 3. 화물 상태 판별 판단
  String status = "🟢 안전 (정지 상태)";
  if (g_force > 2.0) {
    status = "🚨 낙하 또는 강한 충돌!! (2G 이상)";
  } else if (g_force > 1.3 || g_force < 0.7) {
    status = "🟡 흔들림 / 차량 이동 중";
  }

  // 4. 보기 쉽게 시리얼 모니터에 출력
  Serial.println("=========================================");
  Serial.print("🌡️ 온도      : ");
  Serial.print(temp.temperature, 1);
  Serial.println(" °C");

  Serial.print("💥 받은 충격 : ");
  Serial.print(g_force, 2); // 소수점 2자리까지만 출력
  Serial.println(" G (기본=1G)");

  Serial.print("📦 화물 상태 : ");
  Serial.println(status);
  Serial.println("=========================================\n");

  delay(1000); // 눈으로 읽기 편하도록 1초에 한 번만 출력
}
