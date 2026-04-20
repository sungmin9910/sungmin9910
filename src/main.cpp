#include <WiFi.h>
#include <MySQL_Generic.h>
#include <HTTPClient.h>

// --- 설정 (한성민 님의 환경에 맞게 수정) ---
const char* ssid = "225";
const char* password = "123698745";

IPAddress server_addr(203,254,153,113); // DB 호스트 IP
uint16_t db_port = 3307;
char user[] = "root";
char password_db[] = "Lab22512251!";
char db[] = "lab225";

// UART2 (DE2110 연결)
HardwareSerial ScannerSerial(2);

// DB 객체
MySQL_Connection conn((Client *)&client);
MySQL_Query *query_mem;
// WiFiClient client; 는 MySQL_Generic.h에 이미 포함되어 있으므로 삭제합니다.

void setup() {
  Serial.begin(115200);
  ScannerSerial.begin(115200, SERIAL_8N1, 16, 17); // RX:16, TX:17

  // Wi-Fi 연결
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

// URL에서 쿼리 파라미터 추출 함수 (Python의 parse_qs 역할)
String getQueryParam(String url, String param) {
  int start = url.indexOf(param + "=");
  if (start == -1) return "NULL";
  start += param.length() + 1;
  int end = url.indexOf("&", start);
  if (end == -1) end = url.length();
  return "'" + url.substring(start, end) + "'";
}

// FmID 추출 (URL의 마지막 세그먼트)
String getFmID(String url) {
  int lastSlash = url.lastIndexOf('/');
  int questionMark = url.indexOf('?');
  if (questionMark == -1) return "'" + url.substring(lastSlash + 1) + "'";
  return "'" + url.substring(lastSlash + 1, questionMark) + "'";
}

void saveToDatabase(String rawUrl) {
  if (conn.connect(server_addr, db_port, user, password_db)) {
    delay(500);
    MySQL_Query query_executor(&conn);

    // 1. 최신 GPS 정보 가져오기
    String gps_query = "SELECT latitude, longitude FROM gps_log ORDER BY recorded_at DESC LIMIT 1";
    query_executor.execute(gps_query.c_str());
    
    column_names *cols = query_executor.get_columns();
    row_values *row = query_executor.get_next_row();
    String lat = "NULL", lon = "NULL";
    if (row != NULL) {
      lat = row->values[0];
      lon = row->values[1];
    }

    // 2. 데이터 파싱 및 INSERT 쿼리 생성
    // Python 코드의 로직을 그대로 따름 (Lo: A10 고정)
    String fmId = getFmID(rawUrl);
    String ac = getQueryParam(rawUrl, "AC");
    String frt = getQueryParam(rawUrl, "FrT");
    String vt = getQueryParam(rawUrl, "Vt");
    String ct = getQueryParam(rawUrl, "Ct");
    String hd = getQueryParam(rawUrl, "HD");
    String dd = getQueryParam(rawUrl, "DD");
    String qt = getQueryParam(rawUrl, "Qt");
    String mt = getQueryParam(rawUrl, "Mt");
    String hn = getQueryParam(rawUrl, "HN");
    String std = getQueryParam(rawUrl, "StD");
    String rp = getQueryParam(rawUrl, "Rp");

    String insert_query = "INSERT INTO lab225.qr (Lo, AC, FmID, FrT, Vt, Ct, HD, DD, Qt, Mt, HN, StD, Rp, APC_AD, Lat, lon) VALUES ";
    insert_query += "('A10', " + ac + ", " + fmId + ", " + frt + ", " + vt + ", " + ct + ", " + hd + ", " + dd + ", " + qt + ", " + mt + ", " + hn + ", " + std + ", " + rp + ", NOW(), " + lat + ", " + lon + ")";

    // 3. 실행
    if (query_executor.execute(insert_query.c_str())) {
      Serial.println("✅ A10 데이터가 DB에 저장되었습니다.");
    } else {
      Serial.println("❌ DB 저장 실패");
    }
    conn.close();
  } else {
    Serial.println("❌ DB 연결 실패");
  }
}

void loop() {
  if (ScannerSerial.available()) {
    String scannedData = ScannerSerial.readStringUntil('\r');
    scannedData.trim();

    if (scannedData.length() > 0) {
      Serial.println("📷 스캔된 데이터: " + scannedData);
      saveToDatabase(scannedData);
    }
  }
}