const int trigPin = A1;  // Trig 引脚连接到 A0
const int echoPin = A2;  // Echo 引脚连接到 A1
long duration;
float distance;

void setup() {
  Serial.begin(9600);           // 初始化串口
  pinMode(trigPin, OUTPUT);     // 设置 trig 为输出
  pinMode(echoPin, INPUT);      // 设置 echo 为输入
}

void loop() {
  // 触发超声波脉冲
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // 读取回波持续时间
  duration = pulseIn(echoPin, HIGH);

  // 计算距离（单位：厘米）
  distance = duration * 0.0343 / 2;

  // 通过串口以 JSON 格式输出
  Serial.print("{\"distance\": ");
  Serial.print(distance, 2);  // 保留两位小数
  Serial.println("}");

  delay(500); // 每隔0.5秒测一次
}
