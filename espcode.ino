/*
  ESP8266 -> L298N dual H-bridge, WASD control from Serial Monitor (115200, line ending "Newline")
  w/s = forward/reverse   a/d = spin left/right   x or space = brake   q = release (coast)
  + / - = speed step      number + Enter = speed in % (0-100)          ? = help
  Keep this as the ONLY .ino in its sketch folder.
*/

#include <ESP8266WiFi.h>

// ---------------- pins (NodeMCU labels) ----------------
const uint8_t L_EN  = 14;   // D5 -> ENA (PWM)
const uint8_t L_IN1 = 5;    // D1 -> IN1
const uint8_t L_IN2 = 4;    // D2 -> IN2
const uint8_t R_EN  = 12;   // D6 -> ENB (PWM)
const uint8_t R_IN3 = 13;   // D7 -> IN3
const uint8_t R_IN4 = 16;   // D0 -> IN4
// ---------------- settings ----------------
const bool     LEFT_INVERT   = false;   // flip if a motor runs backwards on 'w'
const bool     RIGHT_INVERT  = false;
const uint8_t  SPEED_STEP    = 10;      // % per +/- press
const uint8_t  MIN_DUTY_PCT  = 30;      // L298N motors usually stall below this; 1% speed maps to this duty
const uint16_t PWM_RANGE     = 1023;
const uint16_t PWM_FREQ_HZ   = 1000;
const bool     STARTUP_BRAKE = false;   // false = coast at boot, true = brake at boot

struct Motor {
  uint8_t en, inA, inB;
  bool    invert;
  const char *name;
};

Motor leftMotor  = { L_EN, L_IN1, L_IN2, LEFT_INVERT,  "LEFT"  };
Motor rightMotor = { R_EN, R_IN3, R_IN4, RIGHT_INVERT, "RIGHT" };

uint8_t speedPct   = 50;     // 0-100
char    lastMotion = 'q';

static uint16_t dutyFromPct(uint8_t pct) {
  if (pct == 0) return 0;
  uint32_t duty = MIN_DUTY_PCT + (uint32_t)(100 - MIN_DUTY_PCT) * (pct - 1) / 99;
  return (uint16_t)(duty * PWM_RANGE / 100);
}

static void runMotor(Motor &m, bool forward) {
  bool dir = forward ^ m.invert;
  digitalWrite(m.inA, dir ? HIGH : LOW);
  digitalWrite(m.inB, dir ? LOW : HIGH);
  analogWrite(m.en, dutyFromPct(speedPct));
}

static void brakeMotor(Motor &m) {        // both inputs equal + EN high = fast stop
  digitalWrite(m.inA, HIGH);
  digitalWrite(m.inB, HIGH);
  analogWrite(m.en, PWM_RANGE);
}

static void coastMotor(Motor &m) {        // EN low = outputs off, motor free-wheels
  analogWrite(m.en, 0);
  digitalWrite(m.inA, LOW);
  digitalWrite(m.inB, LOW);
}

static void applyMotion(char c) {
  switch (c) {
    case 'w': runMotor(leftMotor, true);  runMotor(rightMotor, true);  break;
    case 's': runMotor(leftMotor, false); runMotor(rightMotor, false); break;
    case 'a': runMotor(leftMotor, false); runMotor(rightMotor, true);  break;  // spin left
    case 'd': runMotor(leftMotor, true);  runMotor(rightMotor, false); break;  // spin right
    case 'x': brakeMotor(leftMotor);      brakeMotor(rightMotor);      break;
    case 'q': coastMotor(leftMotor);      coastMotor(rightMotor);      break;
  }
  lastMotion = c;
}

static void setSpeed(uint32_t pct) {
  speedPct = (uint8_t)min<uint32_t>(100, pct);
  Serial.printf("> speed %u%%%s\n", speedPct, pct > 100 ? " (capped)" : "");
  if (strchr("wasd", lastMotion)) applyMotion(lastMotion);   // apply live
}

static void printHelp() {
  Serial.println(F("\nw/a/s/d = move   x/space = brake   q = release (coast)"));
  Serial.println(F("+/- = speed step   number + Enter = speed in % (0-100)   ? = help"));
  Serial.printf("Speed: %u%%\n", speedPct);
}

void setup() {
  WiFi.mode(WIFI_OFF);
  Serial.begin(115200);

  const uint8_t pins[] = { L_EN, L_IN1, L_IN2, R_EN, R_IN3, R_IN4 };
  for (uint8_t p : pins) pinMode(p, OUTPUT);
  analogWriteRange(PWM_RANGE);
  analogWriteFreq(PWM_FREQ_HZ);

  coastMotor(leftMotor);                 // nothing moves until w/a/s/d
  coastMotor(rightMotor);
  if (STARTUP_BRAKE) applyMotion('x');
  lastMotion = 'q';

  Serial.println(F("\n\nL298N dual motor controller"));
  Serial.println(F("Idle. Motors off - send w/a/s/d to move."));
  printHelp();
}

void loop() {
  static uint32_t numBuf = 0;
  static bool     numPending = false;

  if (!Serial.available()) return;
  char c = tolower(Serial.read());

  if (c >= '0' && c <= '9') {            // typed number, applied on next non-digit
    numBuf = min<uint32_t>(numBuf * 10 + (c - '0'), 100000);
    numPending = true;
    return;
  }
  if (numPending) {
    setSpeed(numBuf);
    numBuf = 0;
    numPending = false;
  }

  switch (c) {
    case 'w': case 'a': case 's': case 'd': case 'q': case 'x':
      applyMotion(c);
      Serial.printf("> %c (%u%%)\n", c, speedPct);
      break;
    case ' ':
      applyMotion('x');
      Serial.println(F("> brake"));
      break;
    case '+': case '=':
      setSpeed(speedPct + SPEED_STEP);
      break;
    case '-': case '_':
      setSpeed(speedPct > SPEED_STEP ? speedPct - SPEED_STEP : 0);
      break;
    case '?': case 'h':
      printHelp();
      break;
    default:
      break;                              // ignore \r, \n, etc.
  }
}
