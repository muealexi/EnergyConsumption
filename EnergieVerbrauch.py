import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable
import datetime

# Constants
GAS_TO_KWH = 10.9  # Conversion factor from cubic meters of gas to kWh
VAT = 1.2  # Bills.csv: fixed part is net, total is gross
ENERGIES = {"EL": "electricity", "GAS": "gas"}  # Keys in the consumption dict -> Bills.csv

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
    df['Day'] = (df.index - df.index[0]).days  # unit-independent (pandas 3 stores datetimes in us, not ns)

    # Convert gas to kWh
    df['Counter_Gas_kWh'] = convert_m3_to_kWh(df.Counter_Gas_m3)

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
def consumption_dict_to_list(df, consumptions):
    consumption_dict = {}
    consumption_dict["Name"] = [c[0] for c in consumptions]
    # Entry: [name, start, end, share, *extra (start, end, share) periods]
    periods = [[tuple(c[1:4])] + list(c[4:]) for c in consumptions]
    consumption_dict["EL"] = [sum((df.Counter_El_kWh.iloc[e] - df.Counter_El_kWh.iloc[s]) * f for s, e, f in p) for p in periods]
    consumption_dict["GAS"] = [sum((df.Counter_Gas_kWh.iloc[e] - df.Counter_Gas_kWh.iloc[s]) * f for s, e, f in p) for p in periods]
    consumption_dict["DAYS"] = [sum((e - s) * f for s, e, f in p) for p in periods]
    consumption_dict["start"] = [p[0][0] for p in periods]
    consumption_dict["end"] = [p[-1][1] for p in periods]
    return consumption_dict

# Split each bill: fixed part by days present x share, variable part by kWh.
# Without a bill yet, estimate from the latest bill: its fixed rates at the end of the
# period, and its average price per kWh without the one-off electricity subsidy.
def add_costs(consumption_dict, bills, year):
    rows = bills[bills.year == year]
    consumption_dict["estimate"] = rows.empty
    if rows.empty:
        rows = bills[bills.year == bills.year.max()]
    consumption_dict["bill_year"] = rows.year.iloc[0]
    for key, energy in ENERGIES.items():
        r = rows[rows.energy == energy].iloc[0]
        fixed = r.fixed_net_eur * VAT
        variable = r.total_eur - fixed
        if consumption_dict["estimate"]:
            # ponytail: last bill's prices carried forward, the real bill replaces this
            calendar_days = consumption_dict["DAYS"][-1] + 1  # DAYS counts intervals, first day included
            fixed = r.fixed_rate_net_eur_per_year * VAT * calendar_days / 365
            variable = (variable - r.subsidy_eur) / r.kwh * consumption_dict[key][-1]
        # Normalised over the people, so gaps (e.g. an empty room) are still fully paid
        days, kwh = consumption_dict["DAYS"][:-1], consumption_dict[key][:-1]
        eur = [fixed * d / (sum(days) or 1) + variable * k / (sum(kwh) or 1) for d, k in zip(days, kwh)]
        assert abs(sum(eur) - fixed - variable) < 0.01, "people's shares must add up to the bill"
        consumption_dict["EUR_" + key] = eur + [fixed + variable]

# Print consumption table
def consumption_table(title, consumption_dict, df):
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
    # Costs [EUR]
    est = f" (est. Y{consumption_dict['bill_year']} prices)" if consumption_dict["estimate"] else ""
    table.add_row([f"Electricity [EUR]{est}"] + [round(val, 2) for val in consumption_dict["EUR_EL"]])
    table.add_row([f"Gas [EUR]{est}"] + [round(val, 2) for val in consumption_dict["EUR_GAS"]])
    table.add_row([f"Total [EUR]{est}"] + [round(a + b, 2) for a, b in zip(consumption_dict["EUR_EL"], consumption_dict["EUR_GAS"])])
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

def total_comparison_table(results, df):
    print("Total Consumption Comparison over the Years (est. = no bill yet)")
    labels = [f"Year {i+1}" + (" (est.)" if c["estimate"] else "") for i, c in enumerate(results)]
    el = [c["EL"][-1] for c in results]
    gas = [c["GAS"][-1] for c in results]
    eur_el = [c["EUR_EL"][-1] for c in results]
    eur_gas = [c["EUR_GAS"][-1] for c in results]

    table = PrettyTable(["What", "Unit"] + labels)
    table.add_row(["Electricity", "kWh"] + [round(val, 2) for val in el])
    table.add_row(["Gas", "kWh"] + [round(val, 2) for val in gas])
    table.add_row(["Electricity", "EUR"] + [round(val, 2) for val in eur_el])
    table.add_row(["Gas", "EUR"] + [round(val, 2) for val in eur_gas])
    table.add_row(["Electricity", "EUR/kWh"] + [round(e / k, 2) if k else 0 for e, k in zip(eur_el, el)])
    table.add_row(["Gas", "EUR/kWh"] + [round(e / k, 2) if k else 0 for e, k in zip(eur_gas, gas)])
    table.add_row(["Total Costs", "EUR"] + [round(a + b, 2) for a, b in zip(eur_el, eur_gas)])
    table.add_row(["From", "yyyy-mm-dd"] + [df.index[c["start"][-1]].date() for c in results])
    table.add_row(["To", "yyyy-mm-dd"] + [df.index[c["end"][-1]].date() for c in results])
    print(table)

def plot_timeline(df):
    plt.figure()
    plt.title('Moving Average Energy Consumption per Day in kWh')
    plt.plot(df.index, df.dE_EL_kWh_MA, label='Electricity')
    plt.plot(df.index, df.dE_Gas_kWh_MA, label='Gas')
    plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Ari -> Quentin')
    plt.axvline(datetime.datetime(2024, 9, 1), color = 'r', label = 'Quentin -> Ander')
    plt.axvline(datetime.datetime(2026, 7, 1), color = 'r', label = '+ Ines')
    plt.axvline(datetime.datetime(2026, 11, 1), color = 'r', label = '- Ander')
    plt.ylabel('Energy [kWh/d]')
    plt.xlabel('Date')
    plt.xticks(rotation=45)
    plt.grid()
    plt.legend()

# Year boundaries and who lived here when, with which share
def define_years(df):
    last_day = round(df.Day.iloc[-1])
    Y1End = df.index.get_loc(pd.Timestamp('2023-10-02'))
    Y2End = df.index.get_loc(pd.Timestamp('2024-10-02'))
    Y3End = df.index.get_loc(pd.Timestamp('2025-10-02'))
    Y4End = df.index.get_loc(pd.Timestamp('2026-10-02'))
    year_ends = [Y1End, Y2End, Y3End, Y4End, last_day]  # last_day = Year 5 so far

    ##################### 2022-2023 #####################
    AriEnd = 287
    y1 = [
        ["Ari", 0, AriEnd, 0.5],
        ["Quentin", AriEnd + 1, Y1End, 0.5],
        ["Alexis", 0, Y1End, 0.5],
        ["Total", 0, Y1End, 1.0],
    ]

    ##################### 2023-2024 #####################
    QuentinEnd = 365 * 2 - 29
    AnderStart = 365 * 2 - 14
    y2 = [
        ["Quentin", Y1End+1, QuentinEnd, 0.5],
        ["Ander", AnderStart, Y2End, 0.5],
        ["Alexis", Y1End+1, Y2End, 0.5],
        ["Total", Y1End+1, Y2End, 1.0],
    ]

    ##################### 2024-2025 #####################
    y3 = [
        ["Ander", Y2End+1, Y3End, 0.5],
        ["Alexis", Y2End+1, Y3End, 0.5],
        ["Total", Y2End+1, Y3End, 1.0],
    ]

    ##################### 2025-2026 #####################
    # 3 people from 1st of July 2026
    InesStart = df.index.get_loc(pd.Timestamp('2026-07-01'))
    y4 = [
        ["Ander", Y3End+1, InesStart, 0.5, (InesStart, Y4End, 1/3)],
        ["Ines", InesStart, Y4End, 1/3],
        ["Alexis", Y3End+1, InesStart, 0.5, (InesStart, Y4End, 1/3)],
        ["Total", Y3End+1, Y4End, 1.0],
    ]

    ##################### 2026-2027 #####################
    # Ander lives here until end of October 2026, then only Ines and Alexis (1/2 each).
    # Clamped to last_day while the data doesn't reach 1st of November yet.
    AnderEnd = min(df.index.searchsorted(pd.Timestamp('2026-11-01')), last_day)
    y5 = [
        ["Ander", Y4End+1, AnderEnd, 1/3],
        ["Ines", Y4End+1, AnderEnd, 1/3, (AnderEnd, last_day, 0.5)],
        ["Alexis", Y4End+1, AnderEnd, 1/3, (AnderEnd, last_day, 0.5)],
        ["Total", Y4End+1, last_day, 1.0],
    ]

    return year_ends, [y1, y2, y3, y4, y5]

# Load data and compute consumption and costs per person for every year
def compute():
    df = preprocess_data(pd.read_csv('EnergyCounter.csv'))
    bills = pd.read_csv('Bills.csv', parse_dates=['from', 'to'])
    year_ends, years = define_years(df)
    results = []
    for i, entries in enumerate(years, start=1):
        consumption_dict = consumption_dict_to_list(df, entries)
        add_costs(consumption_dict, bills, i)
        results.append(consumption_dict)
    return df, year_ends, results

if __name__ == '__main__':
    df, year_ends, results = compute()
    print("Year ends at indices: ", year_ends)
    for i, consumption_dict in enumerate(results, start=1):
        consumption_table(f"Year {i}", consumption_dict, df)
    total_comparison_table(results, df)

    plot_rolling_year(df, year_ends, mode='ma')
    plot_rolling_year(df, year_ends, mode='cumulative')
    plot_timeline(df)
    plt.show()
