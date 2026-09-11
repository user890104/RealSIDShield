/*
RealSIDFirmware
Version 1.0

Copyright (c) 2013, A.T.Brask (atbrask[at]gmail[dot]com)
All rights reserved,

Demonstration code for the RealSIDShield Arduino shield.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include <avr/io.h>
#include <Arduino.h>

#include "Pins.h"
#include "SID.h"
#include "Latch.h"

Latch LatchChip;

void SID::Select()
{
  digitalWrite(SID_CS, LOW);
}

void SID::Deselect()
{
  digitalWrite(SID_CS, HIGH);
}

void SID::DataBusOutput()
{
  pinMode(DATA_0, OUTPUT);
  pinMode(DATA_1, OUTPUT);
  pinMode(DATA_2, OUTPUT);
  pinMode(DATA_3, OUTPUT);
  pinMode(DATA_4, OUTPUT);
  pinMode(DATA_5, OUTPUT);
  pinMode(DATA_6, OUTPUT);
  pinMode(DATA_7, OUTPUT);
}

void SID::DataBusInput()
{
  pinMode(DATA_0, INPUT);
  pinMode(DATA_1, INPUT);
  pinMode(DATA_2, INPUT);
  pinMode(DATA_3, INPUT);
  pinMode(DATA_4, INPUT);
  pinMode(DATA_5, INPUT);
  pinMode(DATA_6, INPUT);
  pinMode(DATA_7, INPUT);
}

uint8_t SID::ReadDataBus()
{
  uint8_t value = 0;

  value |= digitalRead(DATA_0) << 0;
  value |= digitalRead(DATA_1) << 1;
  value |= digitalRead(DATA_2) << 2;
  value |= digitalRead(DATA_3) << 3;
  value |= digitalRead(DATA_4) << 4;
  value |= digitalRead(DATA_5) << 5;
  value |= digitalRead(DATA_6) << 6;
  value |= digitalRead(DATA_7) << 7;

  return value;
}

void SID::WriteDataBus(uint8_t value)
{
  digitalWrite(DATA_0, bitRead(value, 0));
  digitalWrite(DATA_1, bitRead(value, 1));
  digitalWrite(DATA_2, bitRead(value, 2));
  digitalWrite(DATA_3, bitRead(value, 3));
  digitalWrite(DATA_4, bitRead(value, 4));
  digitalWrite(DATA_5, bitRead(value, 5));
  digitalWrite(DATA_6, bitRead(value, 6));
  digitalWrite(DATA_7, bitRead(value, 7));
}

void SID::Setup()
{
  LatchChip.Setup();

  // Set up SID chip select, output, inactive
  pinMode(SID_CS, OUTPUT);
  Deselect();

  // Copied from the SIDaster project:
  // 1MHz generation on OC1B - Clk 16 MHz

  // set pin 10 as OC1B output
  pinMode(SID_CLOCK, OUTPUT);

  // Reset settings of Timer/Counter register 1
  TCCR1A &= ~((1<<COM1B1) | (1<<COM1B0) | (1<<WGM11) | (1<<WGM10));
  TCCR1B &= ~((1<<WGM13) | (1<<WGM12) | (1<<CS12) | (1<<CS11) | (1<<CS10));

  // Set compare match output B to toogle
  TCCR1A |= (0<<COM1B1) | (1<<COM1B0);

  // Set waveform generation mode to CTC (Clear Counter on Match)
  TCCR1A |= (0<<WGM11) | (0<<WGM10);
  TCCR1B |= (0<<WGM13) | (1<<WGM12);

  // No prescaler
  TCCR1B |= (0<<CS12) | (0<<CS11) | (1<<CS10);

  // Set output compare register A to 8 (i.e. OC1B Toggle every 7+1=8 Clk pulses)
  OCR1A = 7;

  // delay 1 PAL frame = 50 Hz
  delay(20);

  // Reset SID
  pinMode(SID_RESET, OUTPUT);

  digitalWrite(SID_RESET, LOW);
  delay(20);

  digitalWrite(SID_RESET, HIGH);
  delay(20);

  // Data bus is output by default
  DataBusOutput();

  // Reset SID registers (0..24 are write-only and 25...28 are read-only)
  for (uint8_t address = 0; address < 25; address++)
    Poke(address, 0);
}

void SID::Poke(uint8_t address, uint8_t value)
{
  // deselect before accessing the bus
  Deselect();

  // set address, set r/w to write
  LatchChip.SetAddress(address, false);

  // Put the value on the databus
  WriteDataBus(value);

  // Make the SID read our values
  Select();
  delayMicroseconds(1);
  Deselect();
}

uint8_t SID::Peek(uint8_t address)
{
  uint8_t result = 0;

  // deselect before accessing the bus
  Deselect();

  // set address, set r/w to read
  LatchChip.SetAddress(address, true);

  // Set databus in input mode
  DataBusInput();

  // Enable SID and wait one clock cycle (more or less)
  Select();
  delayMicroseconds(1);
  
  // Read databus and return
  result = ReadDataBus();

  Deselect();

  // Revert data bus to output
  DataBusOutput();

  return result;
}
