# SECTION 03: House of the Dragon

## Part 1: Repair the Reins (Code & Bug Fixes)

### 1. Refactored Code

#### `encoder.cpp`
```cpp
#include "encoder.h"

QuadratureEncoder::QuadratureEncoder(uint8_t a, uint8_t b)
    : pinA(a), pinB(b), tickCount(0) {}

void QuadratureEncoder::init() {
    // FIX (a): Open-collector outputs float HIGH when inactive.
    // Changing INPUT to INPUT_PULLUP enables the internal pull-up resistor.
    pinMode(pinA, INPUT_PULLUP);
    pinMode(pinB, INPUT_PULLUP);
}

long QuadratureEncoder::readTicks() {
    if (digitalRead(pinA) == HIGH) { tickCount++; }
    return tickCount;
}

void QuadratureEncoder::resetTicks() { tickCount = 0; }