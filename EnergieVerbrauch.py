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
  
def plot_rolling_year(df, year_ends, mode='ma'):
    """
    Extensible rolling year plot.
    mode: 'ma', 'cumulative', or any custom string.
    custom_func: function(df, start_idx, end_idx) -> (x, y_el, y_gas, ylabel, title)
    """

    plt.figure()
    colors_el = ['#ffe5e5', '#ffb3b3', '#ff6666', '#cc0000', '#660000', '#2d0000']
    colors_gas = ['#e0f7fa', '#80deea', '#26c6da', '#00838f', '#004d4d', '#002222']
    n_years = len(year_ends)
    start_idx = 0

    
    for i in range(n_years):
        end_idx = year_ends[i]
        color_el = colors_el[i % len(colors_el)]
        color_gas = colors_gas[i % len(colors_gas)]
        x = df.Day.iloc[start_idx:end_idx-1] - df.Day.iloc[start_idx]
        if mode == 'ma':
            y_el = df.dE_EL_kWh_MA.iloc[start_idx:end_idx-1]
            y_gas = df.dE_Gas_kWh_MA.iloc[start_idx:end_idx-1]
            ylabel = 'Energy [kWh/d]'
            title = 'Moving Average Energy Consumption per Day in kWh (Rolling Year)'
        elif mode == 'cumulative':
            y_el = df.Counter_El_kWh.iloc[start_idx:end_idx-1] - df.Counter_El_kWh.iloc[start_idx]
            y_gas = df.Counter_Gas_kWh.iloc[start_idx:end_idx-1] - df.Counter_Gas_kWh.iloc[start_idx]
            ylabel = 'Energy [kWh]'
            title = 'Energy Consumption in kWh (Rolling Year)'
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        plt.plot(x, y_el, color=color_el, label=f'Electricity (Y{i+1})')
        plt.plot(x, y_gas, color=color_gas, label=f'Gas (Y{i+1})')
        start_idx = end_idx
    plt.ylabel(ylabel)
    plt.xlabel('Day')
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()
    plt.tight_layout()

def total_comparison_table(year_labels, consumption_total_el, consumption_total_gas, costs_total_el, costs_total_gas, df, year_ends):
    print("Total Consumption Comparison over the Years")

    table = PrettyTable(["What", "Unit"] + year_labels)
    # Electricity (kWh)
    table.add_row(["Electricity", "kWh"] + [round(val, 2) for val in consumption_total_el])
    # Gas (kWh)
    table.add_row(["Gas", "kWh"] + [round(val, 2) for val in consumption_total_gas])
    # Electricity (EUR)
    table.add_row(["Electricity", "EUR"] + [round(val, 2) for val in costs_total_el])
    # Gas (EUR)
    table.add_row(["Gas", "EUR"] + [round(val, 2) for val in costs_total_gas])
    # Electricity (EUR/kWh)
    table.add_row(["Electricity", "EUR/kWh"] + [round(costs_total_el[i] / consumption_total_el[i], 2) if consumption_total_el[i] else 0 for i in range(len(year_labels))])
    # Gas (EUR/kWh)
    table.add_row(["Gas", "EUR/kWh"] + [round(costs_total_gas[i] / consumption_total_gas[i], 2) if consumption_total_gas[i] else 0 for i in range(len(year_labels))])
    # Total Costs (EUR)
    table.add_row(["Total Costs", "EUR"] + [round(costs_total_el[i] + costs_total_gas[i], 2) for i in range(len(year_labels))])
    # From
    from_dates = [df.index[0].date()] + [df.index[year_ends[i-1]+1].date() for i in range(1, len(year_labels))]
    table.add_row(["From", "yyyy-mm-dd"] + from_dates)
    # To
    to_dates = [df.index[year_ends[i]].date() for i in range(len(year_labels))]
    table.add_row(["To", "yyyy-mm-dd"] + to_dates)
    print(table)

# Load data
df = pd.read_csv('EnergyCounter.csv')
df = preprocess_data(df)

# Consumption per User
last_day = round(df.Day.iloc[-1])
year_ends = [365 + 2, 365 * 2 + 3, 365 * 3 + 3, last_day]  # End of Year 1, Year 2, Year 3
print("Year ends at indices: ", year_ends)
plot_rolling_year(df, year_ends, mode='ma')
plot_rolling_year(df, year_ends, mode='cumulative')

##################### 2022-2023 #####################
AriEnd = 287

consumption_ari_y1 = ["Ari", 0, AriEnd, 0.5]
consumption_quentin_y1 = ["Quentin", AriEnd + 1, year_ends[0], 0.5]
consumption_ali_y1 = ["Alexis", 0, year_ends[0], 0.5]
consumption_tot_y1 = ["Total", 0, year_ends[0], 1.0]

consumption_y1 = consumption_dict_to_list([consumption_ari_y1, consumption_quentin_y1, consumption_ali_y1, consumption_tot_y1])

consumption_table("Year 1", consumption_y1)

##################### 2023-2024 #####################
QuentinEnd = 365 * 2 - 29
AnderStart = 365 * 2 - 14

consumption_quentin_y2 = ["Quentin", year_ends[0]+1, QuentinEnd, 0.5]
consumption_ander_y2 = ["Ander", AnderStart, year_ends[1], 0.5]
consumption_ali_y2 = ["Alexis", year_ends[0]+1, year_ends[1], 0.5]
consumption_tot_y2 = ["Total", year_ends[0]+1, year_ends[1], 1.0]

consumption_y2 = consumption_dict_to_list([consumption_quentin_y2, consumption_ander_y2, consumption_ali_y2, consumption_tot_y2])

consumption_table("Year 2", consumption_y2)

##################### 2024-2025 #####################
consumption_ander_y3 = ["Ander", year_ends[1]+1, year_ends[2], 0.5]
consumption_ali_y3 = ["Alexis", year_ends[1]+1, year_ends[2], 0.5]
consumption_tot_y3 = ["Total", year_ends[1]+1, year_ends[2], 1.0]

consumption_y3 = consumption_dict_to_list([consumption_ander_y3, consumption_ali_y3, consumption_tot_y3])

consumption_table("Year 3", consumption_y3)

##################### 2025-2026 #####################

consumption_ander_y4 = ["Ander", year_ends[2]+1, last_day, 0.5]
consumption_ali_y4 = ["Alexis", year_ends[2]+1, last_day, 0.5]
consumption_tot_y4 = ["Total", year_ends[2]+1, last_day, 1.0]

consumption_y4 = consumption_dict_to_list([consumption_ander_y4, consumption_ali_y4, consumption_tot_y4])

consumption_table("Year 4", consumption_y4)

##################### Total Comparison #####################

costsTot_Gas_Y1 = 621.14  / (621.14 + 780.99) * 1356.80
costsTot_El_Y1 = 780.99 / (621.14 + 780.99) * 1356.80
costsTot_Gas_Y2 = 210.60 / (210.60 + 421.98) * 662.20
costsTot_El_Y2 = 421.98 / (210.60 + 421.98) * 662.20
costsTot_Gas_Y3 = 323.23 / (323.23 + 483.43) * 951.46
costsTot_El_Y3 = 483.43 / (323.23 + 483.43) * 951.46
# speculation:

costs_total_el = [costsTot_El_Y1, costsTot_El_Y2, costsTot_El_Y3]
costs_total_gas = [costsTot_Gas_Y1, costsTot_Gas_Y2, costsTot_Gas_Y3]
consumption_total_el = [consumption_y1["EL"][-1], consumption_y2["EL"][-1], consumption_y3["EL"][-1]]
consumption_total_gas = [consumption_y1["GAS"][-1], consumption_y2["GAS"][-1], consumption_y3["GAS"][-1]]

year_labels = [f"Year {i+1}" for i in range(len(costs_total_el))]
total_comparison_table(year_labels, consumption_total_el[:len(costs_total_el)], consumption_total_gas[:len(costs_total_gas)], costs_total_el[:len(costs_total_el)], costs_total_gas[:len(costs_total_gas)], df, year_ends)

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

plt.show()


