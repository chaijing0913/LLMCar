#include <Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// 超声波、蜂鸣器引脚
#define BUZZER_PIN A0
#define TRIG_PIN A1
#define ECHO_PIN A2
#define SERVO_PIN 6

// OLED 参数设置
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

Servo radarServo;
bool isReversing = true;  // 初始为倒车模式

// 获取当前距离（单位：cm）
float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  float distance = duration * 0.034 / 2;
  return distance;
}

// 倒车模式（20cm内开始警报，OLED 显示）
void reverseMode() {
  radarServo.write(65);
  float d = getDistance();

  // OLED 显示
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.print("Mode: Rev");
  display.setCursor(0, 30);
  display.print("Dist: ");
  display.print((int)d);
  display.println("cm");

  if (d < 3) {
    display.setCursor(0, 50);
    display.setTextSize(1);
    display.println("Out of Range");
    noTone(BUZZER_PIN);  // 不发声
    display.display();
    delay(300);
    return;
  }

  int beepFrequency = 1000; // 初始频率设定为 1000Hz
  int beepDelay = 200;

  if (d >= 20) {
    // 安全距离，不响
    noTone(BUZZER_PIN);  // 停止发声
    display.display();
    delay(300);
    return;
  } else if (d > 15) {
    beepFrequency = 800;
  } else if (d > 10) {
    beepFrequency = 600;
  } else if (d > 5) {
    beepFrequency = 400;
  } else {
    // <5 cm 连续响
    display.setCursor(0, 50);
    display.setTextSize(1);
    display.println("Too Close!");
    tone(BUZZER_PIN, 1000);  // 高频连续响
    display.display();
    delay(300);
    noTone(BUZZER_PIN);
    delay(100);
    return;
  }

  // 有节奏地“滴”
  display.setCursor(0, 50);
  display.setTextSize(1);
  display.println("Warning!");
  display.display();

  tone(BUZZER_PIN, beepFrequency);  // 发出警报音
  delay(beepDelay);
  noTone(BUZZER_PIN);  // 停止发声
}

// 显示雷达信息
void displayRadarInfo(int angle, float distance) {
  // OLED 显示
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.print("Mod: Radar");
  display.setCursor(0, 30);
  display.print("Ang: ");
  display.print(angle);
  display.setCursor(0, 50);
  display.print("Dis: ");
  display.print((int)distance);
  display.println(" cm");
  display.display();
}

// 雷达扫描模式（舵机旋转）
void radarScan() {
  // 从 0 到 180 度扫描
  for (int angle = 0; angle <= 180; angle += 10) {
    radarServo.write(angle);
    delay(500); // 慢速旋转
    float d = getDistance();
    displayRadarInfo(angle, d);  // 显示雷达信息
    delay(1000);
  }

  // 从 180 度回到 0 度
  for (int angle = 180; angle >= 0; angle -= 10) {
    radarServo.write(angle);
    delay(500); // 慢速旋转
    float d = getDistance();
    displayRadarInfo(angle, d);  // 显示雷达信息
    delay(1000);
  }
}


// 串口监听模式切换
void checkSerialCommand() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'r') {
      isReversing = true;
      Serial.println("切换为倒车模式");
    } else if (cmd == 's') {
      isReversing = false;
      Serial.println("切换为雷达扫描模式");
    }
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  radarServo.attach(SERVO_PIN);

  // 初始化 OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED 初始化失败");
    for (;;); // 卡住
  }
  display.clearDisplay();
  display.display();

  Serial.println("输入 'r' 切换为倒车模式，输入 's' 进入雷达扫描模式");
}

void loop() {
  checkSerialCommand();

  if (isReversing) {
    reverseMode();  // 倒车模式
  } else {
    radarScan();  // 雷达扫描模式
  }
}
