#include <Arduino.h>

#include "Latch.h"
#include "Pins.h"

void Latch::Enable(void)
{
  digitalWrite(LATCH_CLOCK, HIGH);
}

void Latch::Disable(void)
{
  digitalWrite(LATCH_CLOCK, LOW);
}

void Latch::Setup(void)
{
  // Set up 74574
  pinMode(LATCH_CLOCK, OUTPUT);
  Disable();
}

void Latch::SetAddress(uint8_t address, uint8_t read)
{
  // Address bits 0 and 1 goes to B0 and B1 and bits 2..4 goes to D2...D4. The read/write-bit goes to D5.
  digitalWrite(DATA_0, bitRead(address, 0));
  digitalWrite(DATA_1, bitRead(address, 1));
  digitalWrite(DATA_2, bitRead(address, 2));
  digitalWrite(DATA_3, bitRead(address, 3));
  digitalWrite(DATA_4, bitRead(address, 4));
  digitalWrite(DATA_5, read ? HIGH : LOW);

  // Pulse the 74374's clock
  Enable();
  Disable();
}
