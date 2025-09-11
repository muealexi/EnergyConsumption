import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable
import datetime


def convert_m3_to_kWh(m3):
    kWh = m3 * 10.9
    return kWh

df = pd.read_csv('EnergyCounter.csv')

df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
# Change electricity counter after changing counter
condition = df['Date'] > np.datetime64('2023-11-11')
# Apply a calculation to the selected rows
df.loc[condition, 'Counter_El_kWh'] = df.loc[condition, 'Counter_El_kWh'] + 17221.6

df = df.set_index('Date').resample('D').mean()
df = df.interpolate(method='linear')

days = pd.to_numeric(df.index)
df['Day'] = (days - days[0]) / 86400000000000
df.Counter_Gas_kWh = convert_m3_to_kWh(df.Counter_Gas_m3)
df['dE_EL_kWh'] = df.Counter_El_kWh.diff(periods=1)
df['dE_Gas_m3'] = df.Counter_Gas_m3.diff(periods=1)
df['dE_Gas_kWh'] = convert_m3_to_kWh(df.dE_Gas_m3)
df.fillna(0,inplace=True)
df['dE_Combined_KWh'] = (df.dE_EL_kWh+df.dE_Gas_kWh)

window_size = 10
df['dE_EL_kWh_MA'] = df.dE_EL_kWh.rolling(window=window_size).mean()
df['dE_Gas_kWh_MA'] = df.dE_Gas_kWh.rolling(window=window_size).mean()

# Consumption per User
##################### 2022-2023 #####################
Year1End = 365 + 2
AriEnd = 287
consumptionTot_El = (df.Counter_El_kWh.iloc[Year1End] - df.Counter_El_kWh.iloc[0])
consumptionTot_Gas = (df.Counter_Gas_kWh.iloc[Year1End] - df.Counter_Gas_kWh.iloc[0])

consumptionAri_El = (df.Counter_El_kWh.iloc[AriEnd] - df.Counter_El_kWh.iloc[0]) / 2
consumptionAri_Gas = (df.Counter_Gas_kWh.iloc[AriEnd] - df.Counter_Gas_kWh.iloc[0]) / 2
consumptionQuentin_El = (df.Counter_El_kWh.iloc[Year1End] - df.Counter_El_kWh.iloc[AriEnd+1]) / 2
consumptionQuentin_Gas = (df.Counter_Gas_kWh.iloc[Year1End] - df.Counter_Gas_kWh.iloc[AriEnd+1]) / 2
consumptionAli_El = (df.Counter_El_kWh.iloc[Year1End] - df.Counter_El_kWh.iloc[0]) / 2
consumptionAli_Gas = (df.Counter_Gas_kWh.iloc[Year1End] - df.Counter_Gas_kWh.iloc[0]) / 2

# Specify the Column Names while initializing the Table
print("First Year: From ", df.index[0], " to ", df.index[Year1End])

table_Y1 = PrettyTable(["What", "Ari", "Quentin", "Alexis", "Total"])
# Add rows
table_Y1.add_row(["Electricity [kWh]", round(consumptionAri_El, 2),
                  round(consumptionQuentin_El, 2),
                  round(consumptionAli_El, 2),
                  round(consumptionTot_El, 2)])
table_Y1.add_row(["Gas [kWh]", round(consumptionAri_Gas, 2),
                  round(consumptionQuentin_Gas, 2),
                  round(consumptionAli_Gas, 2),
                  round(consumptionTot_Gas, 2)])
table_Y1.add_row(["Electricity [%]", round(consumptionAri_El / consumptionTot_El, 2),
                  round(consumptionQuentin_El / consumptionTot_El, 2),
                  round(consumptionAli_El / consumptionTot_El, 2),
                  round((consumptionAri_El + consumptionQuentin_El + consumptionAli_El) / consumptionTot_El, 2)])
table_Y1.add_row(["Gas [%]", round(consumptionAri_Gas / consumptionTot_Gas, 2),
                  round(consumptionQuentin_Gas / consumptionTot_Gas, 2),
                  round(consumptionAli_Gas / consumptionTot_Gas, 2),
                  round((consumptionAri_Gas + consumptionQuentin_Gas + consumptionAli_Gas) / consumptionTot_Gas, 2)])
table_Y1.add_row(["From", df.index[0].date(), df.index[AriEnd].date(), df.index[0].date(), df.index[0].date()])
table_Y1.add_row(["To", df.index[AriEnd].date(), df.index[Year1End].date(), df.index[Year1End].date(), df.index[Year1End].date()])
print(table_Y1)


##################### 2023-2024 #####################
Year2End = 365 *2 + 3
QuentinEnd = 365 * 2 - 29
AnderStart = 365 * 2 - 14
consumptionTot_El_Y2 = (df.Counter_El_kWh.iloc[Year2End] - df.Counter_El_kWh.iloc[Year1End+1])
consumptionTot_Gas_Y2 = (df.Counter_Gas_kWh.iloc[Year2End] - df.Counter_Gas_kWh.iloc[Year1End+1])

consumptionAnder_El = (df.Counter_El_kWh.iloc[Year2End] - df.Counter_El_kWh.iloc[AnderStart]) / 2
consumptionAnder_Gas = (df.Counter_Gas_kWh.iloc[Year2End] - df.Counter_Gas_kWh.iloc[AnderStart]) / 2
consumptionQuentin_El_Y2 = (df.Counter_El_kWh.iloc[QuentinEnd] - df.Counter_El_kWh.iloc[Year1End+1]) / 2
consumptionQuentin_Gas_Y2 = (df.Counter_Gas_kWh.iloc[QuentinEnd] - df.Counter_Gas_kWh.iloc[Year1End+1]) / 2
consumptionAli_El_Y2 = (df.Counter_El_kWh.iloc[AnderStart] - df.Counter_El_kWh.iloc[QuentinEnd]) / 2 + (df.Counter_El_kWh.iloc[Year2End] - df.Counter_El_kWh.iloc[Year1End + 1]) / 2
consumptionAli_Gas_Y2 = (df.Counter_Gas_kWh.iloc[AnderStart] - df.Counter_Gas_kWh.iloc[QuentinEnd]) / 2 + (df.Counter_Gas_kWh.iloc[Year2End] - df.Counter_Gas_kWh.iloc[Year1End + 1]) / 2

# Specify the Column Names while initializing the Table
print("\n Second Year: From ", df.index[Year1End+1], " to ", df.index[Year2End])
table_Y2 = PrettyTable(["What", "Ander", "Quentin", "Alexis", "Total"])
# Add rows
table_Y2.add_row(["Electricity [kWh]", round(consumptionAnder_El, 2),
                  round(consumptionQuentin_El_Y2, 2),
                  round(consumptionAli_El_Y2, 2),
                  round(consumptionTot_El_Y2, 2)])
table_Y2.add_row(["Gas [kWh]", round(consumptionAnder_Gas, 2),
                  round(consumptionQuentin_Gas_Y2, 2),
                  round(consumptionAli_Gas_Y2, 2),
                  round(consumptionTot_Gas_Y2, 2)])
table_Y2.add_row(["Electricity [%]", round(consumptionAnder_El / consumptionTot_El_Y2  * 100, 3),
                  round(consumptionQuentin_El_Y2 / consumptionTot_El_Y2 * 100, 3),
                  round(consumptionAli_El_Y2 / consumptionTot_El_Y2 * 100, 3),
                  round((consumptionAnder_El + consumptionQuentin_El_Y2 + consumptionAli_El_Y2) / consumptionTot_El_Y2  * 100, 3)])
table_Y2.add_row(["Gas [%]", round(consumptionAnder_Gas / consumptionTot_Gas_Y2  * 100, 3),
                  round(consumptionQuentin_Gas_Y2 / consumptionTot_Gas_Y2  * 100, 3),
                  round(consumptionAli_Gas_Y2 / consumptionTot_Gas_Y2  * 100, 3),
                  round((consumptionAnder_Gas + consumptionQuentin_Gas_Y2 + consumptionAli_Gas_Y2) / consumptionTot_Gas_Y2  * 100, 3)])
table_Y2.add_row(["From", df.index[AnderStart].date(), df.index[Year1End+1].date(), df.index[Year1End+1].date(), df.index[Year1End+1].date()])
table_Y2.add_row(["To", df.index[Year2End].date(), df.index[QuentinEnd].date(), df.index[Year2End].date(), df.index[Year2End].date()])
print(table_Y2)

##################### 2024-2025 #####################
Year3End = 365 * 3 - 30
consumptionTot_El_Y3 = (df.Counter_El_kWh.iloc[Year3End] - df.Counter_El_kWh.iloc[Year2End+1])
consumptionTot_Gas_Y3 = (df.Counter_Gas_kWh.iloc[Year3End] - df.Counter_Gas_kWh.iloc[Year2End+1])

consumptionAnder_El_Y2 = (df.Counter_El_kWh.iloc[Year3End] - df.Counter_El_kWh.iloc[Year2End + 1]) / 2
consumptionAnder_Gas_Y2 = (df.Counter_Gas_kWh.iloc[Year3End] - df.Counter_Gas_kWh.iloc[Year2End + 1]) / 2
consumptionAli_El_Y3 = (df.Counter_El_kWh.iloc[Year3End] - df.Counter_El_kWh.iloc[Year2End + 1]) / 2
consumptionAli_Gas_Y3 = (df.Counter_Gas_kWh.iloc[Year3End] - df.Counter_Gas_kWh.iloc[Year2End + 1]) / 2

# Specify the Column Names while initializing the Table
print("\n Third Year: From ", df.index[Year2End+1], " to ", df.index[Year3End])
table_Y3 = PrettyTable(["What", "Ander", "Alexis", "Total"])
# Add rows
table_Y3.add_row(["Electricity [kWh]", round(consumptionAnder_El_Y2, 2),
                  round(consumptionAli_El_Y3, 2),
                  round(consumptionTot_El_Y3, 2)])
table_Y3.add_row(["Gas [kWh]", round(consumptionAnder_Gas_Y2, 2),
                  round(consumptionAli_Gas_Y3, 2),
                  round(consumptionTot_Gas_Y3, 2)])
table_Y3.add_row(["Electricity [%]", round(consumptionAnder_El_Y2 / consumptionTot_El_Y3  * 100, 3),
                  round(consumptionAli_El_Y3 / consumptionTot_El_Y3 * 100, 3),
                  round((consumptionAnder_El_Y2 + consumptionAli_El_Y3) / consumptionTot_El_Y3  * 100, 3)])
table_Y3.add_row(["Gas [%]", round(consumptionAnder_Gas_Y2 / consumptionTot_Gas_Y3  * 100, 3),
                  round(consumptionAli_Gas_Y3 / consumptionTot_Gas_Y3  * 100, 3),
                  round((consumptionAnder_Gas_Y2 + consumptionAli_Gas_Y3) / consumptionTot_Gas_Y3  * 100, 3)])
table_Y3.add_row(["From", df.index[Year2End+1].date(), df.index[Year2End+1].date(), df.index[Year2End+1].date()])
table_Y3.add_row(["To", df.index[Year3End].date(), df.index[Year3End].date(), df.index[Year3End].date()])
print(table_Y3)

##################### Total Comparison #####################

costsTot_Gas_Y1 = 621.14  / (621.14 + 780.99) * 1356.80
costsTot_El_Y1 = 780.99 / (621.14 + 780.99) * 1356.80
costsTot_Gas_Y2 = 210.60 / (210.60 + 421.98) * 662.20
costsTot_El_Y2 = 421.98 / (210.60 + 421.98) * 662.20
costsTot_Gas_Y3 = 300 / (300 + 500) * 900
costsTot_El_Y3 = 500 / (300 + 500) * 900

table_Y3 = PrettyTable(["What", "Year 1", "Year 2", "Year 3"])
# Add rows
table_Y3.add_row(["Electricity [kWh]", round(consumptionTot_El, 2),
                  round(consumptionTot_El_Y2, 2),
                  round(consumptionTot_El_Y3, 2)])
table_Y3.add_row(["Gas [kWh]", round(consumptionTot_Gas, 2),
                  round(consumptionTot_Gas_Y2, 2),
                  round(consumptionTot_Gas_Y3, 2)])
table_Y3.add_row(["Electricity [EUR]", round(costsTot_El_Y1, 2),
                  round(costsTot_El_Y2, 2),
                  round(costsTot_El_Y3, 2)])
table_Y3.add_row(["Gas [EUR]", round(costsTot_Gas_Y1, 2),
                  round(costsTot_Gas_Y2, 2),
                  round(costsTot_Gas_Y3, 2)])
table_Y3.add_row(["Electricity [EUR/kWh]", round(costsTot_El_Y1 / consumptionTot_El, 2),
                  round(costsTot_El_Y2 / consumptionTot_El_Y2, 2),
                  round(costsTot_El_Y3 / consumptionTot_El_Y3, 2)])
table_Y3.add_row(["Gas [EUR/kWh]", round(costsTot_Gas_Y1 / consumptionTot_Gas, 2),
                  round(costsTot_Gas_Y2 / consumptionTot_Gas_Y2, 2),
                  round(costsTot_Gas_Y3 / consumptionTot_Gas_Y3, 2)])
table_Y3.add_row(["From", df.index[0].date(), df.index[Year1End+1].date(), df.index[Year2End+1].date()])
table_Y3.add_row(["To", df.index[Year1End].date(), df.index[Year2End].date(), df.index[Year3End].date()])
print(table_Y3)

print("Cost Electricity: ", consumptionTot_El * 0.49)
print("Cost Gas: ", consumptionTot_Gas * 0.33)
print("Total Costs:", consumptionTot_El * 0.49 + consumptionTot_Gas * 0.33)


# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    # print(df)
    # print(df.dtypes)
# print(df.index)

# fig = plt.subplots()
# plt.title('Energy Consumption per Day in kWh')
# plt.plot(df.index, df.dE_EL_kWh, label='Electricity')
# plt.plot(df.index, df.dE_Gas_kWh, label='Gas')
# plt.plot(df.index, df.dE_Combined_KWh, label='Combined')
# plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Change Date')
# plt.xlabel('Date')
# plt.ylabel('Energy [kWh/d]')
# plt.xticks(rotation=45)
# plt.grid()
# plt.legend()

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