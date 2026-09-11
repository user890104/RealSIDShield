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
#ifndef SID_H
#define SID_H

#include <avr/io.h>
#include <Arduino.h>

// Port D
#define DATA_2      2
#define DATA_3      3
#define DATA_4      4
#define DATA_5      5
#define DATA_6      6
#define DATA_7      7

// Port B
#define DATA_0      8
#define DATA_1      9
#define SID_CLOCK   10
#define SID_CS      11
#define LATCH_CLOCK 12
#define SID_RESET   13

class SID
{
  void SID::Select();
  void SID::Deselect();
  void SID::LatchAddress();
  void SID::UnlatchAddress();
  void SID::DataBusOutput();
  void SID::DataBusInput();
  uint8_t SID::ReadDataBus();
  void SID::WriteDataBus(uint8_t value);
  void SID::WriteAddress(uint8_t address, uint8_t read);

  public:
    void Setup();
    void Poke(uint8_t address, uint8_t value);
    uint8_t Peek(uint8_t address);
};

#endif
