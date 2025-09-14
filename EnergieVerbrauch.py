import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable
import datetime

# Constants
GAS_TO_KWH = 10.9  # Conversion factor from cubic meters of gas to kWh

# Function to convert m3 of gas to kWh
def convert_m3_to_kWh(m3):
    # Convert cubic meters of gas to kWh
    return m3 * GAS_TO_KWH

# Preprocess the data
def preprocess_data(df):
    # Preprocess the data: handle missing values, convert units, etc.

    df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
    # Change electricity counter after changing counter
    condition = df['Date'] > np.datetime64('2023-11-11')
    # Apply a calculation to the selected rows
    df.loc[condition, 'Counter_El_kWh'] = df.loc[condition, 'Counter_El_kWh'] + 17221.6

    # Resample and interpolate
    df = df.set_index('Date').resample('D').mean()
    df = df.interpolate(method='linear')

    # Add day count
    days = pd.to_numeric(df.index)
    df['Day'] = (days - days[0]) / 86400000000000

    # Convert gas to kWh
    df.Counter_Gas_kWh = convert_m3_to_kWh(df.Counter_Gas_m3)

    # Calculate differences
    df['dE_EL_kWh'] = df.Counter_El_kWh.diff(periods=1)
    df['dE_Gas_m3'] = df.Counter_Gas_m3.diff(periods=1)
    df['dE_Gas_kWh'] = convert_m3_to_kWh(df.dE_Gas_m3)

    # Fill remaining NaNs only in calculated columns
    df.fillna(0,inplace=True)
    df['dE_Combined_KWh'] = (df.dE_EL_kWh+df.dE_Gas_kWh)

    # Moving averages
    window_size = 10
    df['dE_EL_kWh_MA'] = df.dE_EL_kWh.rolling(window=window_size).mean()
    df['dE_Gas_kWh_MA'] = df.dE_Gas_kWh.rolling(window=window_size).mean()

    return df

# Convert consumption definitions to a dictionary
def consumption_dict_to_list(consumptions):
    consumption_dict = {}
    consumption_dict["Name"] = [c[0] for c in consumptions]
    consumption_dict["EL"] = [(df.Counter_El_kWh.iloc[c[2]] - df.Counter_El_kWh.iloc[c[1]]) * c[3] for c in consumptions]
    consumption_dict["GAS"] = [(df.Counter_Gas_kWh.iloc[c[2]] - df.Counter_Gas_kWh.iloc[c[1]]) * c[3] for c in consumptions]
    consumption_dict["start"] = [c[1] for c in consumptions]
    consumption_dict["end"] = [c[2] for c in consumptions]
    return consumption_dict

# Print consumption table
def consumption_table(title, consumption_dict):
    # Specify the Column Names while initializing the Table
    print(title, ": From ", df.index[consumption_dict["start"][-1]], " to ", df.index[consumption_dict["end"][-1]])

    table = PrettyTable(["What"] + consumption_dict["Name"])
    # Electricity [kWh]
    table.add_row(["Electricity [kWh]"] + [round(val, 2) for val in consumption_dict["EL"]])
    # Gas [kWh]
    table.add_row(["Gas [kWh]"] + [round(val, 2) for val in consumption_dict["GAS"]])
    # Electricity [%]
    el_total = consumption_dict["EL"][-1]
    table.add_row(
        ["Electricity [%]"] + [round(val / el_total, 2) * 100 if el_total else 0 for val in consumption_dict["EL"][:-1]] + [round(sum(consumption_dict["EL"][:-1]) / el_total, 2) * 100 if el_total else 0]
    )
    # Gas [%]
    gas_total = consumption_dict["GAS"][-1]
    table.add_row(
        ["Gas [%]"] + [round(val / gas_total, 2) * 100 if gas_total else 0 for val in consumption_dict["GAS"][:-1]] + [round(sum(consumption_dict["GAS"][:-1]) / gas_total, 2) * 100 if gas_total else 0]
    )
    # From
    table.add_row(["From"] + [df.index[start].date() for start in consumption_dict["start"]])
    # To
    table.add_row(["To"] + [df.index[end].date() for end in consumption_dict["end"]])
    print(table)

# Load data
df = pd.read_csv('EnergyCounter.csv')
df = preprocess_data(df)

# Consumption per User
##################### 2022-2023 #####################
Year1End = 365 + 2
AriEnd = 287

consumption_ari_y1 = ["Ari", 0, AriEnd, 0.5]
consumption_quentin_y1 = ["Quentin", AriEnd + 1, Year1End, 0.5]
consumption_ali_y1 = ["Alexis", 0, Year1End, 0.5]
consumption_tot_y1 = ["Total", 0, Year1End, 1.0]

consumption_y1 = consumption_dict_to_list([consumption_ari_y1, consumption_quentin_y1, consumption_ali_y1, consumption_tot_y1])

consumption_table("Year 1", consumption_y1)

##################### 2023-2024 #####################
Year2End = 365 *2 + 3
QuentinEnd = 365 * 2 - 29
AnderStart = 365 * 2 - 14

consumption_quentin_y2 = ["Quentin", Year1End+1, QuentinEnd, 0.5]
consumption_ander_y2 = ["Ander", AnderStart, Year2End, 0.5]
consumption_ali_y2 = ["Alexis", Year1End+1, Year2End, 0.5]
consumption_tot_y2 = ["Total", Year1End+1, Year2End, 1.0]

consumption_y2 = consumption_dict_to_list([consumption_quentin_y2, consumption_ander_y2, consumption_ali_y2, consumption_tot_y2])

consumption_table("Year 2", consumption_y2)

##################### 2024-2025 #####################
Year3End = 365 * 3 - 30

consumption_ander_y3 = ["Ander", Year2End+1, Year3End, 0.5]
consumption_ali_y3 = ["Alexis", Year2End+1, Year3End, 0.5]
consumption_tot_y3 = ["Total", Year2End+1, Year3End, 1.0]

consumption_y3 = consumption_dict_to_list([consumption_ander_y3, consumption_ali_y3, consumption_tot_y3])

consumption_table("Year 3", consumption_y3)

##################### Total Comparison #####################

costsTot_Gas_Y1 = 621.14  / (621.14 + 780.99) * 1356.80
costsTot_El_Y1 = 780.99 / (621.14 + 780.99) * 1356.80
costsTot_Gas_Y2 = 210.60 / (210.60 + 421.98) * 662.20
costsTot_El_Y2 = 421.98 / (210.60 + 421.98) * 662.20
costsTot_Gas_Y3 = 300 / (300 + 500) * 900
costsTot_El_Y3 = 500 / (300 + 500) * 900

print("Total Consumption Comparison over the Years")

table_Y3 = PrettyTable(["What", "Year 1", "Year 2", "Year 3"])
# Add rows
table_Y3.add_row(["Electricity [kWh]", round(consumption_y1["EL"][-1], 2),
                  round(consumption_y2["EL"][-1], 2),
                  round(consumption_y3["EL"][-1], 2)])
table_Y3.add_row(["Gas [kWh]", round(consumption_y1["GAS"][-1], 2),
                  round(consumption_y2["GAS"][-1], 2),
                  round(consumption_y3["GAS"][-1], 2)])
table_Y3.add_row(["Electricity [EUR]", round(costsTot_El_Y1, 2),
                  round(costsTot_El_Y2, 2),
                  round(costsTot_El_Y3, 2)])
table_Y3.add_row(["Gas [EUR]", round(costsTot_Gas_Y1, 2),
                  round(costsTot_Gas_Y2, 2),
                  round(costsTot_Gas_Y3, 2)])
table_Y3.add_row(["Electricity [EUR/kWh]", round(costsTot_El_Y1 / consumption_y1["EL"][-1], 2),
                  round(costsTot_El_Y2 / consumption_y2["EL"][-1], 2),
                  round(costsTot_El_Y3 / consumption_y3["EL"][-1], 2)])
table_Y3.add_row(["Gas [EUR/kWh]", round(costsTot_Gas_Y1 / consumption_y1["GAS"][-1], 2),
                  round(costsTot_Gas_Y2 / consumption_y2["GAS"][-1], 2),
                  round(costsTot_Gas_Y3 / consumption_y3["GAS"][-1], 2)])
table_Y3.add_row(["From", df.index[0].date(), df.index[Year1End+1].date(), df.index[Year2End+1].date()])
table_Y3.add_row(["To", df.index[Year1End].date(), df.index[Year2End].date(), df.index[Year3End].date()])
print(table_Y3)

print("Cost Electricity: ", consumption_y1["EL"][-1] * 0.49)
print("Cost Gas: ", consumption_y1["GAS"][-1] * 0.33)
print("Total Costs:", consumption_y1["EL"][-1] * 0.49 + consumption_y1["GAS"][-1] * 0.33)

##################### Plots #####################

fig = plt.figure()
plt.title('Moving Average Energy Consumption per Day in kWh')
plt.plot(df.index, df.dE_EL_kWh_MA, label='Electricity')
plt.plot(df.index, df.dE_Gas_kWh_MA, label='Gas')
plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Ari -> Quentin')
plt.axvline(datetime.datetime(2024, 9, 1), color = 'r', label = 'Quentin -> Ander')
plt.ylabel('Energy [kWh/d]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()


fig = plt.figure()
plt.title('Moving Average Energy Consumption per Day in kWh (Rolling Year)')
# plt.plot(index_Y1, dE_EL_kWh_MA_Y1, label='Electricity (Y1)')
plt.plot(df.Day.iloc[0:Year1End-1], df.dE_EL_kWh_MA.iloc[0:Year1End-1], 'mistyrose', label='Electricity (Y1)')
plt.plot(df.Day.iloc[Year1End:Year2End-1] - df.Day.iloc[Year1End], df.dE_EL_kWh_MA.iloc[Year1End:Year2End-1], 'coral', label='Electricity (Y2)')
plt.plot(df.Day.iloc[Year2End:-1] - df.Day.iloc[Year2End], df.dE_EL_kWh_MA.iloc[Year2End:-1], 'r', label='Electricity (Y3)')
plt.plot(df.Day.iloc[0:Year1End-1], df.dE_Gas_kWh_MA.iloc[0:Year1End-1], 'paleturquoise', label='Gas (Y1)')
plt.plot(df.Day.iloc[Year1End:Year2End-1] - df.Day.iloc[Year1End], df.dE_Gas_kWh_MA.iloc[Year1End:Year2End-1], 'deepskyblue', label='Gas (Y2)')
plt.plot(df.Day.iloc[Year2End:-1] - df.Day.iloc[Year2End], df.dE_Gas_kWh_MA.iloc[Year2End:-1], 'b', label='Gas (Y3)')
plt.ylabel('Energy [kWh/d]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

fig = plt.figure()
plt.title('Energy Consumption in kWh (Rolling Year)')
# plt.plot(index_Y1, dE_EL_kWh_MA_Y1, label='Electricity (Y1)')
plt.plot(df.Day.iloc[0:Year1End-1], df.Counter_El_kWh.iloc[0:Year1End-1] - df.Counter_El_kWh.iloc[0], 'mistyrose', label='Electricity (Y1)')
plt.plot(df.Day.iloc[Year1End:Year2End-1] - df.Day.iloc[Year1End], df.Counter_El_kWh.iloc[Year1End:Year2End-1] - df.Counter_El_kWh.iloc[Year1End], 'coral', label='Electricity (Y2)')
plt.plot(df.Day.iloc[Year2End:-1] - df.Day.iloc[Year2End], df.Counter_El_kWh.iloc[Year2End:-1] - df.Counter_El_kWh.iloc[Year2End], 'r', label='Electricity (Y3)')
plt.plot(df.Day.iloc[0:Year1End-1], (df.Counter_Gas_kWh.iloc[0:Year1End-1] - df.Counter_Gas_kWh.iloc[0]), 'paleturquoise', label='Gas (Y1)')
plt.plot(df.Day.iloc[Year1End:Year2End-1] - df.Day.iloc[Year1End], (df.Counter_Gas_kWh.iloc[Year1End:Year2End-1] - df.Counter_Gas_kWh.iloc[Year1End]), 'deepskyblue', label='Gas (Y2)')
plt.plot(df.Day.iloc[Year2End:-1] - df.Day.iloc[Year2End], (df.Counter_Gas_kWh.iloc[Year2End:-1] - df.Counter_Gas_kWh.iloc[Year2End]), 'b', label='Gas (Y3)')
plt.ylabel('Energy [kWh]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

plt.show()