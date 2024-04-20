import pandas as pd
import csv

#file names
start_file = 'energy_data_full.csv'
end_file = 'energy_data_short.csv'

#read in full energy database from 2016 city and energy profiles
# data accessed from: data.openei.org/submissions/149
temp_db = pd.read_csv(start_file, usecols=[1, 4, 14, 19, 29, 36, 47, 51])
#this gives the columns for
#  1 --- state abbreviation
#  4 --- city name
#  14 -- Residential electricity consumption (MWh) --> R_E
#  19 -- Residential natural gas consumption (Mcf) --> R_NG
#  29 -- State calculation Commercial electricity consumption (MWh) --> SC_C_E
#  36 -- State calculation Commercial natural gas consumption (Mcf) --> SC_C_NG
#  47 -- Industry electricity consumption (MWh) --> I_E
#  51 -- Industry natural gas consumption (Mcf) --> I_NG

#make new dataframe to hold desired information
#  'comb.' --> combined [residential, commercial, industry']
db = pd.DataFrame(data=None, columns=['State', 'City', 'Total Power (MWh)', 'Comb. R', 'Comb. C', 'Comb. I'])
db['State'] = temp_db['state_abbr']

#Edits:
#  1 -- remove last word in city name
new_cities = []
for city in temp_db['city_name']:
    full_name = city.split(' ')
    correct_name = full_name[0]
    for i in range(1, len(full_name)-1):
        correct_name += ' '+full_name[i]
    new_cities.append(correct_name)

db['City'] = new_cities

#  2 -- turn numbers into actual numbers
def make_numbers(df, column):
    # remove first and last spaces, strip commas, return series of floats
    # assumes format str ' #,### ' for unknown size of number
    new_num = []
    for value in df[column]:
        all = value.split(' ')
        number = all[1]
        if number == '-':
            num = 0
        else:
            numbers = number.split(',')
            num_str = ''
            for i in range(0, len(numbers)):
                num_str += numbers[i]
            num = float(num_str)
        new_num.append(num)
    return new_num

temp_db['R_E_consumption_MWh'] = make_numbers(temp_db, 'R_E_consumption_MWh')
temp_db['R_NG_consumption_Mcf'] = make_numbers(temp_db, 'R_NG_consumption_Mcf')
temp_db['SC_C_E_consumption_MWh'] = make_numbers(temp_db, 'SC_C_E_consumption_MWh')
temp_db['SC_C_NG_consumption_Mcf'] = make_numbers(temp_db, 'SC_C_NG_consumption_Mcf')
temp_db['I_E_consumption_MWh'] = make_numbers(temp_db, 'I_E_consumption_MWh')
temp_db['I_NG_consumption_Mcf'] = make_numbers(temp_db, 'I_NG_consumption_Mcf')

#  3 -- convert natural gas use from Mcf to MWh equivalent
CONVERSION = 0.003 # 1 Mcf natural gas = 0.003 MWh
r = temp_db['R_NG_consumption_Mcf']*CONVERSION
c = temp_db['SC_C_NG_consumption_Mcf']*CONVERSION
i = temp_db['I_NG_consumption_Mcf']*CONVERSION

#  4 -- calculate combined energy need and totals per city
db['Comb. R'] = temp_db['R_E_consumption_MWh']+r
db['Comb. C'] = temp_db['SC_C_E_consumption_MWh']+c
db['Comb. I'] = temp_db['I_E_consumption_MWh']+i
db['Total Power (MWh)'] = round(db['Comb. R'] + db['Comb. C'] + db['Comb. I'], 3)

#Make new csv file with edited dataframe
db.to_csv(end_file, index=False)

