#include <WiFi.h>
#include <ModbusIP_ESP8266.h>
#include <DHT.h>

#define DHTPIN 4     // DHT22数据引脚
#define DHTTYPE DHT22

const char* ssid = "vivo X80";
const char* password = "12345678";

ModbusIP mb;
DHT dht(DHTPIN, DHTTYPE);

// Modbus寄存器地址
#define TEMP_REG 0
#define HUMID_REG 1

void setup() {
  Serial.begin(115200);
  
  // 连接WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // 初始化Modbus TCP服务器
  mb.server();
  
  // 添加Holding寄存器(可读可写)
  mb.addHreg(TEMP_REG, 0);
  mb.addHreg(HUMID_REG, 0);
  
  // 初始化DHT传感器
  dht.begin();
}

void loop() {
  // 处理Modbus通信
  mb.task();
  
  // 每2秒读取一次传感器数据
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 2000) {
    lastRead = millis();
    
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    
    if (!isnan(temperature) && !isnan(humidity)) {
      // 将浮点数转换为整数并放大100倍保持2位小数精度
      mb.Hreg(TEMP_REG, (int)(temperature * 100));
      mb.Hreg(HUMID_REG, (int)(humidity * 100));
      
      Serial.printf("Temperature: %.2f°C, Humidity: %.2f%%\n", temperature, humidity);
    } else {
      Serial.println("Failed to read from DHT sensor!");
    }
  }
  
  delay(10);
}