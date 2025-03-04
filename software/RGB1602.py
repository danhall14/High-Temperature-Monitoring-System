# -*- coding: utf-8 -*-
import time
from machine import Pin,I2C

RGB1602_SDA = Pin(0)
RGB1602_SCL = Pin(1)

RGB1602_I2C = I2C(0,sda = RGB1602_SDA,scl = RGB1602_SCL ,freq = 400000)

#Device I2C Arress
LCD_ADDRESS   =  (62)
RGB_ADDRESS   =  (96)

#color define

REG_RED    =     0x04
REG_GREEN  =     0x03
REG_BLUE   =     0x02
REG_MODE1  =     0x00
REG_MODE2  =     0x01
REG_OUTPUT =     0x08
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

#flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

#flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

#flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

#flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x8DOTS = 0x00


class RGB1602():
  def __init__(self, sda=Pin(0), scl=Pin(1), col=16, row=2):
    self._row = row
    self._col = col
    

    self._showfunction = LCD_4BITMODE | LCD_1LINE | LCD_5x8DOTS;
    
    self.lcd_connected = True
    try:
        self.begin(self._row, self._col)
    except OSError:
        self.lcd_connected = False
        
  def command(self,cmd):
    RGB1602_I2C.writeto_mem(LCD_ADDRESS, 0x80, chr(cmd))

  def chr_write(self,data):
    RGB1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, chr(data))
    
  def write(self, data):
     if isinstance(data, str):
            for char in data:
                RGB1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, char)
     else:
        RGB1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, chr(data))

    
  def setReg(self,reg,data):
    RGB1602_I2C.writeto_mem(RGB_ADDRESS, reg, chr(data))


  def setRGB(self,r,g,b):
    self.setReg(REG_RED,r)
    self.setReg(REG_GREEN,g)
    self.setReg(REG_BLUE,b)

  def setCursor(self,col,row):
    if(row == 0):
      col|=0x80
    else:
      col|=0xc0;
    RGB1602_I2C.writeto(LCD_ADDRESS, bytearray([0x80,col]))

  def clear(self):
    if self.lcd_connected:
        self.command(LCD_CLEARDISPLAY)
        time.sleep(0.002)
    
  def printout(self,arg):
    if(isinstance(arg,int)):
      arg=str(arg)

    for x in bytearray(arg,'utf-8'):
      self.write(x)


  def display(self):
    self._showcontrol |= LCD_DISPLAYON 
    self.command(LCD_DISPLAYCONTROL | self._showcontrol)

 
  def begin(self,cols,lines):
    if (lines > 1):
        self._showfunction |= LCD_2LINE 
     
    self._numlines = lines 
    self._currline = 0 

    
     
    time.sleep(0.05)


    # Send function set command sequence
    self.command(LCD_FUNCTIONSET | self._showfunction)
    #delayMicroseconds(4500);  # wait more than 4.1ms
    time.sleep(0.005)
    # second try
    self.command(LCD_FUNCTIONSET | self._showfunction);
    #delayMicroseconds(150);
    time.sleep(0.005)
    # third go
    self.command(LCD_FUNCTIONSET | self._showfunction)
    # finally, set # lines, font size, etc.
    self.command(LCD_FUNCTIONSET | self._showfunction)
    # turn the display on with no cursor or blinking default
    self._showcontrol = LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF 
    self.display()
    # clear it off
    self.clear()
    # Initialize to default text direction (for romance languages)
    self._showmode = LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT 
    # set the entry mode
    self.command(LCD_ENTRYMODESET | self._showmode);
    # backlight init
    self.setReg(REG_MODE1, 0)
    # set LEDs controllable by both PWM and GRPPWM registers
    self.setReg(REG_OUTPUT, 0xFF)
    # set MODE2 values
    # 0010 0000 -> 0x20  (DMBLNK to 1, ie blinky mode)
    self.setReg(REG_MODE2, 0x20)
    self.setColorWhite()
    
  def character_write(self, data):
    RGB1602_I2C.writeto_mem(LCD_ADDRESS, 0x40, bytes([data]))
        
  def setColorWhite(self):
    self.setRGB(255, 255, 255)
