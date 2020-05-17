#!/bin/python

# last changed on april 18, 2020
# version BH - 1.0
#
# this file registers the pulses in a text file
#
# changelog:
# version BH - 1.0
# - add oled screen info
# - change bounce times
#       - water 1500 ms
#       - gas 1500 ms
#

# importeer de GPIO bibliotheek.
import RPi.GPIO as GPIO
# Importeer de time biblotheek voor tijdfuncties.
from time import sleep
from datetime import datetime
import os
import sys

# for oled1302
import time
import Adafruit_SSD1306
import Adafruit_GPIO.SPI as SPI

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Zet de pinmode op Broadcom SOC.
GPIO.setmode(GPIO.BCM)
# Zet waarschuwingen uit.
GPIO.setwarnings(False)
# bepaal bestandsnaam
nu = datetime.now()
filenameISO = nu.strftime("%y%m%d_iso_data_water.txt")
padISO = '/home/pi/nutshoek/'

# pin toewijzen
pinPulsWater = 18 
pinPulsGas = 22
pinKnipperLicht = 23

class Gegevens(object):
    def __init__(self, aantalpulsen=0, pulstijd=0, pin=0):
        self.ap = aantalpulsen
        self.pt = pulstijd
        self.pin = pin

    def getData(self):
        # print("{0}+{1}j".format(self.real,self.imag))
        print("{0},{1}/{2}/{3},{4},{5},{6}.{7}".format(self.ap, self.pt.year, self.pt.month, self.pt.day, self.pt.hour,
                                                       self.pt.minute, self.pt.second, self.pt.microsecond))

    def getDataStr(self):
        seconden_sinds_middernacht = self.pt.hour * 3600 + self.pt.minute * 60 + self.pt.second + float(
            self.pt.microsecond) / 1000000
        return "{0},{1}/{2}/{3},{4},{5},{6},{7},{8}".format(self.ap, self.pt.year, self.pt.month, self.pt.day,
                                                            self.pt.hour, self.pt.minute, self.pt.second,
                                                            self.pt.microsecond, seconden_sinds_middernacht)

    def getISODataStr(self):
        seconden_sinds_middernacht = self.pt.hour * 3600 + self.pt.minute * 60 + self.pt.second + float(
            self.pt.microsecond) / 1000000
        return "{0},{1},{2},{3}".format(self.ap, self.pt.isoformat(), seconden_sinds_middernacht,self.pin)


class LeesPulsen(object):
    counter = 0
    counterWater = 0
    counterGas = 0
    vorigedatapuntgas = datetime.now()

    def __init__(self):
        self._counter = 0
        self.datapunten = []
        self.vorigedatapuntgas = datetime.now()
        # Zet de GPIO pin als ingang.
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # water
        GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # gas
        # Gebruik een interrupt, wanneer actief run subroutinne 'gedrukt'
        GPIO.add_event_detect(17, GPIO.RISING, callback=self.gedrukt, bouncetime=1500) # water
        GPIO.add_event_detect(27, GPIO.RISING, callback=self.gedrukt, bouncetime=1500) # gas

    # Deze functie wordt uitgevoerd als er op de knop gedrukt is.
    def gedrukt(self, pin):
        self._counter += 1
        nu = datetime.now()
        datapunt = Gegevens(self._counter, nu, pin)
        self.datapunten.append(datapunt)
        print("Er is gedrukt!, interrupt op pin:", pin, " aantal: ", self._counter, "tijd ", datetime.now())
        if (pin == 17):
            GPIO.output(pinPulsWater, 1)
            self.counterWater += 1
        if (pin == 27):
            GPIO.output(pinPulsGas, 1)
            tijdsverschil = nu - self.vorigedatapuntgas
            if tijdsverschil.seconds > 5:
                self.counterGas += 1
                self.vorigedatapuntgas = nu

    def getcounter(self):
        return self._counter

    def getWaterCounter(self):
        return self.counterWater

    def getGasCounter(self):
        return self.counterGas

    def resetCounters(self):
        self.counterWater = 0
        self.counterGas = 0

    def PrintDataPunten(self):
        for x in self.datapunten:
            print(x.getData())

    def WriteDataPunten(self):
        f = open(padISO + filename, "a")
        if f.tell() == 0:
            f.write('teller,datum,uur,minuut,seconde,microsec,tijdsindsmiddernacht' + os.linesep)
        while len(self.datapunten) > 0:
            tmp = self.datapunten.pop(0)
            f.write(tmp.getDataStr() + os.linesep)
        f.close()

    def WriteDataPuntenISO(self):
        f = open(padISO + filenameISO, "a")
        if f.tell() == 0:
            f.write('Teller,TijdISO,SecondenSindsMiddernacht,Pin' + os.linesep)
        while len(self.datapunten) > 0:
            tmp = self.datapunten.pop(0)
            f.write(tmp.getISODataStr() + os.linesep)
        f.close()

loper = 0
GPIO.setup(pinKnipperLicht, GPIO.OUT)  # knipperlicht
GPIO.setup(pinPulsWater, GPIO.OUT)  # lampje voor waterpulsen
GPIO.setup(pinPulsGas, GPIO.OUT)  # lampje voor gaspulsen

LP = LeesPulsen()

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)


while True:
    try:
        # even rust
        sleep(0.5)
        # puls lampje resetten
        GPIO.output(pinPulsWater, 0)
        GPIO.output(pinPulsGas, 0)
        # loop timer verhogen
        loper += 1

        # knipperlichtje schakelen
        if loper % 2 == 0:
            # even
            GPIO.output(pinKnipperLicht, 0)
        else:
            # odd
            GPIO.output(pinKnipperLicht, 1)

        # wegschrijven data naar file
        if loper > 120:
            # print(" --> pulsen: ", LP.getcounter())
            loper = 0
            # LP.PrintDataPunten()
            nu = datetime.now()
            filenameISO = nu.strftime("%y%m%d_iso_data_water.txt")
            LP.WriteDataPuntenISO()
            seconden = nu.hour*3600 + nu.minute*60 + nu.second
            if seconden > 86280:
                LP.resetCounters()


        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
        cmd = "hostname -I | cut -d\' \' -f1"
        IP = subprocess.check_output(cmd, shell=True)
        # cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        # CPU = subprocess.check_output(cmd, shell=True)
        # cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        # MemUsage = subprocess.check_output(cmd, shell=True)
        # cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        # Disk = subprocess.check_output(cmd, shell=True)

        # Write two lines of text.

        draw.text((x, top), "Gas & Water teller", font=font, fill=255)
        draw.text((x, top + 8), "G: " + str(LP.counterGas) + "p, " + str(LP.counterGas/100.0) + "m3", font=font, fill=255)
        draw.text((x, top + 16), "W: " + str(LP.counterWater) + "p, " + str(LP.counterWater/2.0) + "l.", font=font, fill=255)
        draw.text((x, top + 25), "IP: " + str(IP), font=font, fill=255) # str(Disk), font=font, fill=255)

        # Display image.
        disp.image(image)
        disp.display()

        # Wanneer er op CTRL+C gedrukt wordt.
    except KeyboardInterrupt:
        # GPIO netjes afsluiten
        GPIO.output(pinKnipperLicht, 0)
        GPIO.cleanup()
        sleep(0.3)
        sys.exit("User exit in while loop")
