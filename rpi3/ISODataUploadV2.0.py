# last changed on feb 28, 2020
# version BH - 2.1
#
# this file uploads all datafiles to the firebase database
#
# changelog:
# version BH - 2.1
# -read credentials from json file
#
# version BH - 2.0
# -correct way of counting gas and water
#
# version BH - 1.1
# -add gas
#
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
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import math
import json

# de datum van vandaag
vandaag = datetime.now() # - timedelta(days=2)
print(vandaag)
# pad waar de data staat op raspberry
pad_datafile = "/home/pi/nutshoek/"
pad_credentials = "/home/pi/nutshoek/json/"

# pad waar de data staat op engineering PC
engineering = False
if engineering:
    pad_datafile = "/home/bart/PycharmProjects/gasenwaterteller/rpi3/" # txt files
    pad_credentials = "/home/bart/PycharmProjects/gasenwaterteller/" # json files

# [START load_credentials]
with open(pad_credentials + 'logingegevens.json', 'r') as json_file:
    logingegevens = json.load(json_file)
# [END load_credentials]

# laad gebruikerid
userid = logingegevens['firebaseuserid']

# [START custom_class_def]
class Meetdata(object):
    def __init__(self, datum, literwatervandaag = 0.0, literwaterperkwartier=[], litergasvandaag = 0.0, litergasperkwartier=[], mogelijksdataverlies = False):
        self.datum = datum
        self.literwatervandaag = literwatervandaag
        self.literwaterperkwartier = literwaterperkwartier
        self.litergasvandaag = litergasvandaag
        self.litergasperkwartier = litergasperkwartier
        self.mogelijksdataverlies = mogelijksdataverlies

    @staticmethod
    def from_dict(source):
        # [START_EXCLUDE]
        meetdata = Meetdata(source[u'datum'])
        if u'literwatervandaag' in source:
            meetdata.literwatervandaag = source[u'literwatervandaag']
        if u'literwaterperkwartier' in source:
            meetdata.literwaterperkwartier = source[u'literwaterperkwartier']
        if u'litergasvandaag' in source:
            meetdata.litergasvandaag = source[u'litergasvandaag']
        if u'litergasperkwartier' in source:
            meetdata.litergasperkwartier = source[u'litergasperkwartier']
        if u'mogelijksdataverlies' in source:
            meetdata.mogelijksdataverlies = source[u'mogelijksdataverlies']
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
        if self.litergasvandaag:
            dest[u'litergasvandaag'] = self.litergasvandaag
        if self.litergasperkwartier:
            dest[u'litergasperkwartier'] = self.litergasperkwartier
        if self.mogelijksdataverlies:
            dest[u'mogelijksdataverlies'] = self.mogelijksdataverlies
        return dest
        # [END_EXCLUDE]

    def __repr__(self):
        return(
            u'Meetdata(datum={}, literwatervandaag={}, literwaterperkwartier={}, litergasvandaag={}, litergasperkwartier={}, mogelijksdataverlies={})'
            .format(self.datum, self.literwatervandaag, self.literwaterperkwartier, self.litergasvandaag, self.litergasperkwartier, self.mogelijksdataverlies))
# [END custom_class_def]

# bepaal bestandsnaam
bestandsnaam = pad_datafile + vandaag.strftime('%y%m%d') + "_iso_data_water.txt"
# inlezen bestand
data = pd.read_csv(bestandsnaam)
# kolom met seconden sinds middernacht selecteren
# tijddiff = data.loc[ : , 'SecondenSindsMiddernacht' ].diff()
# tijdsverschil bepalen tussen de verschillende meetpunten en toevoegen aan de kolom 'tijdsverschil'
# data.loc[:, 'tijdsverschil'] = tijddiff
ruwewaterdata = data[data['Pin'] == 17]
# omzetten naar datetime in pandas
ruwewaterdata.loc[:,'Tijd'] = pd.to_datetime(ruwewaterdata["TijdISO"])
# bepaal tijdsverschil tussen pulsen
ruwewaterdata.loc[:,'TijdsverschilTijd'] = ruwewaterdata["Tijd"].diff()
# maak tijd als index (nodig voor selectie interval)
ruwewaterdata = ruwewaterdata.set_index(ruwewaterdata['Tijd'])
# Select observations between two datetimes
# ruwewaterdata = ruwewaterdata.loc['2020-03-22 08:25:00.00':'2020-03-22 13:27:00.00']
# selecteer enkel die datapunten waarbij het tijdsverschil meer dan 3.5 seconden bedraagt
waterdata = ruwewaterdata.loc[ruwewaterdata["TijdsverschilTijd"] > pd.Timedelta(3.5, unit='s')]
# print(waterdata)

# bepaal aantal pulsen per kwartier: deel darvoor de tijd door 900 om te weten in welk kwartier de puls valt.
# Tel nadien al de gelijke nummers
waterdata.loc[:,'barchart'] = (waterdata["SecondenSindsMiddernacht"]/900).apply(np.floor)
pulsenperkwartier = waterdata['barchart'].value_counts().sort_index()
# print(pulsenperkwartier)
# reindex om kwartieren zonder pulsen ook in dataframe te hebben
pulsenperkwartier = pulsenperkwartier.reindex(range(0,95), fill_value=0.0)
# print(pulsenperkwartier)
# Zet de pulsen om in liter
literperkwartier = pulsenperkwartier/2
# ter info
print("totaal aantal liter water: " + str(sum(literperkwartier)))

ruwegasdata = data.loc[data['Pin'] == 27]
# omzetten naar datetime in pandas
ruwegasdata.loc[:,'Tijd'] = pd.to_datetime(ruwegasdata["TijdISO"])
# bepaal tijdsverschil tussen pulsen
ruwegasdata.loc[:,'TijdsverschilTijd'] = ruwegasdata["Tijd"].diff()
# maak tijd als index (nodig voor selectie interval)
ruwegasdata = ruwegasdata.set_index(ruwegasdata['Tijd'])
# Select observations between two datetimes
#ruwegasdata = ruwegasdata.loc['2020-03-22 08:25:00.00':'2020-03-22 13:27:00.00']
# selecteer enkel die datapunten waarbij het tijdsverschil meer dan 5 seconden bedraagt
gasdata = ruwegasdata.loc[ruwegasdata["TijdsverschilTijd"] > pd.Timedelta(5, unit='s')]
# print(gasdata)

# bepaal aantal pulsen per kwartier: deel darvoor de tijd door 900 om te weten in welk kwartier de puls valt.
# Tel nadien al de gelijke nummers
gasdata.loc[:, 'barchart'] = (gasdata["SecondenSindsMiddernacht"]/900).apply(np.floor)
pulsenperkwartiergas = gasdata['barchart'].value_counts().sort_index()
# print(pulsenperkwartiergas)
# reindex om kwartieren zonder pulsen ook in dataframe te hebben
pulsenperkwartiergas = pulsenperkwartiergas.reindex(range(0,95), fill_value=0.0)
# print(pulsenperkwartiergas)
# Zet de pulsen om in liter
litergasperkwartier = pulsenperkwartiergas*10
print("totaal aantal liter gas: " + str(sum(litergasperkwartier)))

# bepaal of data geupload moet worden
middernacht = vandaag.replace(hour=0, minute=0, second=0, microsecond=0)
seconden_sinds_middernacht = (vandaag - middernacht).seconds
kwartieren_sinds_middernacht = math.floor(seconden_sinds_middernacht/900)
te_controleren_index = kwartieren_sinds_middernacht - 1
print("te controleren index: " + str(te_controleren_index))

if te_controleren_index > 0:
    if (pulsenperkwartier[te_controleren_index] > 0) | (pulsenperkwartiergas[te_controleren_index] > 0) | (te_controleren_index>94):
        print("start")
        # inloggen in firebase
        cred = credentials.Certificate(pad_credentials + "nuts-verbruik-firebase-adminsdk-qiq4p-2a438f625b.json")
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
        meetlitergasvandaag = sum(litergasperkwartier)
        meetlitergasperkwartier = []
        for i in range(len(litergasperkwartier)):
            meetlitergasperkwartier.append(litergasperkwartier[i])

        # nagaan of er mogelijk dataverlies kan zijn
        if (data["Teller"].iat[-1] - data["Teller"].iat[0] + 1 - data["Teller"].size) == 0:
            meetmogelijksdataverlies = False
        else:
            meetmogelijksdataverlies = True

        # meetwaarden in juiste structuur
        meetwaarden = Meetdata(meetdatum,meetliterwatervandaag,meetliterwaterperkwartier,meetlitergasvandaag,meetlitergasperkwartier,meetmogelijksdataverlies)

        try:
            col_ref = db.collection(u'users').document(userid).collection(u'meetgegevens').document(dag)
            col_ref.set(meetwaarden.to_dict())
            print('Wegschrijven naar Firebase ok')
        except:
             print('Wegschrijven naar Firebase mislukt!')
    else:
        print('Niets geupload')

