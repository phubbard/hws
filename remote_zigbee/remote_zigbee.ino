/*
Paul Hubbard
Jan 6 2012

Updated home weather station code, Arduino portion. This file is for the remote sensor node, which
sends its data via the XBee ZigBee radio module.

Sensors:
 - DS18B20 on digital pin 8 (OneWire temp sensor)
 - Ohmic Instruments SC-600 humidity sensor on analog pin 1
 - Sparkfun TEMT6000 breakout board light sensor on analog pin 0

Hardware:
- XBee connected, with PAN ID matching that of the coordinator. XBee must have TX/RX connected
either via jumpers or switches, so that the serial writes go out over Zigbee.
-- Radio must be programmed to be either remote or router, zigbee, probably AT mode, 9600N81. 

Notes:
 - Hardwired temp sensor address. Need to put the search loop back in, so I can swap sensors.
 - Using floating point math. Might as well, speed a total non-issue.
 - Light sensor is uncalibrated, seems to max out at ~1k lux. Way less than full daylight.
*/ 

#include <OneWire.h>
#include <SPI.h>
#include <stdarg.h>
#include <avr/wdt.h>

 // DS18B20 Temperature chip i/o
OneWire ds(8); 
byte addr[8] = {0x28, 0x2a, 0x34, 0xb7, 0x03, 0x00, 0x00, 0x0F};
const int lightInPin = A0;
const int rhInPin = A1;


void setup(void) 
{
  // Pin 13 has an LED connected on most Arduino boards:
  pinMode(13, OUTPUT);     
  digitalWrite(13, HIGH);   // set the LED on
  
  // initialize inputs/outputs
  // start serial port
  Serial.begin(9600);

  // Enable watchdog timer, 8 second deadtime
  // See http://tushev.org/articles/electronics/48-arduino-and-watchdog-timer
  wdt_enable(WDTO_8S);
  
  digitalWrite(13, LOW);
}


float rhConvert(int reading, float temp)
{
  float rhVolts = 0.0;
  float rhcf = 1.0;
  float rh = 0.0;
  float c_rh = 0.0;
  
  rhVolts = reading * 0.0048828125;
  // RH temp correction is -0.7% per deg C
  rhcf = (-0.7 * (temp - 25.0)) / 100.0;
  rh = (rhVolts * 45.25) - 42.76;
  c_rh = rh + (rhcf * rh);
  return c_rh;
}

float getTemp(void)
{
  byte i;
  byte data[12];
  int adcCounts = 0;
  int HighByte, LowByte, TReading, SignBit, Tc_100, Whole, Fract;
  float temp = 0.0;
  
  ds.reset();
  ds.select(addr);
  ds.write(0x44);         // start conversion

  delay(1000);     // maybe 750ms is enough, maybe not
  // we might do a ds.depower() here, but the reset will take care of it.

  ds.reset();
  ds.select(addr);    
  ds.write(0xBE);         // Read Scratchpad

  for ( i = 0; i < 9; i++) {           // we need 9 bytes
    data[i] = ds.read();
  }
  
  LowByte = data[0];
  HighByte = data[1];
  TReading = (HighByte << 8) + LowByte;
  SignBit = TReading & 0x8000;  // test most sig bit
  if (SignBit) // negative
  {
    TReading = (TReading ^ 0xffff) + 1; // 2's comp
  }

  temp = TReading * 0.0625;
  return temp;  
}

float getRH(float temp)
{
  int adcCounts = 0;
  
  adcCounts = analogRead(rhInPin);  
  return rhConvert(adcCounts, temp);
}

int getLight(void)
{
  return analogRead(lightInPin); 
}

// Sends a JSON-encoded single line, with sensor ID 'indoor-1' and fields simply named.
void sendData(void)
{
  float temp = getTemp();
  float rh = getRH(temp);
  int lux = getLight();
  
  Serial.print("{\"name\":\"indoor-1\", ");
  Serial.print("\"temp\":");
  Serial.print(temp);
  Serial.print(", \"RH\":");
  Serial.print(rh);
  Serial.print(", \"lux\":");
  Serial.print(lux);
  Serial.println("}");
}

void loop(void)
{
  digitalWrite(13, HIGH);  
  sendData();
  // Reset watchdog timer
  wdt_reset();
  digitalWrite(13, LOW); // LED off
  
  delay(5000);
}

