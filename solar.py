import requests
import csv
import pandas as pd
import numpy as np
import re
import time
import os
from datetime import datetime

t0 = time.time()

#=====START FUNCTIONS=====

#functions for accessing data
def make_url(station):
    #create full url from given station name
    baseurl = "https://www.ncei.noaa.gov/access/services/data/v1?"
    datasetid = "global-hourly"
    #max # years/query = 100
    url = "{}dataset={}&dataTypes={}&stations={}&startDate={}-{}-{}&endDate={}-{}-{}".format(
    	baseurl, datasetid, 'CIG,GG1,GF1,GJ1', station, 
        '1924', '01', '01', '2023', '12', '31'
    )
    return url

def get_stations(db, latr, longr, checked=None):
    #get list of station data from database
    #  db is database of stations to search
    #  latr and longr are ranges of latitude and longitude
    station_list = []
    for row in db.itertuples():
        #row[2] is latitude; row[3] is longitude
        if row[2] > latr[0] and row[2] < latr[1]:
            if row[3] > longr[0] and row[3] < longr[1]:
                station_list.append([row[1], row[4], row[5], row[8]])
    #return value is possile station names
    return get_names(station_list, checked)

def get_names(station_list, checked=None):
    #create list of possible station names based on known ids
    names = []
    for i in station_list:
        this_station = ''
        #grab last 5 characters of first id (always 11 characters)
        temp = list(i[0])[6:]
        id1 = ''
        for j in temp:
            id1 += j
        #if one or more of these characters is a letter, it won't be used
        char = re.compile('[A-Z]')
        if char.search(id1) != None:
            id1 = '099999' #what the database uses if id1 is "missing"
        #check for id2
        if i[-1] != -1:
            id2 = str(i[-1])
        else:
            id2 = '999999'
        if len(list(id1)) == 5 and len(list(id2)) == 5:
            #if we have both values; most likely to work
            this_station = id2 + '0' + id1
            names.append(this_station)
        else:
            if id1 == '099999' and id2 == '999999':
                #if both ids are missing
                continue
            else:
                #if only one id is missing
                this_station = id2 + id1
                #names.append(this_station)
    #remove station names that have already been checked
    #  only used if we needed to increase search radius
    if checked != None:
        for i in checked:
            matched = -1
            for j in range(0, len(names)):
                if i == names[j]:
                    matched = j
            if matched > -1:
                names.pop(matched)
    return names

def request_data(stations):
    #send the request to ncei.noaa.gov
    #  there are limits to how many requests can happen in a minute
    header = {"token": "kiJaPVLmenKFlmxVfHEwzTFDZzNuFgnV"}
    files = []
    for i in stations:
        url = make_url(i)
        #timeout to reduce chance of website throwing retries error
        r = requests.get(url, headers=header, timeout=60)
        if len(r.content) < 124:
            #file is empty but no error was raised, don't save
            continue
        elif len(r.content) == 428:
            print("Error 503 for station: ", i)
            continue
        this_filename = d_filename+'_'+i+'.csv'
        files.append(this_filename)
        with open(this_filename, "wb") as file:
            file.write(r.content)
    return files

#functions for weather analysis
def check_gf1(gf1):
    #gf1 should have form: XX,XX,X,XX,X,XX,XXXXX,X,XX,X,XX,X
    # only first two entries can be useful
    if gf1 != 'nan':
        data = int(gf1.split(',')[0])
        if data == 99:
            data = int(gf1.split(',')[1])
            if data == 99:
                #can't use gf1, return lower priority
                return -1, 2
        if data == 9 or data == 10:
            #can't use gf1, return lower priority
            return -1, 2
        if data >= 12:
            #assuming sky fully covered, return same priority
            return 1, 3
        else:
            #return % sky covered, return same priority
            return data/8, 3
    else:
        #error occured, return lower priority
        return -1, 2

def check_gj1(gj1):
    #gj1 should have form: XXXX,X
    if gj1 != 'nan':
        data = int(gj1.split(',')[0])
        if data == 9999:
            #can't use gj1, return lower priority 
            return -1, 3
        else:
            #I believe value is reported in hundreths of a minute
            #return appropriate value and same priority
            data = data/100
            return data/60, 4
    else:
        #error occured, return lower priority
        return -1, 3
                   
def check_gg1(gg1):
    #gg1 should have form: XX,X,XXXXX,X,XX,X,XX,X
    if gg1 != 'nan':
        data = int(gg1.split(',')[0])
        if data == 99:
            #can't use gg1, return lower priority 
            return -1, 1
        if data == 9 or data == 10:
            #assume sky fully covered, return same priority
            return 1, 2
        else: 
            #return appropriate value and same priority
            return data/8, 2
    else:
        #error occured, return lower priority
        return -1, 1

def check_cig(cig):
    #cig should have form: XXXXX,X,X,X
    data = int(cig.split(',')[0])
    if data == 99999:
        #can't use cig
        return -1
    if data == 22000:
        #no cloud layer, assume no coverage
        return 0
    else:
        #at least 5/8 of sky obscured
        #assume full coverage
        return 1 

#=====END FUNCTIONS=====

zip_csv = 'zip_code_database.csv'
energy_csv = 'energy_data_short.csv'

zip_db = pd.read_csv(zip_csv, usecols=[0,3,4,6,12,13])
#selected columns are: 
#  0 -- zip code
#  3 -- primary city
#  4 -- acceptable city
#  6 -- state (2 letter code)
# 12 -- latitude
# 13 -- longitude

#get city, state from user
location = input("Enter City, State: ")

#test cities
#location = 'Asheville, NC'
#location = 'Las Vegas, NV'
#location = 'Tipp City, OH'
location = location.split(', ')
city = location[0]
state = location[1]

#=====DATA RETRIEVAL=====

#prepare base filename for selected city
city_long = city.replace(' ', '_')
d_filename = city_long+'_'+state

#get coordinates for selected city based on postal codes
latitude = []
longitude = []
for row in zip_db.itertuples():
    if state == row[4]:
        if city == row[2]:
            latitude.append(row[5])
            longitude.append(row[6])

lat_range = [min(latitude), max(latitude)]
long_range = [min(longitude), max(longitude)]

#look for weather stations within coordinate range
stations_db = pd.read_csv('stations_readable.csv', low_memory=False)
stations = get_stations(stations_db, lat_range, long_range)

#look for data with station name list
files = request_data(stations)

#if no stations had data, find closeby stations to check
#expand lat and long ranges and try again
radius_increase = 0
while len(files) == 0:
    #adding one degree should increase range by ~7 miles in each direction
    lat_range = [lat_range[0]-1, lat_range[1]+1]
    long_range = [long_range[0]-1, long_range[1]+1]
    #include old stations list to remove names from list to check
    stations_new = get_stations(stations_db, lat_range, long_range, stations)
    files = request_data(stations_new)
    stations += stations_new
    radius_increase += 1

print("radius increase: ", radius_increase)

#=====ANALYZE WEATHER=====

columns=['STATION', 'YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'CIG', 'GF1', 'GG1', 'GJ1', 'PRIORITY']
combined = pd.DataFrame(columns=columns)

#check size of files to reduce memory usage
total_size = 0
for i in files:
    total_size += os.path.getsize(i)

total_size = total_size / 1000000
full_files = []
#if total_size is >200 MB, only use biggest file
#this number is based on what caused issues on my computer
if total_size > 200:
    sizes = []
    full_files = files
    for i in range(0, len(files)):
        sizes.append(os.path.getsize(files[i]))
    biggest = max(enumerate(sizes),key=lambda x: x[1])[0]
    files = [files[biggest]]

#edit files and combine into one dataframe
for i in files:
    this_df = pd.read_csv(i, low_memory=False)
    #split date/time and put in as new columns
    full_date = this_df['DATE'].to_numpy()
    dates=[]; times=[]
    for j in full_date:
        date, t = j.split('T')
        dates.append(date.split('-'))
        times.append(t.split(':'))
    this_df.insert(1, 'YEAR', [i[0] for i in dates]); this_df.insert(2, 'MONTH', [i[1] for i in dates])
    this_df.insert(3, 'DAY', [i[2] for i in dates]); this_df.insert(4, 'HOUR', [i[0] for i in times])
    this_df.insert(5, 'MINUTE', [i[1] for i in times])
    #don't need seconds column because it's always 0
    #remove unused columns
    this_df.drop(columns=['DATE', 'SOURCE', 'REPORT_TYPE', 'CALL_SIGN', 'QUALITY_CONTROL'], inplace=True)
    #make priority assessment
    priority_array = []
    for row in this_df.itertuples():
        priority = -1
        values = [str(row[7]), str(row[9]), str(row[8]), str(row[10])]
        for k in range(0, len(values)):
            if int(values[0].split(',')[0]) == 99999:
                #if there's a bad 'CIG' value, leave with lowest priority
                continue
            elif values[k] != 'nan':
                if k+1 > priority:
                    priority = k+1
        priority_array.append(priority)
    this_df.insert(len(this_df.columns), 'PRIORITY', priority_array)
    #remove bad values
    this_array = this_df.to_numpy()
    to_drop = 0
    for j in range(0, len(this_array)):
        if this_array[j][10] == -1:
            to_drop += 1
    new_array = np.zeros([len(this_array)-to_drop, 11], np.dtype('U100'))
    k = 0
    for j in this_array:
        if j[10] == -1:
            continue
        elif j[10] >= 1:
            new_array[k] = j
            k += 1
        else:
            print("Something went wrong removing bad data")
    new_df = pd.DataFrame(new_array, columns=columns)
    #put all dataframes into one
    combined = pd.concat([combined, new_df], ignore_index=True)

#sort combined dataframe by date, time, priority
df = combined.sort_values(by=['YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'PRIORITY'])

#put dates back together for new dataframe
year = df['YEAR'].to_numpy(); month = df['MONTH'].to_numpy(); day = df['DAY'].to_numpy()
full_dates = []
for i in range(0, len(year)):
    date = str(year[i])+'-'+str(month[i]).zfill(2)+'-'+str(day[i]).zfill(2)
    full_dates.append(date)

#get list of days with data
dates = np.unique(np.array(full_dates))
per_day = np.zeros(len(dates)); num_days = np.zeros(len(dates))
#weather is where we will hold our values per day
weather = np.transpose(np.concatenate([[dates, per_day, num_days]]))

#put full dates back in dataframe
df.insert(1, 'DATE', [i for i in full_dates])
df.drop(columns=['YEAR', 'MONTH', 'DAY'], inplace=True)

df.to_csv("combined_data.csv", index=False)


#get % coverage per day
last_index = 0
for i in range(0, len(weather)):
    this_date = weather[i][0]
    today = []
    sunshine = [1] #start with 100% sunshine
    for j in range(last_index, len(df)):
        if df.loc[j]['DATE'] == this_date:
            if int(df.loc[j]['HOUR']) >= 7 and int(df.loc[j]['HOUR']) <= 19:
                #aka "daytime"; 12 hours
                values = np.array([df.loc[j]['HOUR'], df.loc[j]['MINUTE'], df.loc[j]['CIG'], 
                                   df.loc[j]['GF1'], df.loc[j]['GG1'], df.loc[j]['GJ1'], df.loc[j]['PRIORITY']])
                today.append(values)
            last_index = j
        if j > last_index:
            break
    #values in today should have form: [ [hour, minute, cig, gf1, gg1, gj1, priority] ]
    #get max hours for this set (in case we're missing hours)
    if len(today) == 0:
        #didn't find any values within time range for this date
        #set flag to remove date from list
        weather[i][2] = '-1'
    else:
        max_hours = int(today[-1][0]) - int(today[0][0])
    for j in range(0, len(today)-1):
        priority = int(today[j][6])
        tomorrow = today[j+1]
        #determine time difference between values
        startminute = int(today[j][1]); endminute = int(tomorrow[1])
        min_diff = (endminute - startminute) / 60 #difference as part of an hour
        starthour = int(today[j][0]); endhour = int(tomorrow[0])
        hr_diff = endhour - starthour
        t_diff = hr_diff + min_diff
        if t_diff == 0:
            if priority >= int(tomorrow[6]) and starthour != 19:
                #meaning this value has higher or equal priority and it's not the final hour of the day
                #assign data point 1 hr portion
                t_diff = 1
            else:
                #skip to next value
                break
        portion = max_hours / t_diff #what portion of max hours is this segment
        this_value = -1
        #get data based on priority flag
        #  if check fails for higher priority, should return new flag and try again
        if priority == 4:
            this_value, priority = check_gj1(today[j][5])
        if priority == 3:
            this_value, priority = check_gf1(today[j][3])
        if priority == 2:
            this_value, priority = check_gg1(today[j][4])
        if priority == 1:
            this_value = check_cig(today[j][2])
        if this_value == -1:
            print("Something went wrong with checks")
        this_value = this_value / portion #weight value for how much of the day it is
        sun = round(sunshine[-1] - this_value, 3)
        if sun == -0.0:
            sun = 0.0 #make sure it's positive 0
        if sun < 0:
            #stop counting if day has full coverage
            break
        sunshine.append(sun)
    #save final sunshine value as percent of day clear
    if len(sunshine) > 1:
        #we have more than the starting value
        weather[i][1] = round(sunshine[-1]*100, 2)

#look for dates without data
no_data = 0
for i in weather:
    if i[2] == '-1':
        no_data += 1
        
temp = np.zeros([len(weather)-no_data, 3], np.dtype('U100'))
j = 0
for i in range(0, len(weather)):
    if float(weather[i][2]) == -1:
        continue
    else:
        temp[j] = weather[i]
        j += 1
        
weather = temp

#get count of consecutive dark days
for i in range(1, len(weather)):
    yesterday = weather[i-1]; y_day = datetime.strptime(yesterday[0], "%Y-%m-%d")
    today = weather[i];       t_day = datetime.strptime(today[0], "%Y-%m-%d")
    if (t_day-y_day).days <= 1:
        if float(today[1]) < 50 and float(yesterday[1]) < 50:
            weather[i][2] = str(float(yesterday[2])+1)

#=====OUTPUT RESULTS=====

print("Data for: "+city+', '+state)

start = weather[0][0]; end = weather[-1][0]
print("Our time frame was from "+start+" until "+end)

year1 = int(start.split('-')[0]); year2 = int(end.split('-')[0])
years = year2 - year1; days = years*365.25
missing_days = days - len(weather)
if missing_days > 1:
    print("\t"+str(missing_days)+" days are missing data")

total_days = len(weather)
below_fifty = 0
for i in weather:
    if float(i[1]) < 50:
        below_fifty += 1
percentage_dark = round((below_fifty/total_days)*100, 2)
print("Out of "+str(total_days)+" days, "+str(below_fifty)+" had 50% or more sky coverage")
print("\tThis is "+str(percentage_dark)+"% of the time")

streak = [float(day[2]) for day in weather]
max_streak = max(streak)
print("\tThe max period without a clear day was: ", max_streak, " days")

week_plus = 0
for i in range(0, len(weather)-1):
    if float(weather[i][2]) >= 7.0 and weather[i+1][2] == '0.0':
        week_plus += 1

print("\tArea was without a clear day for more than a week "+str(week_plus)+" times")
print("\tThis occurs on average "+str(round(week_plus/years, 2))+" times per year")

#Output energy data
energy_db = pd.read_csv(energy_csv)

#Get energy for selected city state
yr_energy = 0
for row in energy_db.itertuples():
    if state == row[1]:
        if city == row[2]:
            yr_energy = row[3]
print("Yearly energy usage (MWh): ", round(yr_energy, 2))

#How much sq. footage of panels needed?
#Assuming 150 W usable power per m^2 coming from 15% efficiency
use_power = 150*pow(10, -6) #convert to MW for comparison

#Calculate daily average power usage for selected city
daily_energy = yr_energy/365.25
print("\tAverage daily energy use: ", round(daily_energy, 2), " MWh")

#solar panel area
sp_area = round((daily_energy/use_power)*pow(10, -6), 3)
print("\tNeeded area (km^2) of solar panels: ", sp_area)
print("\tOr in acres: ", round(sp_area*247.10538161, 2))

#capacity factor and efficiency
capacity = round(100 - percentage_dark, 2)
efficiency = round(capacity *.15, 2)
print("Capacity factor is: ", capacity)
print("Total efficiency is: ", efficiency)

t3 = time.time()
print("time to finish: ", t3-t0)

#=====CLEAN-UP=====

#remove all data files
if len(full_files) > 0:
    files = full_files
for i in files:
    os.remove(i)