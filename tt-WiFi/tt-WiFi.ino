#include <SoftwareSerial.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
// //oled设置
// #define SCREEN_WIDTH 128
// #define SCREEN_HEIGHT 64
// #define OLED_RESET    -1 // 如果 OLED 上没有 Reset 引脚就设为 -1
// Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
//接收json指令
String buffer = "";  
// Motor A connections
int enA = 9;
int in1 = 8;
int in2 = 7;
// Motor B connections
int in3 = 5;
int in4 = 4;
int enB = 3;
// 电机参数（根据实测校准）
const float WHEEL_CIRCUMFERENCE = 23;    // 车轮周长=2πr=23.2cm
const int MAX_RPM = 110;                   // 标称转速
const float MAX_SPEED_CM_PER_SEC = 42;   // 理论最大速度=(110×23.2)/60≈42.5cm/s
const int MAX_PWM = 255;                   // PWM最大值
// 转向校准参数（需实测调整）
const float MS_PER_90_DEGREE = 600;        // 90°转向耗时(ms)
// 电机死区补偿参数（需实测调整）
const int MIN_START_PWM = 80;              // 实测能启动电机的最小PWM值

// 创建一个虚拟串口（软件串口）
SoftwareSerial espSerial(10, 11);  // RX, TX

void setup() {
  // 设置所有电机控制引脚为输出
  pinMode(enA, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  // 初始化串口通信
  Serial.begin(115200);       // 用于PC调试
  espSerial.begin(115200);    // 用于ESP8266通信
  //espSerial.setTimeout(100);
  Serial.println("Robot Motor Controller Ready!");
  // //初始化oled
  //  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
  //   Serial.println(F("OLED 初始化失败"));
  //   for(;;); // 无限循环卡住
  // }
  // display.clearDisplay();
  // display.setTextSize(1);      // 字体大小
  // display.setTextColor(SSD1306_WHITE);
  // display.setCursor(0, 0);
  // display.println("OLED Ready");
  // display.display();
}

void loop() {
  while (espSerial.available()) {
    char c = espSerial.read();
    if (c == '\n') {
      buffer.trim();
      Serial.println("Received JSON:");
      Serial.println(buffer);
      handleJsonCommand(buffer);
      buffer = "";
    } else {
      buffer += c;
    }
  }
}

// //oled显示json指令
// void showCommandOnOLED(String cmd, float distance, float speed, int angle) {
//   display.clearDisplay();
//   display.setCursor(0, 0);
//   display.println("Received Command:");
//   display.print("Cmd: "); display.println(cmd);
//   display.print("Dist: "); display.print(distance); display.println("cm");
//   display.print("Speed: "); display.print(speed); display.println("cm/s");
//   display.print("Angle: "); display.print(angle); display.println(" deg");
//   display.display();
// }

void handleJsonCommand(String jsonStr) {
  //库的标准做法，创建一个固定大小的JSON文档，用于存储解析后的数据
  StaticJsonDocument<512> doc; 
  //将JsonStr解析为JSON文档对象，如果JSON字符串格式不正确，会返回错误
  DeserializationError error = deserializeJson(doc, jsonStr);
  if (error) {
    Serial.print("JSON 解析失败: ");
    Serial.println(error.c_str());
    return;
  }
  //从解析后的JSON中读取字段
  String cmd = doc["command"];
  float distance = doc["distance"] | 0;//如果字段不存在，用默认值0，避免程序崩溃
  float speed = doc["speed"] | 0;
  int angle = doc["angle"].isNull() ? 0 : doc["angle"];
  //showCommandOnOLED(cmd, distance, speed, angle);
  // 处理角度（例如转向）
  if (!doc["angle"].isNull()) {
    turnByAngle(angle, speed);
    return;
  }

  // 普通移动指令
  if (cmd == "F") move(distance, speed, true);
  else if (cmd == "B") move(distance, speed, false);
  else if (cmd == "L") turnAndMove(false, distance, speed);
  else if (cmd == "R") turnAndMove(true, distance, speed);
  else if (cmd == "S") stop();
  else Serial.println("未知命令");
}


// ========== 核心运动函数 ==========

// 通用移动函数（前进/后退）
void move(float distance_cm, float speed_cm_per_sec, bool isForward) {
  Serial.print(isForward ? "[Forward " : "[Backward ");
  Serial.print(distance_cm);
  Serial.print("cm @ ");
  Serial.print(speed_cm_per_sec);
  Serial.println("cm/s]");

  // 设置方向
  digitalWrite(in1, isForward ? HIGH : LOW);
  digitalWrite(in2, isForward ? LOW : HIGH);
  digitalWrite(in3, isForward ? HIGH : LOW);
  digitalWrite(in4, isForward ? LOW : HIGH);

  // 设置速度
  int pwm = speedToPWM(speed_cm_per_sec);
  analogWrite(enA, pwm-25);
  analogWrite(enB, pwm);

  // 计算运行时间（ms）
  unsigned long duration = distanceToTime(distance_cm, speed_cm_per_sec);
  delay(duration);
  stop();
}

// 精确90°转向（原地旋转）
void pivotTurn90(bool isRight, float speed_cm_per_sec) {
  digitalWrite(in1, isRight ? HIGH : LOW);
  digitalWrite(in2, isRight ? LOW : HIGH);
  digitalWrite(in3, isRight ? LOW : HIGH);
  digitalWrite(in4, isRight ? HIGH : LOW);

  int pwm = speedToPWM(speed_cm_per_sec);
  analogWrite(enA, pwm);
  analogWrite(enB, pwm);

  delay(MS_PER_90_DEGREE);
  stop();
}

// 左右转并直行
void turnAndMove(bool isRight, float distance_cm, float speed_cm_per_sec) {
  pivotTurn90(isRight, speed_cm_per_sec);
  delay(200); // 转向后短暂停顿
  move(distance_cm, speed_cm_per_sec, true);
}

// 转向指定角度（顺时针+angle，逆时针-angle）
void turnByAngle(int angle_deg, float speed_cm_per_sec) {
  unsigned long duration = (abs(angle_deg) / 90.0) * MS_PER_90_DEGREE;
  bool isClockwise = (angle_deg > 0);
  
  digitalWrite(in1, isClockwise ? HIGH : LOW);
  digitalWrite(in2, isClockwise ? LOW : HIGH);
  digitalWrite(in3, isClockwise ? LOW : HIGH);
  digitalWrite(in4, isClockwise ? HIGH : LOW);

  int pwm = speedToPWM(speed_cm_per_sec);
  analogWrite(enA, pwm);
  analogWrite(enB, pwm);

  delay(duration);
  stop();
}

// 停止电机
void stop() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(enA, 0);
  analogWrite(enB, 0);
}

// 速度→PWM映射
int speedToPWM(float speed_cm_per_sec) {
  speed_cm_per_sec = constrain(speed_cm_per_sec, 0, MAX_SPEED_CM_PER_SEC);
  
  if (speed_cm_per_sec <= 0) return 0;
  const float VERY_LOW_SPEED = 5.0;
  if (speed_cm_per_sec < VERY_LOW_SPEED) {
    return MIN_START_PWM; 
  }
  
  return map(speed_cm_per_sec, VERY_LOW_SPEED, MAX_SPEED_CM_PER_SEC, MIN_START_PWM, MAX_PWM);
}

// 距离→时间转换（cm→ms）
unsigned long distanceToTime(float distance_cm, float speed_cm_per_sec) {
  if (speed_cm_per_sec <= 0) return 0;
  return (unsigned long)((distance_cm / speed_cm_per_sec) * 1000);
}
