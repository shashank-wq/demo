// ESP32 -> FastAPI. Sensors: capacitive soil-moisture probe (analog) + DHT22 (temp/humidity).
// Libraries (Arduino Library Manager): "DHT sensor library" + "Adafruit Unified Sensor", ArduinoJson.
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASSWORD";
const char* API_URL   = "http://192.168.1.10:8000/readings";  // your PC's IP, not localhost
const char* API_KEY   = "change-me";
const char* DEVICE    = "godown-1";                            // create it first via POST /devices

const int MOISTURE_PIN = 34;
const int DHT_PIN = 4;
DHT dht(DHT_PIN, DHT22);

// CALIBRATION: read raw values with the probe in dry air and in samples of known moisture,
// then fill these in. Probe readings do NOT equal grain moisture % until calibrated.
const int RAW_DRY = 3200, RAW_WET = 1400;
const float PCT_AT_DRY = 8.0, PCT_AT_WET = 24.0;

float rawToPercent(int raw) {
  float t = float(raw - RAW_DRY) / float(RAW_WET - RAW_DRY);
  return constrain(PCT_AT_DRY + t * (PCT_AT_WET - PCT_AT_DRY), 0, 100);
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi connected");
}

void loop() {
  long sum = 0;
  for (int i = 0; i < 10; i++) { sum += analogRead(MOISTURE_PIN); delay(20); }  // average noise
  float moisture = rawToPercent(sum / 10);
  float temp = dht.readTemperature(), hum = dht.readHumidity();

  if (!isnan(temp) && !isnan(hum)) {
    JsonDocument doc;
    doc["device"] = DEVICE; doc["moisture"] = moisture; doc["temperature"] = temp; doc["humidity"] = hum;
    String body; serializeJson(doc, body);

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);
    int code = http.POST(body);
    Serial.printf("POST %d: %s\n", code, body.c_str());
    http.end();
  } else {
    Serial.println("DHT read failed");
  }
  delay(30000);  // one reading every 30 s
}
