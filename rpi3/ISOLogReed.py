#!/bin/python

# last changed on march 8, 2020
# version BH - 1.1
#
# this file checks change of pins and logs the detected pulses
#
# changelog:
# version BH - 1.0 - feb 28, 2020
# only pin 17 is used.
# version BH - 1.1 - march 8, 2020
# add pin 27 for use with gas counter.



# importeer de GPIO bibliotheek.
import RPi.GPIO as GPIO
# Importeer de time biblotheek voor tijdfuncties.
from time import sleep
from datetime import datetime
import os
import sys

# Zet de pinmode op Broadcom SOC.
GPIO.setmode(GPIO.BCM)
# Zet waarschuwingen uit.
GPIO.setwarnings(False)
# bepaal bestandsnaam
nu = datetime.now()
filenameISO = nu.strftime("%y%m%d_iso_data_water.txt")
padISO = '/home/pi/nutshoek/'

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

    def __init__(self):
        self._counter = 0
        self.datapunten = []
        # Zet de GPIO pin als ingang.
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # water
        GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # gas
        # Gebruik een interrupt, wanneer actief run subroutinne 'gedrukt'
        GPIO.add_event_detect(17, GPIO.RISING, callback=self.gedrukt, bouncetime=50)
        GPIO.add_event_detect(27, GPIO.RISING, callback=self.gedrukt, bouncetime=100)

    # Deze functie wordt uitgevoerd als er op de knop gedrukt is.
    def gedrukt(self, pin):
        self._counter += 1
        datapunt = Gegevens(self._counter, datetime.now(), pin)
        self.datapunten.append(datapunt)
        print("Er is gedrukt!, interrupt op pin:", pin, " aantal: ", self._counter, "tijd ", datetime.now())
        GPIO.output(18, 1)

    def getcounter(self):
        return self._counter

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
GPIO.setup(23, GPIO.OUT)  # knipperlicht
GPIO.setup(18, GPIO.OUT)  # lampje voor pulsen

LP = LeesPulsen()
while True:
    try:
        # even rust
        sleep(0.5)
        # puls lampje resetten
        GPIO.output(18, 0)
        # loop timer verhogen
        loper += 1

        # knipperlichtje schakelen
        if loper % 2 == 0:
            # even
            GPIO.output(23, 0)
        else:
            # odd
            GPIO.output(23, 1)

        # wegschrijven data naar file
        if loper > 120:
            # print(" --> pulsen: ", LP.getcounter())
            loper = 0
            # LP.PrintDataPunten()
            nu = datetime.now()
            filenameISO = nu.strftime("%y%m%d_iso_data_water.txt")
            LP.WriteDataPuntenISO()
        # Wanneer er op CTRL+C gedrukt wordt.
    except KeyboardInterrupt:
        # GPIO netjes afsluiten
        GPIO.output(23, 0)
        GPIO.cleanup()
        sleep(0.3)
        sys.exit("User exit in while loop")
