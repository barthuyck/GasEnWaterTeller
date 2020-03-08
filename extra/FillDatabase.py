# last changed on feb 28, 2020
# version BH - 1.0
#
# this file uploads all datafiles to the firebase database
#
# changelog:
# version BH - 1.0
# -clean up code
# -add some info
#
# version BH - 0.1
# -first version
#


#import os
import os.path
#import sys
import time
#from datetime import datetime

import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import datetime
# import matplotlib.dates as mdates
import firebase_admin
from firebase_admin import credentials, firestore
import math

# [START custom_class_def]
class Meetdata(object):
    def __init__(self, datum, literwatervandaag = 0.0, literwaterperkwartier=[]):
        self.datum = datum
        self.literwatervandaag = literwatervandaag
        self.literwaterperkwartier = literwaterperkwartier

    @staticmethod
    def from_dict(source):
        # [START_EXCLUDE]
        meetdata = Meetdata(source[u'datum'])
        if u'literwatervandaag' in source:
            meetdata.literwatervandaag = source[u'literwatervandaag']
        if u'literwaterperkwartier' in source:
            meetdata.literwaterperkwartier = source[u'literwaterperkwartier']
        return meetdata
        # [END_EXCLUDE]
    def to_dict(self):
        # [START_EXCLUDE]
        dest = {
            u'datum': self.datum
        }
        if self.literwatervandaag:
            dest[u'literwatervandaag'] = self.literwatervandaag
        if self.literwaterperkwartier:
            dest[u'literwaterperkwartier'] = self.literwaterperkwartier
        return dest
        # [END_EXCLUDE]

    def __repr__(self):
        return(
            u'Meetdata(datum={}, literwatervandaag={}, literwaterperkwartier={})'
            .format(self.datum, self.literwatervandaag, self.literwaterperkwartier))
# [END custom_class_def]

# data directory to by uploaded
Datadir = './data/' # path for with csv files to be uploaded
Credpath = './' # path to .json file with firebase credentials
# gebruiker
userid = u'dhcuudje' #

# list all filenames in a list
filenames = next(os.walk(Datadir))[2]

# select only files with 'txt' and 'data' in the filename
TXTFileNames = []
for filename in filenames:
    if 'txt' and 'data' in filename.lower():
        TXTFileNames.append(filename)

# read credentials and open database
cred = credentials.Certificate(Credpath + "nuts-verbruik-firebase-adminsdk-qiq4p-2a438f625b.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

for TXTFileName in TXTFileNames:
    print(TXTFileNames)
    time.sleep(2)
    # read data from file
    data = pd.read_csv(Datadir + TXTFileName)
    # select column "TijdISO" with time in ISO string time format
    tijdISO = data.loc[: , 'TijdISO']
    vandaag = datetime.datetime.fromisoformat(tijdISO.iloc[-1])
    print(vandaag)
    tijddiff = data.loc[:, 'SecondenSindsMiddernacht'].diff()
    # add time difference betweeen the different measurement points to the column 'tijdsverschil'
    data.loc[:, 'tijdsverschil'] = tijddiff
    # select the location of the points that differ less than 2 seconds to remove extra point due to contact bouncing
    wel = data["tijdsverschil"] > 2
    # select only the data point with time difference higher thant 2 seconds
    waterdata = data.loc[wel]
    # determain the number of pulses per quarter: the time is devided by 900 to determain in with quarter sinds
    # midnight the data point is registered. Count afterwards the items with the same numbers
    waterdata.loc[:, 'barchart'] = (waterdata["SecondenSindsMiddernacht"] / 900).apply(np.floor)
    pulsenperkwartier = waterdata['barchart'].value_counts().sort_index()
    print(pulsenperkwartier)
    # reindex to add quarters without data point to dataframe (with all quarters per day
    pulsenperkwartier = pulsenperkwartier.reindex(range(0, 95), fill_value=0)
    print(pulsenperkwartier)
    # calculate liter based on number of pulses
    literperkwartier = pulsenperkwartier / 2
    # for your information
    print("total liter of water: " + str(sum(literperkwartier)))

    dag = 'D' + vandaag.strftime('%Y%m%d')  # unique indetifer for database based on date
    meetdatum = vandaag.isoformat()  # string with ISO date format
    meetliterwatervandaag = sum(literperkwartier)
    meetliterwaterperkwartier = []
    for i in range(len(literperkwartier)):
        meetliterwaterperkwartier.append(literperkwartier[i])
    # build data object for adding data to firebase
    meetwaarden = Meetdata(meetdatum, meetliterwatervandaag, meetliterwaterperkwartier)
    # check
    # print(meetwaarden)
    # write data to database
    try:
        col_ref = db.collection(u'users').document(userid).collection(u'meetgegevens').document(dag)
        col_ref.set(meetwaarden.to_dict())
        print('Wegschrijven naar Firebase ok')
    except google.cloud.exceptions.NotFound:
        print('Wegschrijven naar Firebase mislukt!')
