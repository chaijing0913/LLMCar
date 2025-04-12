#include <Servo.h>

Servo myServo;

void setup() {
  Serial.begin(9600);
  myServo.attach(6);

  for (int i = 500; i <= 2500; i += 100) {
    myServo.writeMicroseconds(i);
    Serial.print("PWM: ");
    Serial.println(i);
    delay(1000);
  }
}

void loop() {}
