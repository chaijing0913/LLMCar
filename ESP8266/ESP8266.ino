#include <ESP8266WiFi.h>
#include <WiFiClient.h>

// WiFi配置
const char* ssid = "chai";
const char* password = "123456789";

// TCP服务器配置
const char* host = "172.20.10.3";
const uint16_t port = 8089;

WiFiClient client;
String jsonBuffer = "";  // 放到 loop 外，全局变量

void setup() {
  Serial.begin(115200);  // 用作与 Arduino 通讯的串口（不能再当调试口用了）
  delay(1000);         // 稍作延时，等待模块稳定

  // 连接 WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    // 没有调试串口，这里不能打印
  }

  // 连接 TCP 服务器
  if (!client.connect(host, port)) {
    // 无法连接服务器，这里也无法反馈
    return;
  }

  // 测试指令
  client.println("F 30 10");
}

void loop() {
  // 从服务器接收命令 → 发给 Arduino
  if (client.available()) {
    char c = client.read();
    if (c == '\n') {
      jsonBuffer.trim(); // 清理前后空格
      Serial.println(jsonBuffer);  // 发给 Arduino
      jsonBuffer = "";             // 清空，准备下一条
    } else {
      jsonBuffer += c;
    }
    // String command = client.readStringUntil('\n');
    // Serial.print("Forwarding to Arduino: ");
    // Serial.println(command); // 发给 Arduino
    // Serial.flush();
  }

  // // 从 Arduino 接收回传 → 发回服务器（可选）
  // if (Serial.available()) {
  //   String response = Serial.readStringUntil('\n');
  //   client.println(response);
  // }

  //delay(50);
}

