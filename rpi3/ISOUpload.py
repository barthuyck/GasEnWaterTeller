#!/bin/python

# last changed on feb 28, 2020
# version BH - 1.0
#
# this file checks change of pins and logs the detected pulses
#
# changelog:
# version BH - 1.0
# credentials removed from this file

import os
import os.path
import sys
import time
import dropbox
import dropbox.files
from datetime import datetime
import json

with open('./dropboxcredentials.json', 'r') as json_file:
    dropboxcredentials = json.load(json_file)
    #json.dump(dropboxcredentials, json_file)

# print(dropboxcredentials)

dbx = dropbox.Dropbox(dropboxcredentials['credentials'])

# check your account
print(dbx.users_get_current_account())

# data directory to by uploaded
Datadir = '/home/pi/nutshoek/'
DBBasisDir = '/nutshoek/'
# list all filenames in a list
filenamesPI = next(os.walk(Datadir))[2]

f1 = open(Datadir + "log.txt", 'a')
TXTFileNames = []
# Find all TXT files
for filenamePI in filenamesPI:
    if 'txt' or 'py' in filenamePI.lower():
        TXTFileNames.append(filenamePI)
        print(filenamePI)
        f1.write(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "to upload: " + filenamePI + "\n")
for TXTFileName in TXTFileNames:
    f1.write(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Upload started: " + TXTFileName + ' - ')
    if (os.path.isfile(Datadir + TXTFileName)):
        # try:
        f2 = open(Datadir + TXTFileName, 'rb')
        try:
            dbx.files_upload(f2.read(), DBBasisDir + TXTFileName, mode=dropbox.files.WriteMode('overwrite', None),
                                autorename=True, mute=False)
            f1.write("file uploaded %s\n" % (Datadir + TXTFileName))
        except Exception as err:
            print(datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Failed to upload %s\n%s" % (TXTFileName, err))
            f1.write(
                datetime.now().strftime("%a %y/%m/%d %H:%M:%S : ") + "Failed to upload %s\n%s\n" % (TXTFileName, err))
        f2.close()
    else:
        f1.write('No file found: ' + Datadir + TXTFileName + '\n')
f1.close()