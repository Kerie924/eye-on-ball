/*
 * Lance On — Windows court buttons (Arduino Uno / Nano / compatible)
 *
 * Fixed wiring (do not change — matches capture/windows_pins.py):
 *   CAM 1 → D2 (signal) + D3 (GND)
 *   CAM 2 → D4 (signal) + D5 (GND)
 *   CAM 3 → D6 (signal) + D7 (GND)
 *   CAM 4 → D8 (signal) + D9 (GND)
 *   CAM 5 → D10 (signal) + D11 (GND)
 *   CAM 6 → D12 (signal) + D13 (GND)
 *
 * Wire each NO push button between the two pins of its pair.
 * On press, this sketch prints the camera number + newline over USB serial
 * (115200 baud) so the Lance On Windows agent can trigger that camera.
 */

const int CAMERAS = 6;
const int SIGNAL_PINS[CAMERAS] = {2, 4, 6, 8, 10, 12};
const int GND_PINS[CAMERAS] = {3, 5, 7, 9, 11, 13};

int previousState[CAMERAS];
unsigned long lastFireMs[CAMERAS];
const unsigned long COOLDOWN_MS = 300;
const unsigned long DEBOUNCE_MS = 40;

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < CAMERAS; i++) {
    pinMode(GND_PINS[i], OUTPUT);
    digitalWrite(GND_PINS[i], LOW);  // software GND
    pinMode(SIGNAL_PINS[i], INPUT_PULLUP);
    previousState[i] = digitalRead(SIGNAL_PINS[i]);
    lastFireMs[i] = 0;
  }
  Serial.println("LANCEON_BUTTONS_READY");
}

void loop() {
  unsigned long now = millis();
  for (int i = 0; i < CAMERAS; i++) {
    int current = digitalRead(SIGNAL_PINS[i]);
    // Press = HIGH → LOW (pull-up)
    if (previousState[i] == HIGH && current == LOW) {
      delay(DEBOUNCE_MS);
      if (digitalRead(SIGNAL_PINS[i]) == LOW) {
        if (now - lastFireMs[i] >= COOLDOWN_MS) {
          lastFireMs[i] = now;
          Serial.println(i + 1);  // camera index 1..6
        }
      }
    }
    previousState[i] = current;
  }
}
