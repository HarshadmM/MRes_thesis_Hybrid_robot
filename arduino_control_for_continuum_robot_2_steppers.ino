#include <Servo.h>
#define X_STEP_PIN 54
#define X_DIR_PIN 55
#define X_EN_PIN 38

#define Y_STEP_PIN 60
#define Y_DIR_PIN 61
#define Y_EN_PIN 56

#define Z_STEP_PIN 46
#define Z_DIR_PIN 48
#define Z_EN_PIN 62

Servo myServo;

int stepDelay = 700;

char xCmd = 'S';
char yCmd = 'W';
char zCmd = 'N';

unsigned long lastXStep =0;
unsigned long lastYStep =0;
unsigned long lastZStep =0;

void setup(){
  Serial.begin(115200);

  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_EN_PIN, OUTPUT);

  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_EN_PIN, OUTPUT);

  pinMode(Z_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);
  pinMode(Z_EN_PIN, OUTPUT);

  // Enable stepper drivers
  digitalWrite(X_EN_PIN, LOW);
  digitalWrite(Y_EN_PIN, LOW);
  digitalWrite(Z_EN_PIN, HIGH);

  Serial.println("Arduino ready");
  myServo.attach(11);      // SERVO0 on RAMPS
  myServo.write(0);        // Start at 0°
}

void loop() {
  readSerialCommands();

  runMotorX();
  runMotorY();
  runMotorZ();
}

void readSerialCommands() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == 'U' || c == 'D' || c == 'S') {
      xCmd = c;
    }

    else if (c == 'R' || c == 'L' || c == 'W') {
      yCmd = c;
    }

    else if (c == 'P') {
      zCmd = 'P';
      digitalWrite(Z_EN_PIN, LOW);    // Enable Z driver
    }

    else if (c == 'N') {
      zCmd = 'N';
      digitalWrite(Z_EN_PIN, HIGH);   // Disable Z driver
    }

    else if (c == 'V') {
      int newSpeed = Serial.parseInt();
      if (newSpeed >= 150 && newSpeed <= 5000) {
        stepDelay = newSpeed;
      }
    }

    else if (c == 'T') {
      Serial.println("Tare ignored");
    }

    else if (c == 'Z') {
      Serial.println("Zero ignored");
    }

    else if (c == 'Q') {
      Serial.println("# LIVE\t0\t0\t0\t0\t0\t0");
    }
    else if (c == 'M') {
  Serial.println("M received");
  myServo.write(90);
  delay(500);
  myServo.write(0);
    }
  }
}

void runMotorX() {
  if (xCmd == 'S') return;

  if (xCmd == 'U') {
    digitalWrite(X_DIR_PIN, HIGH);
  } else if (xCmd == 'D') {
    digitalWrite(X_DIR_PIN, LOW);
  }

  if (micros() - lastXStep >= stepDelay) {
    stepOnce(X_STEP_PIN);
    lastXStep = micros();
  }
}

void runMotorY() {
  if (yCmd == 'W') return;

  if (yCmd == 'R') {
    digitalWrite(Y_DIR_PIN, HIGH);
  } else if (yCmd == 'L') {
    digitalWrite(Y_DIR_PIN, LOW);
  }

  if (micros() - lastYStep >= stepDelay) {
    stepOnce(Y_STEP_PIN);
    lastYStep = micros();
  }
}
void runMotorZ() {
  if (zCmd == 'N') return;

  // Choose the direction of the motor
  digitalWrite(Z_DIR_PIN, HIGH);
  // Change HIGH to LOW if it spins the wrong way

  if (micros() - lastZStep >= stepDelay) {
    stepOnce(Z_STEP_PIN);
    lastZStep = micros();
  }
}

void stepOnce(int stepPin) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(3);
  digitalWrite(stepPin, LOW);
}