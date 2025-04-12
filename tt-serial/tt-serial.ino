// Motor A connections
int enA = 9;
int in1 = 8;
int in2 = 7;

// Motor B connections
int enB = 3;
int in3 = 5;
int in4 = 4;

// 电机参数（根据实测校准）
const float WHEEL_CIRCUMFERENCE = 23.2;    // 车轮周长=2πr=23.2cm
const int MAX_RPM = 110;                   // 标称转速
const float MAX_SPEED_CM_PER_SEC = 42.5;   // 理论最大速度=(110×23.2)/60≈42.5cm/s
const int MAX_PWM = 255;                   // PWM最大值

// 转向校准参数（需实测调整）
const float MS_PER_90_DEGREE = 600;        // 90°转向耗时(ms)

// 电机死区补偿参数（需实测调整）
const int MIN_START_PWM = 80;              // 实测能启动电机的最小PWM值

void setup() {
  // 设置所有电机控制引脚为输出
  pinMode(enA, OUTPUT);
  pinMode(enB, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
  
  // 初始化串口通信
  Serial.begin(9600);
  Serial.println("Robot Motor Controller Ready!");
  Serial.println("Available Commands:");
  Serial.println("F <distance> <speed> - Forward");
  Serial.println("B <distance> <speed> - Backward");
  Serial.println("L <distance> <speed> - Turn Left 90° then move");
  Serial.println("R <distance> <speed> - Turn Right 90° then move");
  Serial.println("T <angle> <speed>   - Turn by angle");
  Serial.println("S - Stop");
  Serial.println("D - Debug PWM mapping");
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    float distance = 0;
    float speed = 0;
    int angle = 0;

    // 解析参数（如 "L 30 10" → 左转90°后前进30cm，速度10cm/s）
    if (Serial.peek() != '\n') {
      distance = Serial.parseFloat();
      speed = Serial.parseFloat();
      angle = Serial.parseInt();
    }
    Serial.read(); // 清除换行符

    // 执行命令
    switch (command) {
      case 'F': move(distance, speed, true); break;    // 前进
      case 'B': move(distance, speed, false); break;   // 后退
      case 'L': turnAndMove(false, distance, speed); break; // 左转90°后直行
      case 'R': turnAndMove(true, distance, speed); break;  // 右转90°后直行
      case 'T': turnByAngle(angle, speed); break;      // 角度转向
      case 'S': stop(); break;
      case 'D': debugPWMmap(); break;                 // PWM映射调试
      default: Serial.println("Invalid command!");
    }
  }
}

// ========== 核心运动函数 ==========

// 转向90°后直行的复合动作
void turnAndMove(bool isRight, float distance_cm, float speed_cm_per_sec) {
  Serial.print(isRight ? "[Right 90° + Move " : "[Left 90° + Move ");
  Serial.print(distance_cm);
  Serial.print("cm @ ");
  Serial.print(speed_cm_per_sec);
  Serial.println("cm/s]");

  pivotTurn90(isRight, speed_cm_per_sec);
  delay(200); // 转向后短暂停顿
  move(distance_cm, speed_cm_per_sec, true);
}

// 精确90°转向（原地旋转）
void pivotTurn90(bool isRight, float speed_cm_per_sec) {
  // 设置差速方向（两轮反向转动）
  digitalWrite(in1, isRight ? HIGH : LOW);
  digitalWrite(in2, isRight ? LOW : HIGH);
  digitalWrite(in3, isRight ? LOW : HIGH);
  digitalWrite(in4, isRight ? HIGH : LOW);

  // 设置速度（使用相同PWM值保证对称转向）
  int pwm = speedToPWM(speed_cm_per_sec);
  analogWrite(enA, pwm);
  analogWrite(enB, pwm);

  delay(MS_PER_90_DEGREE);
  stop();
}

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
  analogWrite(enA, pwm);
  analogWrite(enB, pwm);

  // 计算运行时间（ms）
  unsigned long duration = distanceToTime(distance_cm, speed_cm_per_sec);
  delay(duration);
  stop();
}

// 角度转向（+angle顺时针，-angle逆时针）
void turnByAngle(int angle_deg, float speed_cm_per_sec) {
  Serial.print("[Turn ");
  Serial.print(angle_deg);
  Serial.print("° @ ");
  Serial.print(speed_cm_per_sec);
  Serial.println("cm/s]");

  // 计算转向时间（基于90°转向时间线性缩放）
  unsigned long duration = (abs(angle_deg) / 90.0) * MS_PER_90_DEGREE;

  // 设置差速方向
  bool isClockwise = (angle_deg > 0);
  digitalWrite(in1, isClockwise ? HIGH : LOW);
  digitalWrite(in2, isClockwise ? LOW : HIGH);
  digitalWrite(in3, isClockwise ? LOW : HIGH);
  digitalWrite(in4, isClockwise ? HIGH : LOW);

  // 设置速度
  int pwm = speedToPWM(speed_cm_per_sec);
  analogWrite(enA, pwm);
  analogWrite(enB, pwm);

  delay(duration);
  stop();
}

// ========== 工具函数 ==========

// 速度→PWM映射（优化死区处理）
int speedToPWM(float speed_cm_per_sec) {
  speed_cm_per_sec = constrain(speed_cm_per_sec, 0, MAX_SPEED_CM_PER_SEC);
  
  if (speed_cm_per_sec <= 0) return 0;

  // 新增低速特殊处理（如<5cm/s时固定输出最小有效PWM）
  const float VERY_LOW_SPEED = 5.0;
  if (speed_cm_per_sec < VERY_LOW_SPEED) {
    return MIN_START_PWM; 
  }
  
  return map(speed_cm_per_sec, VERY_LOW_SPEED, MAX_SPEED_CM_PER_SEC,
             MIN_START_PWM, MAX_PWM);
}

// 距离→时间转换（cm→ms）
unsigned long distanceToTime(float distance_cm, float speed_cm_per_sec) {
  if (speed_cm_per_sec <= 0) return 0;
  return (unsigned long)((distance_cm / speed_cm_per_sec) * 1000);
}

// 紧急停止
void stop() {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  analogWrite(enA, 0);
  analogWrite(enB, 0);
}

// ========== 调试函数 ==========
// PWM映射调试
void debugPWMmap() {
  Serial.println("Speed(cm/s)\tPWM");
  Serial.println("-------------------");
  for (float s = 0; s <= MAX_SPEED_CM_PER_SEC + 5; s += 2.5) {
    Serial.print(s);
    Serial.print("\t\t");
    Serial.println(speedToPWM(s));
  }
}

