# last changed on feb 28, 2020
# version BH - 1.0
#
# this file gets the current IP adress of the raspberry pi 3 wifi lan interface
#
# changelog:


import socket
import datetime
import time
import sys
import os.path

def get_local_ip_address(target):
  ipaddr = ''
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target, 8000))
    ipaddr = s.getsockname()[0]
    s.close()
  except:
    pass

  return ipaddr

def getMAC(interface):
  # Return the MAC address of interface
  try:
    str = open('/sys/class/net/' + interface + '/address').read()
  except:
    str = "00:00:00:00:00:00"
  return str[0:17]

today = datetime.datetime.today()
Timestamp =  'Last update: ' + str(today.strftime('%d-%m-%Y %H:%M:%S')) + '\n'

dataFile = open('./IP_Address.txt', 'w')
dataFile.write(Timestamp)
dataFile.write("Local IP Address: " + get_local_ip_address('10.0.1.1') +'\n')
dataFile.write("MAC Address: " + getMAC('wlan0'))
dataFile.close()
