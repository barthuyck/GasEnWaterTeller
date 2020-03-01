# last changed on feb 28, 2020
# version BH - 1.0
#
# this file uploads all datafiles to the firebase database
#
# changelog:
# version BH - 1.0
# -clean up code
# -pulses to liter conversion
# -change database string
#
# version BH - 0.1
# -first version august 2019
#
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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

# de datum van vandaag
vandaag = datetime.now() # - timedelta(days=2)
print(vandaag)
#bestandsnaam maken
pad = "/home/pi/nutshoek/"
# gebruiker
userid = u'dhcuudje' #
# pad = "/home/bart/PycharmProjects/WaterEnGasVerbruik/"
bestandsnaam = pad + vandaag.strftime('%y%m%d') + "_iso_data_water.txt"
# inlezen bestand
data = pd.read_csv(bestandsnaam)
# kolom met seconden sinds middernacht selecteren
tijddiff = data.loc[ : , 'SecondenSindsMiddernacht' ].diff()
# tijdsverschil bepalen tussen de verschillende meetpunten en toevoegen aan de kolom 'tijdsverschil'
data.loc[:, 'tijdsverschil'] = tijddiff
# verwijderen punten die om minder dan 2 seconden van elkaar liggen. Dit is een fout in de registratie
wel = data["tijdsverschil"] > 2
# selecteer enkel die datapunten waarbij hettijdsverschil meer dan 2 seconden bedraagt
waterdata = data.loc[wel]
# bepaal aantal pulsen per kwartier: deel darvoor de tijd door 900 om te weten in welk kwartier de puls valt.
# Tel nadien al de gelijke nummers
waterdata.loc[:, 'barchart'] = (waterdata["SecondenSindsMiddernacht"]/900).apply(np.floor)
pulsenperkwartier = waterdata['barchart'].value_counts().sort_index()
print(pulsenperkwartier)
# reindex om kwartieren zonder pulsen ook in dataframe te hebben
pulsenperkwartier = pulsenperkwartier.reindex(range(0,95), fill_value=0)
print(pulsenperkwartier)
# Zet de pulsen om in liter
literperkwartier = pulsenperkwartier/2
#ter info
print("totaal aantal liter: " + str(sum(literperkwartier)))

# op te slaan
# -datum
# -aantal liter
# -array met liter per kwartier

middernacht = vandaag.replace(hour=0, minute=0, second=0, microsecond=0)
seconden_sinds_middernacht = (vandaag - middernacht).seconds
kwartieren_sinds_middernacht = math.floor(seconden_sinds_middernacht/900)
te_controleren_index = kwartieren_sinds_middernacht - 1
print("te controleren index" + str(te_controleren_index))

if te_controleren_index > 0:
    if (pulsenperkwartier[te_controleren_index] > 0) | (te_controleren_index>94):
        #inloggen in firebase
        cred = credentials.Certificate(pad + "nuts-verbruik-firebase-adminsdk-qiq4p-2a438f625b.json")
        firebase_admin.initialize_app(cred)
        # maak DB connectie
        db = firestore.client()
        # gegevens voor in de databank
        dag = 'D' + vandaag.strftime('%Y%m%d') # dag in het jaar
        meetdatum = vandaag.isoformat() # string met ISO datumformaat
        meetliterwatervandaag = sum(literperkwartier)
        meetliterwaterperkwartier = []
        for i in range(len(literperkwartier)) :
            meetliterwaterperkwartier.append(literperkwartier[i])

        meetwaarden = Meetdata(meetdatum,meetliterwatervandaag,meetliterwaterperkwartier)

        try:
            col_ref = db.collection(u'users').document(userid).collection(u'meetgegevens').document(dag)
            col_ref.set(meetwaarden.to_dict())
            print('Wegschrijven naar Firebase ok')
        except google.cloud.exceptions.NotFound:
             print('Wegschrijven naar Firebase mislukt!')
    else:
        print('Niets geupload')

