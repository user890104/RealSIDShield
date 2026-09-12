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

#include "SID.h"

int idx = 0;
char buffer[26];
char newsid[25];
char oldsid[25];
bool dataconsumed = true;
unsigned long lastupdate = 0;
int updatems = 0;

SID SIDchip;

void setup()
{
  Serial.begin(115200);
  SIDchip.Setup();
  Serial.write('?');
  Serial.flush();
}

void readData()
{
  char ch;

  if (Serial.available() == 0)
    return;

  buffer[idx++] = Serial.read();

  if (idx >= sizeof(buffer)) {
    idx = 0;

    if (buffer[0] == 0) {
      memcpy(newsid, buffer + 1, sizeof(newsid));
      dataconsumed = false;
    }

    if (buffer[0] == 1) {
      SIDchip.Reset();
      updatems = buffer[1];
    }
  }
}

void updateSID()
{
  for (int i = 0; i < sizeof(newsid); i++)
  {
    if (oldsid[i] == newsid[i])
      continue;

    SIDchip.Poke(i, newsid[i]);
    oldsid[i] = newsid[i];
  }
}

void checkUpdateSid(void)
{
  if (!updatems)
    return;

  // Check time and update SID if needed
  unsigned long timenow = millis();

  if (timenow - lastupdate < updatems)
    return;

  lastupdate = timenow;

  if (!dataconsumed) {
    updateSID();
    dataconsumed = true;
  }

  // Send more data!
  Serial.write('?');
  Serial.flush();
}

void loop()
{
  readData();
  checkUpdateSid();
}
