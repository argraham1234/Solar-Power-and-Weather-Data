import pandas as pd
import csv
import re

#Turns list of station names and IDs from the Global Historical Climatology Network daily (GHCNd)
#  into a usable form for solar.py. Original list includes more than 100,000 stations. 

#=====START OBJECTS=====

#create object to store station information
class Station:
    def __init__(self, raw_data):
        #set up all parameters for each station
        self.raw = raw_data
        self.id1 = -1
        self.lat = -1
        self.long = -1
        self.state = -1
        self.name = -1
        self.s1 = -1
        self.s2 = -1
        self.id2 = -1

    def check_raw(self, check):
        #checks that new value was somewhere within the raw data
        #  meant to confirm the new value wasn't created artificially in the later code
        match = -1
        for i in self.raw:
            if i == check:
                match = 0
        return match

    def set_ills(self, id1, lat, long, state):
        #sets first ID, latitude and longitude coordinates, and state abbrv.
        self.id1 = id1
        self.lat = lat
        self.long = long
        self.state = state
        matches = [self.check_raw(self.id1), self.check_raw(self.lat),
                   self.check_raw(self.long), self.check_raw(self.state)]
        for i in matches:
            #check that all the given data was present within station's raw data
            if i == -1:
                print("Something wrong with ills")
                return -1
        return "ILLS set correctly"

    def set_id2(self, id2):
        #check the second ID (the last value in the raw data)
        #this ID v a l u e   m a yt
        self.id2 = id2
        if id2 != -1:
            match = self.check_raw(self.id2)
            if match == -1:
                print("Something wrong with id2")
                return -1
        return "id2 set correctly"

    def set_sources(self, s1=-1, s2=-1):
        #data may have neither, one, or both of these sources
        self.s1 = s1
        self.s2 = s2
        if s1 != -1:
            match = self.check_raw(self.s1)
            if match == -1:
                print("Something wrong with source 1")
                return -1
        if s2 != -1:
            match = self.check_raw(self.s2)
            if match == -1:
                print("Something wrong with source 2")
                return -1
        return "Sources set correctly"

    def set_name(self, name):
        #name can be any number of words and include both numbers and special characters
        #should be set last with whatever is left after all other values found
        self.name = name
        check = name.split(' ')
        overall_match = []
        for i in check:
            overall_match.append(self.check_raw(i))
        for i in overall_match:
            if i == -1:
                print("Something went wrong with name")
                print(self.raw)
                print(name); print('\n')
                return -1
        return "Name set correctly"

    def get_unused_data(self):
        #to be used after setting ills, gives rest of raw data
        unused = self.raw[5:]
        return unused

#=====END OBJECTS=====

#get downloaded list of stations
#accessed from: https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt
with open("ghcnd_stations.csv", newline='') as file:
    reader = csv.reader(file, delimiter=' ')
    newrow = []
    for row in reader:
        #print(row)
        strrow = str(row)
        all = strrow.split(' ')
        temp = list(all[0])
        del (temp[0:2]); del (temp[-2:-1])
        #only get stations where ID1 starts with 'US'
        #this limits available stations to US states
        if temp[0] == 'U' and temp[1] == 'S':
            comb = ''
            for i in range(0, len(temp)):
                if temp[i] != ',':
                    comb += str(temp[i])
            all[0] = comb
            newrow.append(all)

#start editing format into more readable form
for i in range(0, len(newrow)):
    mark = []
    for j in range(0, len(newrow[i])):
        #removed excess characters and spaces
        if str(newrow[i][j]) == '\'\',':
            mark.append(j)
        elif j>0:
            temp = list(newrow[i][j])
            del (temp[-2:-1]); del (temp[0])
            comb = ''
            for k in temp:
                if k != ',':
                    comb += k
            newrow[i][j] = comb
    for k in range(len(mark)-1, 0, -1):
        del (newrow[i][mark[k]])
    newrow[i][-1] = newrow[i][-1][:-1]
    if newrow[i][-1] == '':
        del (newrow[i][-1])
    del (newrow[i][1])

#start making list of station objects
stations = []

#set ID1, coordinates, and state
for i in newrow:
    this_station = Station(i)
    this_station.set_ills(i[0], i[1], i[2], i[4])
    stations.append(this_station)

#set values with variable existence and length/format
for i in range(0, len(stations)):
    this_data = stations[i].get_unused_data()
    id_check = re.compile('[0-9]{5}')
    #check if last value is ID2
    if id_check.match(this_data[-1]) != None:
        if len(list(this_data[-1])) > 5:
            continue
        stations[i].set_id2(this_data[-1])
        this_data.pop(-1)
    #check for sources 1 and 2
    this_s1 = -1; this_s2 = -1
    if this_data[-1] == 'CRN' or this_data[-1] == 'HCN':
        this_s2 = this_data[-1]
        this_data.pop(-1)
    if this_data[-1] == 'GSN':
        this_s1 = this_data[-1]
        this_data.pop(-1)
    #set everything else as station name
    this_name = this_data[0]
    for j in range(1, len(this_data)):
        this_name += ' ' + this_data[j]
    stations[i].set_sources(this_s1, this_s2)
    stations[i].set_name(this_name)

#create readble file with station info
with open('stations_readable.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['ID1', 'Latitude', 'Longitude', 'State Abbr.', 'Name', 'Source1', 'Source2', 'ID2'])
    for i in stations:
        writer.writerow([i.id1, i.lat, i.long, i.state, i.name, i.s1, i.s2, i.id2])
