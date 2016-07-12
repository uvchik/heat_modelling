# -*- coding: utf-8 -*-
"""

"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')

# read csv
df = pd.read_csv('~/ownCloudZNES/openmodsh/simon/heat_data/060-41-4-B.csv',
                   sep=";", skiprows=7, encoding="ISO-8859-1")

# new col names in dictionary
col_names = {'Unnamed: 0': 'year',
           'Unnamed: 1':'district_id',
           'Unnamed: 2':'district',
           'insgesamt':'total',
           'Kohle':'coal',
           'Heizöl':'oil',
           'Erdgas':'gas',
           'Erneuerbare Energien':'renewables',
           'Strom':'electricity',
           'Wärme':'heat',
           'Sonstige Energieträger':'other'}

# rename columns with col_names dictionary
df.rename(columns=col_names, inplace=True)

# drop first unwanted row with index 0 (units and NANs )
df.dropna(how='any', axis=0, inplace=True)

# drop column 'total' and
df.drop(['total'], axis=1, inplace=True)

# remove unwanted elements (names + whitespace) from district column strings
df['district'] = df['district'].str.replace(
      ',|Kreis|Landkreis|Kreisfreie|freie|krsfr.|Stadt|Landeshauptstadt|Hansestadt|Stat. Region,','').str.strip()

# convert column to type str
df['district_id'] = df['district_id'].astype(int).astype(str)

# set new multiindex
df.set_index(['year', 'district_id', 'district'], inplace=True)
# sort dataframe (better for indexing etc. )
df.sortlevel(inplace=True)

# replace text in columnsand convert to integer
func = lambda x: x.str.replace('-|\.', '0').astype(int)
df = df.apply(func, axis=1)



####################### select subset
# select subdata set by partial index
year = '2011'
ids = tuple(map(str, [1001, 1002, 1003, 1004, 1051, 1053, 1054, 1055, 1056,
                      1057, 1058, 1059, 1060, 1061, 1062]))
ix = pd.IndexSlice
sh_df = df.loc[ix[year, ids], :]
#sh_df = df[df.index.map(lambda x: str(x[0]).startswith('10'))]

# assumptions for average conversion efficiecies
conversion_factors= {'coal': 0.85,
                     'gas': 0.85,
                     'oil': 0.80,
                     'renewables': 0.60,
                     'other': 0.80,
                     'heat': 1}
#
def summed_heat(df, f=conversion_factors):
    summed = sum(df[col] / f[col] for col in df if col!='electricity')
    return summed
heat = summed_heat(sh_df)

####################### plotting
# convert data to MWh
# the data is 1000 MJ = 1 GJ. Conversion to MWh: 1 GJ /3.6 GJ/MWh = 0.277 MWh
heat = heat / 3.6
# convert MWh to TWh
heat = heat / 1e6

ax = heat.plot(kind='bar')
ax.set_xticklabels(heat.index.get_level_values('district').values,
                   rotation=45)