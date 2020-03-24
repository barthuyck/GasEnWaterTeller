#!/bin/python

# last changed on
# version BH - 1.1
#
# this file checks change of pins and logs the detected pulses
#
# changelog:
# version BH - 1.1 - march 24, 2020
# credentials in common separated file
#
# version BH - 1.0 - feb 28, 2020
# credentials removed from this file

import os
import os.path
import sys
import time
import dropbox
import dropbox.files
from datetime import datetime
import json

# pad waar de data staat op raspberry
# data directory to by uploaded
pad_datafile = "/home/pi/nutshoek/"
pad_credentials = "/home/pi/nutshoek/json/"
DropBoxBaseDir = '/nutshoek/'

# pad waar de data staat op engineering PC
engineering = False
if engineering:
    pad_datafile = "/home/bart/PycharmProjects/gasenwaterteller/rpi3/" # txt files
    pad_credentials = "/home/bart/PycharmProjects/gasenwaterteller/" # json files

# [START load_credentials]
with open(pad_credentials + 'logingegevens.json', 'r') as json_file:
    logingegevens = json.load(json_file)
# [END load_credentials]

dbx = dropbox.Dropbox(logingegevens['credentials'])

# check your account
print(dbx.users_get_current_account())


# list all filenames in a list
filenamesPI = next(os.walk(pad_datafile))[2]

f1 = open(pad_datafile + "log.txt", 'a')
TXTFileNames = []
# Find all TXT files
for filenamePI in filenamesPI:
    if 'txt' or 'py' in filenamePI.lower():
        TXTFileNames.append(filenamePI)
        print(filenamePI)
        f1.write(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "to upload: " + filenamePI + "\n")
for TXTFileName in TXTFileNames:
    f1.write(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Upload started: " + TXTFileName + ' - ')
    if (os.path.isfile(pad_datafile + TXTFileName)):
        # try:
        f2 = open(pad_datafile + TXTFileName, 'rb')
        try:
            dbx.files_upload(f2.read(), DropBoxBaseDir + TXTFileName, mode=dropbox.files.WriteMode('overwrite', None),
                                autorename=True, mute=False)
            f1.write("file uploaded %s\n" % (pad_datafile + TXTFileName))
        except Exception as err:
            print(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Failed to upload %s\n%s" % (TXTFileName, err))
            f1.write(
                datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Failed to upload %s\n%s\n" % (TXTFileName, err))
        f2.close()
    else:
        f1.write('No file found: ' + pad_datafile + TXTFileName + '\n')
f1.close()