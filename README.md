# Solar-Power-and-Weather-Data
Code to analyze historical weather patterns and determine effective efficiency of solar panels in a user selected location within the US

=====CODE USAGE=====
The main code is solar.py and can be run without any additional commands. It will ask for the desired location in the format "City name, State abbreviation" (e.g. "Las Vegas, NV"). Currently, it can only handle input in this format. It can analyze the data for any city within the US with at least one associated postal code excluding US territories. If an appropriate weather station cannot be found with the coordinates of the selected city, the code will expand it's search radius by +/- 1 degree latitude and longitude and try again. It will continue expanding the radius until at least one station has been located. The code will report how many times it had to repeat this process as "radius increased: x" where x is the integer number of increases. 

Multiple stations may be found for a given city and therefore multiple weather data files created. If the total size of files exceeds 200MB, the largest (assumed most complete) data file will be the only one analyzed. The limiting size can be changed within solar.py. All weather data files are removed at the end of the code. The combined file (called "combined.csv") with all used data from all files, if multiple are found without exceeding the size limit, is not deleted. It does not need to be removed before running the code again, whether for the same or a different city, but will be overwritten. 

=====OUTPUT======
Currently all output from the code is just printed to the screen. All output can be found in solar.py in the section labeled "OUTPUT RESULTS". The results include the final time frame of usable data, how many days within that range are missing data (if any), number of dark days, longest dark period, number of dark periods, capacity factor, final efficiency, energy usage, needed solar panel area. A more detailed description of these values follows: 
  DATE RANGE -- code searches for data from 1924-01-01 to 2023-12-31 however it ususally cannot find data for that entire range. The actual range will be printed as start and end dates
  MISSING DAYS -- if any days within the used range are missing data, the number of days will be reported
  NUMBER OF DARK DAYS -- "dark days" refers to days with 50% or more coverage of the sky during daylight hours (assumed 7am-7pm)
  LONGEST DARK PERIOD -- longest period of consecutive dark days within the date range
  NUMBER OF DARK PERIODS -- "dark periods" refers to times with 7 or more consecutive dark days
  CAPACITY FACTOR -- calculated as the % of time a solar panel could operate at its max efficiency given this analysis
  FINAL EFFICIENCY -- the effective efficiency considering a base 15% efficiency for the panels and the given capacity factor
  ENERGY USAGE -- energy used by the selected city as a total yearly usage and daily average reported in MWh
    This data is taken from a 2016 census. The full datatable is "energy_data_full.csv" and a more detailed description can be found in "energy_data_editor.py"
  NEEDED SOLAR PANEL AREA -- assuming 150 W/m^2 of usable power, the needed area to meet the average daily power needs is given in both km^2 and acres

=====FILE DESCRIPTION=====
From this repository, solar.py should work automatically on its own and none of the other files need to be executed or edited. The following files contain the energy data used: 'energy_data_editor.py", "energy_data_full.csv", "energy_data_short.csv". The following files contain the station information used: "ghcnd_stations.csv", "station_editor.py", "stations_readable.csv". The first of these, "ghcnd_stations.csv", contains the full list of stations from GHCND (described in "station_editor.py") and has data for more than 100,000 stations. The associated editor file is used to create the more functionable file "stations_readable.csv". This limits the station list to those within the US, excluding territories. This may be edited in the future. The last file, "zip_code_database.csv", allows the code to search for coordinates for any US city with at least one associated zip code. 


