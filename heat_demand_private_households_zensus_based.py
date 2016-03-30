# -*- coding: utf-8 -*-
"""
Script reads csv-file with data for apartments from zensus database.


Data structure looks like:

...
Vor 1919;Unter 30;1 Wohnung;3;3;23;-;6;-;9;3;6;3;3;-;-;6;-
Vor 1919;Unter 30;2 Wohnungen;3;6;(22);-;13;18;(34);23;7;-;19;(9);11;9;4
Vor 1919;Unter 30;3 - 6 Wohnungen;192;119;221;50;98;(48);(111);(50);(69);41;(103);97;38;(83);38
...

1st column: Year (class) of building
2nd column: Size (class) of apartment
3rd column: Number of Apartments
4th - to last column: Number of Apartments per Region



"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.style.use('ggplot')


# read csv file (skip unwanted rows at the beginning of the file...)
df = pd.read_csv("./heat_data/apartments_sh.csv", sep=";", encoding="ISO-8859-1",
                 skiprows=5)
#%%
####################### renaming columns ######################################

# names of all value columns for schleswig holstein (columnames 4 - last column)
rename_dict = {'010010000000 Flensburg, Stadt (Kreisfreie Stadt)': 'FL',
               '010020000000 Kiel, Landeshauptstadt (Kreisfreie Stadt)':'KI',
               '010030000000 Lübeck, Hansestadt (Kreisfreie Stadt)':'HL',
               '010040000000 Neumünster, Stadt (Kreisfreie Stadt)':'NMS',
               '01051 Dithmarschen (Kreis)': 'HEI',
               '01053 Herzogtum Lauenburg (Kreis)':'RZ',
               '01054 Nordfriesland (Kreis)':'NF',
               '01055 Ostholstein (Kreis)':'OH',
               '01056 Pinneberg (Kreis)':'PI',
               '01057 Plön (Kreis)':'PLÖ',
               '01058 Rendsburg-Eckernförde (Kreis)':'RD',
               '01059 Schleswig-Flensburg (Kreis)':'SL',
               '01060 Segeberg (Kreis)':'SE',
               '01061 Steinburg (Kreis)':'IZ',
               '01062 Stormarn (Kreis)':'OD',
               '02 Hamburg (Bundesland)':'HH',
               '01 Schleswig-Holstein (Bundesland)':'SH'}

# index columns (check column order in csv file for correct naming)
index = {"Unnamed: 0":"age",
         "Unnamed: 1":"size_of_apartment",
         "Unnamed: 2":"n_apartments"}

# update the dict that will be used for renaming the dataframe
rename_dict.update(index)

# drop nan from last rows occuring from unneeded informations in csv-file
df.dropna(inplace=True, axis=0, how="any")

# rename the columns from the csv file
df.rename(columns=rename_dict, inplace=True)
#%%
################## creating multi index and renaming index    #################

# set "multi-index" from certain columns (s. above dictionary index)
df.set_index(["age", "size_of_apartment", "n_apartments"], inplace=True)

# dictionaries for renaming the indices
size_mapper = {'Insgesamt':0,
                'Unter 30':20,
                '30 - 39':30,
                '40 - 49':40,
                '50 - 59':50,
                '60 - 69':60,
                '70 - 79':70,
                '80 - 89': 80,
                '90 - 99': 90,
                '100 - 109':100,
                '110 - 119':110,
                '120 - 129':120,
                '130 - 139':130,
                '140 - 149':140,
                '150 - 159':150,
                '160 - 169':160,
                '170 - 179':170,
                '180 und mehr':200}

n_apartment_mapper = {'1 Wohnung':1,
                      '13 und mehr Wohnungen':13,
                      '2 Wohnungen':2,
                      '3 - 6 Wohnungen':4,
                      '7 - 12 Wohnungen':7}

age_mapper  = {'Vor 1919': 0,
               '1919 - 1948':1,
               '1949 - 1978':2,
               '1979 - 1986':3,
               '1987 - 1990':4,
               '1991 - 1995':5,
               '1996 - 2000':6,
               '2001 - 2004':7,
               '2005 - 2008':8,
               '2009 und später':9}

# function for mapping new values on indices
def map_level(df, dc, level=0):
    index = df.index
    index.set_levels([[dc.get(item, item) for item in names]
                     if i==level else names
                     for i, names in enumerate(index.levels)], inplace=True)
# make sure that the order of indices is size_of_apartment, age and not different
#if df.index.names[1] != "age":
#    df.index = df.index.swaplevel(0,1)
map_level(df, age_mapper, 0)
map_level(df, size_mapper, 1)
map_level(df, n_apartment_mapper, 2)

# convert to integer (remove some stuff from entries in rows)
for col in df:
    df[col] = df[col].str.replace('-', '0')
    df[col] = df[col].str.replace('(','')
    df[col] = df[col].str.replace(')','')
    df[col] = df[col].astype(int)

# df is now a dataframe with two index columns age, size_of_apartments
# and integer values in columns for number of the types of apartments
#%%
#############  Calculate the heat consumption  ################################


# read typical energy heat demand consumption per year of construction and
# housetype
ec = pd.read_csv('./heat_data/specific_heat_consumption_by_building_class_sh.csv')
ec.set_index(['age', "modernized", "Typ"], inplace=True)

# create new dataframe based on index levels from ec
multiindex = pd.MultiIndex.from_product([ec.index.levels[0],
                                         ec.index.levels[2]],
                                         names=['age', 'typ'])
average_energy = pd.DataFrame(index= multiindex, columns=['value'])

ix = pd.IndexSlice

# walk through first index (age)
for i in ec.index.get_level_values("age").unique():
    # walk through third index ("Typ")
    for k in ec.index.get_level_values("Typ").unique():
        # multipy share with value to get weighted energy consumption per
        # year-class
        sub = ec.ix[ix[i,:,k]]['share'] *  ec.ix[ix[i,:,k]]['parameter']
        # \sum_i (share_i * value_i) , \forall i in ages \forall k in Typ
        average_energy.loc[(i, k), 'value'] = sub.sum()

# create two dataframes (area, energy) with the same structure as df
area = pd.DataFrame(index=pd.MultiIndex.from_tuples(df.index.copy()),
                    columns=df.columns.copy())
energy = area.copy()
# with this for loop the energy/area dataframe is filled
#
for a in df.index.get_level_values('age').unique():
    for s in df.index.get_level_values('size_of_apartment').unique():
        for n in df.index.get_level_values('n_apartments').unique():
           # area = size_of_apartment * number_of_apartments
           area.loc[(a, s, n)] = s*df.loc[(a, s, n)]
           if n > 2:
               htype = 'MFH'
           else:
               htype = 'EFH'
           # add houstype column (not very nice....)
           df.loc[(a,s,n), 'housetype'] = htype

           # calculate energy : area * average_area
           energy.loc[(a,s,n)] = area.loc[(a,s,n)] * \
                           average_energy.loc[(int(a), htype), 'value']
           # add housetype column to energy-dataframe
           energy.loc[(a,s,n), 'housetype'] = htype
#%%
############  prepare for bdew equation    ####################################
# determine the age structure of buildings
# Data from
# "Andwendung von Standardlastprofilen zur Belieferung nicht
#  leistungsgemessener Kunden", BDEW 2006
# get the structure of age pre region
# convert index to normal columns
sub = df.copy()
sub.reset_index(level=["size_of_apartment","n_apartments"],
               inplace=True, drop=True)
sub.drop("housetype", axis=1, inplace=True)
# select and sum all buildings older than class 2 (<=1978)
number_old_buildings = sub[sub.index <= 2].sum()
# select all building young buildings
#new = sub[sub.age > 2].sum()
share_old_buildings = number_old_buildings / sub.sum()
share_old_buildings = share_old_buildings.to_frame()
share_old_buildings.dropna(inplace=True)
# invertvals take from bdew
intervals = [0.405, 0.455, 0.555, 0.605, 0.655, 0.705, 0.755, 0.805, 0.855]
# add category corresponding to share as column
share_old_buildings['category'] = pd.cut(share_old_buildings[0],
                                         bins=intervals, labels=[8,7,6,5,4,3,2,1])

#%%
############## calculate timeseries based on bdew profiles ####################

# TODO: replace with representative temperature timeseries for each region
data = pd.read_csv("/home/simon/znes/projects/oemof/oemof_base/examples/development_examples/example_data.csv")

# sum energy for every region grouped by housetype
energy_per_region = energy.groupby('housetype').sum()

# create a empty dataframe with one column per region
temperature_data = pd.DataFrame(columns=energy.drop('housetype', axis=1).columns.copy())
# create a empty data frame for timeseries with one column per region
energy_series = pd.DataFrame(columns=temperature_data.columns.copy())
# import heat profile
from oemof.demandlib import bdew_heatprofile as heat_profile

# regions are columns
for r in energy_per_region.columns:
    # houstypes are rows (index)
    temp_energyseries = pd.DataFrame()
    for h in energy_per_region.index:
        # create energy timeseries per region
       temp_energyseries[h] = heat_profile.create_bdew_profile(
            datapath="/home/simon/znes/projects/oemof/oemof_base/oemof/demandlib/bdew_data",
            year=2011, temperature=data["temperature"],
            # TODO: Replace 'EFH' with h (once bug is resolved in oemof bdew heatprofile)
            annual_heat_demand=energy_per_region.loc[h, r], shlp_type='EFH',
            building_class=share_old_buildings['category'][r], wind_class=1)
    energy_series[r] = temp_energyseries.sum(axis=1)

#%%
############# some calculations based on generated data #######################
print("Yearly Energy consumption of private households in GWh :",
      energy_per_region.sum()/1e6)
average_apartment_size = area.sum() / df.sum()
by_housetype = df.groupby('housetype').sum()
share_of_efh = by_housetype.ix['EFH'] / df.sum()

total_heat_consumption = energy.sum().drop('housetype').sum()

if False:
    plotting = energy_series.sort_values(by=[i for i in energy_series.columns.values],
                                         ascending=[True]*15)
    plotting.reset_index().plot()

#%%

ax = average_energy.unstack().plot(kind='bar', colormap="Blues")
ax.set_ylabel("Durschnittlicher Wärmebedarf pro Jahr in kWh/m2")
ax.set_xlabel("Age")
ax.legend(average_energy.index.get_level_values('typ').unique(), loc='best')
#ax.set_xticks(df.index)
#ax.set_xticklabels(names, rotation=45)
