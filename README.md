# GasEnWaterTeller Project
These python files are used on a raspberry pi 3. 

- rpi3/GetIP.py: to get the IP adres of the rpi3 for remote access.
- rpi3/ISODataUpload20.py: file that calculates the numberof pulses per quarter of an hour and pushes this data to firebase 
- rpi3/ISOLogReed.py: file that listens to the pulse and save the time each puls occurs on disk.
- rpi3/ISOUpload.py: file to upload data files to dropbox. Not required to get the data. Only usefull as backup for data
- extra/FillDatabase.py: file to upload data to firebase based on backup files
- extra/data/200111_iso_data_water.txt: example file of backup data

