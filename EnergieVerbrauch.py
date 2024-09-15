import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable
import datetime

df = pd.read_csv('EnergyCounter.csv')

df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y")
# Change electricity counter after changing counter
condition = df['Date'] > np.datetime64('2023-11-11')
# Apply a calculation to the selected rows
df.loc[condition, 'Counter_El'] = df.loc[condition, 'Counter_El'] + 17221.6

df = df.set_index('Date').resample('D').mean()
df = df.interpolate(method='linear')

days = pd.to_numeric(df.index)
df['Day'] = (days - days[0]) / 86400000000000
df['dE_EL_kWh'] = df.Counter_El.diff(periods=1)
df['dE_Gas_m3'] = df.Counter_Gas.diff(periods=1)
df['dE_Gas_kWh'] = df.dE_Gas_m3 * 10.55
df.fillna(0,inplace=True)
df['dE_Combined_KWh'] = (df.dE_EL_kWh+df.dE_Gas_kWh)

window_size = 10
df['dE_EL_kWh_MA'] = df.dE_EL_kWh.rolling(window=window_size).mean()
df['dE_Gas_kWh_MA'] = df.dE_Gas_kWh.rolling(window=window_size).mean()

df['E_El_Cost_perMonth'] = df.dE_EL_kWh_MA * 0.49 * 30.5
df['E_Gas_Cost_perMonth'] = df.dE_Gas_kWh_MA * 0.33 * 30.5
df['dE_Combined_Cost_perMonth'] = (df.E_El_Cost_perMonth+df.E_Gas_Cost_perMonth)

# Consumption per User
Year1End = 365 + 2
AriEnd = 287
consumptionTot_El = (df.Counter_El[Year1End] - df.Counter_El[0])
consumptionTot_Gas = (df.Counter_Gas[Year1End] - df.Counter_Gas[0])

consumptionAri_El = (df.Counter_El[AriEnd] - df.Counter_El[0]) / 2
consumptionAri_Gas = (df.Counter_Gas[AriEnd] - df.Counter_Gas[0]) / 2
consumptionQuentin_El = (df.Counter_El[Year1End] - df.Counter_El[AriEnd+1]) / 2
consumptionQuentin_Gas = (df.Counter_Gas[Year1End] - df.Counter_Gas[AriEnd+1]) / 2
consumptionAli_El = (df.Counter_El[Year1End] - df.Counter_El[0]) / 2
consumptionAli_Gas = (df.Counter_Gas[Year1End] - df.Counter_Gas[0]) / 2

Year2End = 365 *2 - 14
QuentinEnd = 365 * 2 - 29
AnderStart = 365 * 2 - 14
consumptionTot_El_Y2 = (df.Counter_El[Year2End] - df.Counter_El[Year1End+1])
consumptionTot_Gas_Y2 = (df.Counter_Gas[Year2End] - df.Counter_Gas[Year1End+1])

consumptionAnder_El = (df.Counter_El[Year2End] - df.Counter_El[AnderStart]) / 2
consumptionAnder_Gas = (df.Counter_Gas[Year2End] - df.Counter_Gas[AnderStart]) / 2
consumptionQuentin_El_Y2 = (df.Counter_El[QuentinEnd] - df.Counter_El[Year1End+1]) / 2
consumptionQuentin_Gas_Y2 = (df.Counter_Gas[QuentinEnd] - df.Counter_Gas[Year1End+1]) / 2
consumptionAli_El_Y2 = (df.Counter_El[AnderStart] - df.Counter_El[QuentinEnd]) / 2 + (df.Counter_El[Year2End] - df.Counter_El[Year1End + 1]) / 2
consumptionAli_Gas_Y2 = (df.Counter_Gas[AnderStart] - df.Counter_Gas[QuentinEnd]) / 2 + (df.Counter_Gas[Year2End] - df.Counter_Gas[Year1End + 1]) / 2


# Specify the Column Names while initializing the Table
print("First Year: From ", df.index[0], " to ", df.index[Year1End])

table_Y1 = PrettyTable(["What", "Ari", "Quentin", "Alexis", "Total"])
# Add rows
table_Y1.add_row(["Electricity [kWh]", round(consumptionAri_El, 2),
                  round(consumptionQuentin_El, 2),
                  round(consumptionAli_El, 2),
                  round(consumptionTot_El, 2)])
table_Y1.add_row(["Gas [m3]", round(consumptionAri_Gas, 2),
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

# Specify the Column Names while initializing the Table
print("\n Second Year: From ", df.index[Year1End+1], " to ", df.index[Year2End])
table_Y2 = PrettyTable(["What", "Ander", "Quentin", "Alexis", "Total"])
# Add rows
table_Y2.add_row(["Electricity [kWh]", round(consumptionAnder_El, 2),
                  round(consumptionQuentin_El_Y2, 2),
                  round(consumptionAli_El_Y2, 2),
                  round(consumptionTot_El_Y2, 2)])
table_Y2.add_row(["Gas [m3]", round(consumptionAnder_Gas, 2),
                  round(consumptionQuentin_Gas_Y2, 2),
                  round(consumptionAli_Gas_Y2, 2),
                  round(consumptionTot_Gas_Y2, 2)])
table_Y2.add_row(["Electricity [%]", round(consumptionAnder_El / consumptionTot_El_Y2, 3),
                  round(consumptionQuentin_El_Y2 / consumptionTot_El_Y2, 3),
                  round(consumptionAli_El_Y2 / consumptionTot_El_Y2, 3),
                  round((consumptionAnder_El + consumptionQuentin_El_Y2 + consumptionAli_El_Y2) / consumptionTot_El_Y2, 3)])
table_Y2.add_row(["Gas [%]", round(consumptionAnder_Gas / consumptionTot_Gas_Y2, 3),
                  round(consumptionQuentin_Gas_Y2 / consumptionTot_Gas_Y2, 3),
                  round(consumptionAli_Gas_Y2 / consumptionTot_Gas_Y2, 3),
                  round((consumptionAnder_Gas + consumptionQuentin_Gas_Y2 + consumptionAli_Gas_Y2) / consumptionTot_Gas_Y2, 3)])
table_Y2.add_row(["From", df.index[AnderStart].date(), df.index[Year1End+1].date(), df.index[Year1End+1].date(), df.index[Year1End+1].date()])
table_Y2.add_row(["To", df.index[Year2End].date(), df.index[QuentinEnd].date(), df.index[Year2End].date(), df.index[Year2End].date()])
print(table_Y2)

print("Cost Electricity: ", consumptionTot_El * 0.49)
print("Cost Gas: ", consumptionTot_Gas * 0.33)
print("Total Costs:", consumptionTot_El * 0.49 + consumptionTot_Gas * 0.33)


# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    # print(df)
    # print(df.dtypes)
# print(df.index)

fig = plt.subplots()
plt.title('Energy Consumption per Day in kWh')
plt.plot(df.index, df.dE_EL_kWh, label='Electricity')
plt.plot(df.index, df.dE_Gas_kWh, label='Gas')
plt.plot(df.index, df.dE_Combined_KWh, label='Combined')
plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Change Date')
plt.xlabel('Date')
plt.ylabel('Energy [kWh/d]')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

fig = plt.figure()
plt.title('Moving Average Energy Consumption per Day in kWh')
plt.plot(df.index, df.dE_EL_kWh_MA, label='Electricity')
plt.plot(df.index, df.dE_Gas_kWh_MA, label='Gas')
plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Change Date')
plt.ylabel('Energy [kWh/d]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

# fig = plt.figure()
# plt.title('Moving Average Costs per Month in EUR')
# plt.plot(df.index, df.E_El_Cost_perMonth, label='Electricity')
# plt.plot(df.index, df.E_Gas_Cost_perMonth, label='Gas')
# plt.plot(df.index, df.dE_Combined_Cost_perMonth, label='Combined')
# plt.axvline(datetime.datetime(2023, 7, 15), color = 'r', label = 'Change Date')
# plt.ylabel('Costs [EUR/m]')
# plt.xlabel('Date')
# plt.xticks(rotation=45)
# plt.grid()
# plt.legend()

fig = plt.figure()
plt.title('Moving Average Energy Consumption per Day in kWh (Rolling Year)')
# plt.plot(index_Y1, dE_EL_kWh_MA_Y1, label='Electricity (Y1)')
plt.plot(df.Day[0:364], df.dE_EL_kWh_MA[0:364], 'm', label='Electricity (Y1)')
plt.plot(df.Day[365:-1] - df.Day[365], df.dE_EL_kWh_MA[365:-1], 'r', label='Electricity (Y2)')
plt.plot(df.Day[0:364], df.dE_Gas_kWh_MA[0:364], 'c', label='Gas (Y1)')
plt.plot(df.Day[365:-1] - df.Day[365], df.dE_Gas_kWh_MA[365:-1], 'b', label='Gas (Y2)')
plt.ylabel('Energy [kWh/d]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

fig = plt.figure()
plt.title('TEnergy Consumption in kWh (Rolling Year)')
# plt.plot(index_Y1, dE_EL_kWh_MA_Y1, label='Electricity (Y1)')
plt.plot(df.Day[0:364], df.Counter_El[0:364] - df.Counter_El[0], 'm', label='Electricity (Y1)')
plt.plot(df.Day[365:-1] - df.Day[365], df.Counter_El[365:-1] - df.Counter_El[365], 'r', label='Electricity (Y2)')
plt.plot(df.Day[0:364], (df.Counter_Gas[0:364] - df.Counter_Gas[0]) * 10.55, 'c', label='Gas (Y1)')
plt.plot(df.Day[365:-1] - df.Day[365], (df.Counter_Gas[365:-1] - df.Counter_Gas[365]) * 10.55, 'b', label='Gas (Y2)')
plt.ylabel('Energy [kWh]')
plt.xlabel('Date')
plt.xticks(rotation=45)
plt.grid()
plt.legend()

plt.show()