import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import os
import json
import pyotp
import datetime
import requests
import pandas as pd
from glob import glob
from tqdm import tqdm

import warnings
warnings.filterwarnings("ignore")

sort_master_col = lambda cols: sorted(sorted(cols, key=lambda x : 0 if 'SELL' in x else 1), key=lambda x: x.split()[0])

fun_cache = {}
def cell_name(row=None, col=None):
    tcol = col
    
    if col in fun_cache:
        col_name = fun_cache[col]
    else:
        col_name = ''
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            col_name = chr(65 + remainder) + col_name
        fun_cache[tcol] = col_name

    if row is None:
        return col_name
    else:
        return col_name, row+1

json_data = json.load(open("datalink.json", "r"))

spots_tokens = { "BANKNIFTY":260105, "NIFTY":256265, "FINNIFTY":257801, "MIDCPNIFTY":288009, "SENSEX":265, "BANKEX":274441, "INDIA VIX":264969}

indices = eval(json_data['indices'])
iCount = len(indices)
prefix_from_index = eval(json_data['prefix_from_index'])
index_from_prefix = eval(json_data['index_from_prefix'])

print("Reading Master File ...")

master_df = pd.read_excel("Combine Master File.xlsx")
master_df = master_df[list(master_df.columns)[:iCount+2] + sort_master_col(list(master_df.columns)[iCount+2:])]
master_df['Date'] = pd.to_datetime(master_df['Date'], dayfirst=False).dt.date

### creating qty df
arrays = [ [5]*iCount + [4]*iCount + [3]*iCount + [2]*iCount + [1]*iCount, indices * 5]
index_dte_col = pd.MultiIndex.from_arrays(arrays, names=('DTE', 'Index'))

master_columns = list(master_df.columns)
all_strategies = master_columns[iCount+2:]

print("Creating Margin DF ...")
unique_strategy = sorted(set([" ".join(s.split()[1:-1]) + " " + suffix for s in all_strategies for suffix in ["A", "B"]]))
unique_strategy = sorted(unique_strategy, key=lambda x : 0 if 'SELL' in x else 1)

margin_df = pd.DataFrame(index=['Margin Allocation', 'Strategies', 'Per Strategy', 'Total Margin Used', ''] + unique_strategy, columns=index_dte_col)
margin_df.loc['Total Margin Used', :] = [f"=SUM(${cell_name(col=2+i)}$9:${cell_name(col=2+i)}${9+len(unique_strategy)-1})" for i in range(len(margin_df.columns))]

cols = margin_df.columns.get_loc((5, indices[0]))+2, margin_df.columns.get_loc((1, indices[-1]))+2
row = margin_df.index.get_loc('Total Margin Used') + 3
c1, r1 = cell_name(row, cols[0])
c2, r2 = cell_name(row, cols[1])
c3, r3 = cell_name(row, cols[1]+1)
max_margin_df = pd.DataFrame([f'=MAX({c1}{r1}:{c2}{r2})'], columns=['Max Margin'])
max_margin_path = f"{c3}{r3}"

# grouping strategies
print('Grouping Strategies ...')
parameter_files = [f"parameters/{param}.csv" for param in json_data["strategyOrder"]]

strategies_with_dte = {}
for parameter_path in parameter_files:
    param_name = os.path.basename(parameter_path).replace(".csv", "")

    parameter = pd.read_csv(parameter_path)
    parameter = parameter[parameter['index'].isin(indices)].reset_index(drop=True)

    output_files = []
    for index in indices:
        output_files += glob(f'backend_files/codes_output/{param_name}/{index} *.csv')

    strategies = parameter["index"] + " " + parameter["start_time"].str[:5].str.replace(":", "") + " " + parameter["day"].astype(str)
    strategies = strategies.unique()
    strategies.sort()
    
    for strategy in strategies:
        index, time, dte = strategy.split()
        fstrategy_name = f"{prefix_from_index[index]} {param_name} {{order}} {time}"

        for o_file in output_files:
            file_name = o_file.split("\\")[-1]
            if file_name.startswith(index) and time in file_name:
                strategy_df = pd.read_csv(o_file)
                break

        strategy_df = strategy_df.rename(columns={'Total PNL':'Total SPNL'})

        if 'Total SPNL' in strategy_df.columns and 'Total BPNL' in strategy_df.columns:
            strategy_name = [fstrategy_name.format(order='SELL'), fstrategy_name.format(order='BUY')]

        elif 'Total SPNL' in strategy_df.columns:
            strategy_name = [fstrategy_name.format(order='SELL')]

        elif 'Total BPNL' in strategy_df.columns:
            strategy_name = [fstrategy_name.format(order='BUY')]

        strategies_with_dte[int(float(dte))] = strategies_with_dte.get(int(float(dte)), []) + strategy_name

# Count no of each strategy
partion_nos = {}
for dte in strategies_with_dte.keys():
    partion_nos[dte] = {}
    temp1 = sorted(set([" ".join(s.split()[1:]) for s in strategies_with_dte[dte]]))
    temp2 = [" ".join(s.split()[:-1]) for s in temp1]
    partion_nos[dte] = {stg:max(int(temp2.count(stg)/2), 1) for stg in temp2}

# grouping strategies in A and B
grouping_stg = {}
for dte in strategies_with_dte.keys():
    grouping_stg[dte] = {}
    temp1 = sorted(set([" ".join(s.split()[1:]) for s in strategies_with_dte[dte]]))

    for stg in temp1:
        s = " ".join(stg.split()[:-1])
        slist = [st for st in temp1 if " ".join(st.split()[:-1]) == s]
        s_index = slist.index(stg)+1
        group = "A" if s_index <= partion_nos[dte][s] else "B"
        grouping_stg[dte][stg] =  s + " " + group

print("Login Zerodha..")
session = requests.session()
login_url = "https://kite.zerodha.com/api"
root_url = "https://kite.zerodha.com/oms"
market_historical_url = "/instruments/historical/{instrument_token}/{interval}"

# login
data = {"user_id": "ZGA974", "password": "Delhi@12345"}
response = session.post(f"{login_url}/login", data=data)
data = {
    "request_id": response.json()['data']['request_id'],
    "twofa_value": pyotp.TOTP("UPNOV7BTHAFFLKRUZUBEZKISDCVSALNY").now(),
    "user_id": response.json()['data']['user_id']
}

response = session.post(f"{login_url}/twofa", data=data)
enctoken = response.cookies.get('enctoken')
header = {"Authorization": f"enctoken {enctoken}"}
print("Login Zerodha Done :)")

print("Creating MTM Sheet...")
hedge_cost = json_data['hedgeCost%']/100

mtm_df = master_df[['Date', 'Day']].copy()

mtm_df[indices + ['Total']] = 0
mtm_df[[f"{index}-DD" for index in indices] + ['Total-DD', 'DD-Days']] = 0
mtm_df[[f"{index}-Hedge" for index in indices] + ['Total-Hedge']] = 0
mtm_df[[f"{index}-Hedge-DD" for index in indices] + ['Total-Hedge-DD', 'Hedge-DD-Days']] = 0

mtm_df[['Loss-Days', 'Loss-Amount', 'Profit-Days', 'Profit-Amount', 'Loss-Greater-1%', 'Profit-Greater-1%']] = 0
mtm_df[['Hedge-Loss-Days', 'Hedge-Loss-Amount', 'Hedge-Profit-Days', 'Hedge-Profit-Amount', 'Hedge-Loss-Greater-1%', 'Hedge-Profit-Greater-1%']] = 0

print("Fetching India Vix Data...")

date_string_format = "%Y-%m-%d %H:%M:%S"
from_date_string = master_df['Date'].iloc[0].strftime(date_string_format)
to_date_string = master_df['Date'].iloc[-1].strftime(date_string_format)
params = {"from": from_date_string, "to": to_date_string, "oi": 0}

spot_token = spots_tokens['INDIA VIX']
URL = f"{root_url}{market_historical_url.format(instrument_token=spot_token, interval='day')}"
response = session.get(URL, params=params, headers=header).json()
df = pd.DataFrame(response['data']['candles'])
df[0] = pd.to_datetime(df[0].str.split("T", expand=True)[0])
df.set_index(0, inplace=True)
mtm_df.loc[:, 'India Vix'] = df.loc[mtm_df.Date, 4].values

index_sell_ranges = {}
for index in indices:
    prefix = prefix_from_index[index]
    columns = [c for c in master_columns if c.startswith(prefix) and not c.endswith("DTE") and 'BUY' not in c]
    if columns:
        first, last = master_columns.index(columns[0]), master_columns.index(columns[-1])
        index_sell_ranges[index] = {"first":first+1, "last":last+1}

index_buy_ranges = {}
for index in indices:
    prefix = prefix_from_index[index]
    columns = [c for c in master_columns if c.startswith(prefix) and not c.endswith("DTE") and 'SELL' not in c]
    if columns:
        first, last = master_columns.index(columns[0]), master_columns.index(columns[-1])
        index_buy_ranges[index] = {"first":first+1, "last":last+1}

start_col = 3
for row in range(1, len(mtm_df.index)+1):
    for col in range(1, len(mtm_df.columns)+1):
        date = mtm_df['Date'].iloc[row-1]
        col_name = mtm_df.columns.to_list()[col-1]
        formula = ''

        # index wise MTM Sum
        if col_name in indices:

            if index_sell_ranges and index_buy_ranges:
                r1a, r1b = cell_name(row, index_sell_ranges[col_name]['first'])
                r2a, r2b = cell_name(row, index_sell_ranges[col_name]['last'])
                r3a, r3b = cell_name(row, index_buy_ranges[col_name]['first'])
                r4a, r4b = cell_name(row, index_buy_ranges[col_name]['last'])
                formula = f"=SUM(PL!{r1a}{r1b}:{r2a}{r2b}) + SUM(PL!{r3a}{r3b}:{r4a}{r4b})"

            elif index_sell_ranges:
                r1a, r1b = cell_name(row, index_sell_ranges[col_name]['first'])
                r2a, r2b = cell_name(row, index_sell_ranges[col_name]['last'])
                formula = f"=SUM(PL!{r1a}{r1b}:{r2a}{r2b})"
            elif index_buy_ranges:
                r3a, r3b = cell_name(row, index_buy_ranges[col_name]['first'])
                r4a, r4b = cell_name(row, index_buy_ranges[col_name]['last'])
                formula = f"=SUM(PL!{r3a}{r3b}:{r4a}{r4b})"

            mtm_df.iloc[row-1, col-1] = formula
                
        # Total MTM
        elif col_name in ['Total']:
            formula = f"=SUM(C{row+1}:{chr(ord('C') + iCount - 1)}{row+1})"
            mtm_df.iloc[row-1, col-1] = formula
            
        ## Hedge calculate index wise
        elif col_name in [f"{index}-Hedge" for index in indices]:
            index_col = col_name.split('-')[0]
            c, r = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)
            
            if index_sell_ranges:
                r1a, r1b = cell_name(row, index_sell_ranges[index_col]['first'])
                r2a, r2b = cell_name(row, index_sell_ranges[index_col]['last'])
                formula = f"={c}{r}-((ABS(SUM(PL!{r1a}{r1b}:{r2a}{r2b})))*{hedge_cost})"
            else:
                formula = f"={c}{r}"

            mtm_df.iloc[row-1, col-1] = formula
            
        # -DD Calculate
        elif col_name in [f"{index}-DD" for index in indices] + [f"{index}-Hedge-DD" for index in indices] + ['Total-DD', 'Total-Hedge-DD']:
            index_col = col_name.replace('-DD', '')
            c, r = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)
            c2, r2 = cell_name(row-1, mtm_df.columns.get_loc(col_name) + 1)
            formula = f"=IF({c}{r} < 0, {c}{r}, 0)" if row == 1 else f"=IF({c}{r} + {c2}{r2} < 0, {c}{r} + {c2}{r2}, 0)"
            mtm_df.iloc[row-1, col-1] = formula

        # DD-Days
        elif col_name in ['DD-Days', 'Hedge-DD-Days']:
            index_col = 'Total-' + col_name.replace('-Days', '')
            c, r = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)
            c2, r2 = cell_name(row-1, mtm_df.columns.get_loc(col_name) + 1)
            formula = f"=IF({c}{r} < 0, 1, 0)" if row == 1 else f"=IF({c}{r} < 0, 1 + {c2}{r2}, 0)"
            mtm_df.iloc[row-1, col-1] = formula
            
        ## Total Hedge
        elif col_name in ['Total-Hedge']:
            c, r = cell_name(row, mtm_df.columns.get_loc(col_name) + 1)
            t = [f"{chr(ord(c) - idx-1)}{r}" for idx, index in enumerate(indices)]
            format_string = "=" + " + ".join(["{" + str(i) + "}" for i in range(len(t))][::-1])
            formula = format_string.format(*t)
            mtm_df.iloc[row-1, col-1] = formula
            
        elif col_name in ['Loss-Days', 'Hedge-Loss-Days', 'Profit-Days', 'Hedge-Profit-Days']:
            index_col = 'Total-Hedge' if 'Hedge' in col_name else 'Total'
            c, r = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)
            sign = '<' if 'Loss' in col_name else '>'
            formula = f"=IF({c}{r}{sign}0,1,0)"
            mtm_df.iloc[row-1, col-1] = formula
            
        elif col_name in ['Loss-Amount', 'Hedge-Loss-Amount', 'Profit-Amount', 'Hedge-Profit-Amount']:
            index_col = 'Total-Hedge' if 'Hedge' in col_name else 'Total'
            c1, r1 = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)
            index_col2 = col_name.replace('-Amount', '-Days')
            c2, r2 = cell_name(row, mtm_df.columns.get_loc(index_col2) + 1)
            formula = f"=IF({c2}{r2}=1,{c1}{r1},0)"
            mtm_df.iloc[row-1, col-1] = formula

        elif col_name in ['Loss-Greater-1%', 'Hedge-Loss-Greater-1%', 'Profit-Greater-1%', 'Hedge-Profit-Greater-1%']:
            
            index_col = col_name.replace('-Greater-1%', '-Amount')
            c1, r1 = cell_name(row, mtm_df.columns.get_loc(index_col) + 1)

            sign = '<-' if 'Loss' in col_name else '>'
            formula = f"=IF({c1}{r1}{sign}Quantity!{max_margin_path}/100,1,0)"
            mtm_df.iloc[row-1, col-1] = formula

last_row_no = mtm_df.shape[0] + 1
total_row = []
for idx, col in enumerate(mtm_df.columns):
    
    if col in ["Date"]: 
        total_row.append("Total")
        
    if col in ["Day", "India Vix"]:
        total_row.append("")
        
    if col in indices + ['Total'] + [f"{index}-Hedge" for index in indices] + ['Total-Hedge']: 
        total_row.append(f"=SUM({cell_name(col=idx+1)}2:{cell_name(col=idx+1)}{last_row_no})")
        
    if col in ['Loss-Days', 'Loss-Amount', 'Profit-Days', 'Profit-Amount', 'Loss-Greater-1%', 'Profit-Greater-1%']: 
        total_row.append(f"=SUM({cell_name(col=idx+1)}2:{cell_name(col=idx+1)}{last_row_no})")
        
    if col in ['Hedge-Loss-Days', 'Hedge-Loss-Amount', 'Hedge-Profit-Days', 'Hedge-Profit-Amount', 'Hedge-Loss-Greater-1%', 'Hedge-Profit-Greater-1%']: 
        total_row.append(f"=SUM({cell_name(col=idx+1)}2:{cell_name(col=idx+1)}{last_row_no})")
    
    if col.endswith("-DD"):
        total_row.append(f"=MIN({cell_name(col=idx+1)}2:{cell_name(col=idx+1)}{last_row_no})")
    
    if col.endswith("DD-Days"):
        total_row.append(f"=MAX({cell_name(col=idx+1)}2:{cell_name(col=idx+1)}{last_row_no})")

months_dict = {}
for index in indices:
    prefix = prefix_from_index[index]
    lst = list(master_df[f"{prefix} DTE"])
    fist_non_zero = next((i for i, x in enumerate(lst) if x != 0))
    last_non_zero = len(lst) - next((i for i, x in enumerate(reversed(lst)) if x != 0)) - 1
    first_date = master_df['Date'].iloc[fist_non_zero]
    last_date = master_df['Date'].iloc[last_non_zero]
    no_of_days = (last_date - first_date).days
    months = round(no_of_days/365*12,2)
    months_dict[index] = months
    
month_row = []
for idx, col in enumerate(mtm_df.columns):
    if col == "Date": 
        month_row.append("Months")
    elif col in indices + [f"{index}-Hedge" for index in indices]:
        month_row.append(months_dict[col.split("-")[0]])
    elif col in ['Loss-Amount', 'Hedge-Loss-Amount', 'Profit-Amount', 'Hedge-Profit-Amount']:
        month_row.append(f"={cell_name(col=idx+1)}{last_row_no+1}/{cell_name(col=idx)}{last_row_no+1}")
    else:
        month_row.append('')

per_month_row = []
for idx, col in enumerate(mtm_df.columns):
    if col == "Date": 
        per_month_row.append("Per Month")
    elif col in indices + [f"{index}-Hedge" for index in indices]:
        per_month_row.append(f"={cell_name(col=idx+1)}{last_row_no+1}/{cell_name(col=idx+1)}{last_row_no+2}")
    elif col in ["Total", "Total-Hedge"]:
        per_month_row.append("=" + "+".join([f"{cell_name(col=idx-iCount+1+i)}{last_row_no+3}" for i in range(iCount)]))    
    elif col in ['Profit-Amount', 'Hedge-Profit-Amount']:
        per_month_row.append(f"={cell_name(col=idx+1)}{last_row_no+2}/{cell_name(col=idx-1)}{last_row_no+2}*-1")
    else:
        per_month_row.append("")

mtm_df.loc[len(mtm_df)] = total_row
mtm_df.loc[len(mtm_df)] = month_row
mtm_df.loc[len(mtm_df)] = per_month_row

print("Creating Spot data...")

spot_data = master_df[['Date', 'Day']].copy()
spot_data.set_index("Date", inplace=True)

for index in indices:
    spot_token = spots_tokens[index]
    URL = f"{root_url}{market_historical_url.format(instrument_token=spot_token, interval='day')}"
    response = session.get(URL, params=params, headers=header).json()
    df = pd.DataFrame(response['data']['candles'])
    df[0] = pd.to_datetime(df[0].str.split("T", expand=True)[0])
    df.set_index(0, inplace=True)
    spot_data.loc[:, index] = df.loc[spot_data.index, 4]
print("Creating Spot data Done :)")

### average data
print("Creating avg data...")
arrays = [ [5]*iCount + [4]*iCount + [3]*iCount + [2]*iCount + [1]*iCount + ['Total']*iCount, indices * 6]
aindex_dte_col = pd.MultiIndex.from_arrays(arrays, names=('DTE', 'Index'))
avg_data = pd.DataFrame(columns=aindex_dte_col, index=unique_strategy)
avg_data.index.name = 'Strategies'

for row in range(1, len(avg_data.index)+1):
    for col in range(1, len(avg_data.columns)-1):
        strategy = avg_data.index[row-1]
        dte, index = avg_data.columns.to_list()[col-1]
        prefix = prefix_from_index[index]
        current_strategies = [f"{prefix} {key}" for key, value in grouping_stg.get(dte, {}).items() if value == strategy]
        ssum = master_df.loc[master_df[f"{prefix} DTE"] == dte, current_strategies].sum().sum()
        avg = round(ssum/len(current_strategies), 2)
        avg_data.iloc[row-1, col-1] = avg
        
for index in indices:
    avg_data[('Total', index)] = avg_data[[i for i in avg_data.columns if i[-1] == index and str(i[0]).isdigit()]].sum(axis=1)
    
print("Creating avg data Done :)")

print("Creating MarginPerDay data...")
margin_perday_df = pd.DataFrame(index=['Nv Percent', 'Lot Size', ''] + master_df['Date'].to_list(), columns=index_dte_col)
margin_perday_df.loc['Nv Percent', :] = 12
margin_perday_df.loc['Lot Size', :] = 1

for row in range(4, len(margin_perday_df.index)+1):
    for col in range(1, len(margin_perday_df.columns)+1):
        date = margin_perday_df.index[row-1]
        index = margin_df.columns[col-1][1]
        r2 = spot_data.index.get_loc(date) + 2
        c2 = spot_data.columns.get_loc(index) + 2
        formula = f"=SpotData!{cell_name(col=c2)}{r2}*MarginPerDay!{cell_name(col=col+1)}5*MarginPerDay!{cell_name(col=col+1)}4/100"
        margin_perday_df.iat[row-1, col-1] = formula
            
print("Creating MarginPerDay data Done :)")

if json_data['manualQntyMaster'].lower() == str(True).lower():

    print("Creating Quantity DF ...")
    qty_index = sorted(set([" ".join(s.split()[1:]) for s in all_strategies]))
    qty_df = pd.DataFrame(index=qty_index, columns=index_dte_col)

    for row in range(1, len(qty_df.index)+1):
        for col in range(1, len(qty_df.columns)+1):

            formula = ''
            strategy = qty_df.index[row-1]
            dte, index = qty_df.columns[col-1]
            if grouping_stg.get(dte, {}).get(strategy, None) is None: continue

            c1 = cell_name(col=col+1)
            r1 = margin_df.index.get_loc(grouping_stg[dte][strategy]) + 4
            partion_no = partion_nos[dte][grouping_stg[dte][strategy][:-2]]
            margin_per_lot = (json_data['margins']['expiry'] if dte == 1 else json_data['margins']['nonExpiry'])[index]
            lot_size = json_data['lotSize'][index]
            formula = f"={c1}{r1}/{margin_per_lot}/{partion_no}*{lot_size}"
            qty_df.iat[row-1, col-1] = formula
        
    print("Creating PL Sheet...")
    pl_formula_df = master_df.copy()
    for row in tqdm(range(1, len(pl_formula_df.index)+1)):
        for col in range(iCount+3, len(pl_formula_df.columns)+1):

            date = pl_formula_df['Date'].iloc[row-1]
            strategy = master_columns[col-1]
            prefix = strategy.split()[0]
            index = index_from_prefix[prefix]
            dte = pl_formula_df.loc[row-1, f"{prefix} DTE"]
            dte = 5 if dte > 5 else dte
            if dte == 0: continue
            if grouping_stg.get(dte, {}).get(strategy.replace(f"{prefix} ", ""), None) is None: continue

            qcol = qty_df.columns.get_loc((dte, index))
            qrow = qty_df.index.get_loc(strategy.replace(f"{prefix} ", ""))

            cell, number = cell_name(row, col)
            qcell, qnumber = cell_name(qrow + margin_df.shape[0] + 7, qcol+2)

            pl_formula_df.iat[row-1, col-1] = f"=Master!${cell}${number}*Quantity!${qcell}${qnumber}"
    print("PL Sheet Created :)")
            
else:
    print("Creating StgQuantity & PL Sheet...")
    strategy_quantity_df = master_df.copy()
    pl_formula_df = master_df.copy()
    for row in tqdm(range(1, len(strategy_quantity_df.index)+1)):
        for col in range(iCount+3, len(strategy_quantity_df.columns)+1):

            date = strategy_quantity_df['Date'].iloc[row-1]
            strategy = master_columns[col-1]
            prefix = strategy.split()[0]
            index = index_from_prefix[prefix]
            dte = strategy_quantity_df.loc[row-1, f"{prefix} DTE"]
            dte = 5 if dte > 5 else dte
            if dte == 0: continue
            if grouping_stg.get(dte, {}).get(strategy.replace(f"{prefix} ", ""), None) is None: continue

            mrow = margin_df.index.get_loc(grouping_stg[dte][strategy.replace(f"{prefix} ", "")]) + 3
            mcol = margin_df.columns.get_loc((dte, index)) + 2
            c1, r1 = cell_name(row=mrow, col=mcol)

            mrow = margin_perday_df.index.get_loc(date) + 3
            mcol = margin_perday_df.columns.get_loc((dte, index)) + 2
            c2, r2 = cell_name(row=mrow, col=mcol)

            strategy_quantity_df.iat[row-1, col-1] = f"=Quantity!{c1}{r1}/MarginPerDay!{c2}{r2}/{partion_nos[dte][' '.join(strategy.split()[1:-1])]}"

            cell, number = cell_name(row, col)
            pl_formula_df.iat[row-1, col-1] = f"=Master!${cell}${number}*StgQuantity!${cell}${number}"
    print("StgQuantity & PL Sheet Created :)")

print("Saving Master File...")
master_df.set_index(list(master_df.columns[:iCount+2]), inplace=True)

if not json_data['manualQntyMaster'].lower() == str(True).lower():
    strategy_quantity_df.set_index(list(strategy_quantity_df.columns[:iCount+2]), inplace=True)

pl_formula_df.set_index(list(pl_formula_df.columns[:iCount+2]), inplace=True)
mtm_df.set_index(list(mtm_df.columns[:2]), inplace=True)

writer = pd.ExcelWriter("Master File.xlsx", engine="xlsxwriter")
master_df.to_excel(writer, sheet_name="Master")
margin_df.to_excel(writer, sheet_name="Quantity")
max_margin_df.to_excel(writer, sheet_name="Quantity", startrow=int(max_margin_path[1])-2, startcol=ord(max_margin_path[0])-65, index=False)
margin_perday_df.to_excel(writer, sheet_name="MarginPerDay")

if json_data['manualQntyMaster'].lower() == str(True).lower():
    qty_df.to_excel(writer, sheet_name="Quantity", startrow=margin_df.shape[0]+4)
else:
    strategy_quantity_df.to_excel(writer, sheet_name="StgQuantity")

pl_formula_df.to_excel(writer, sheet_name="PL")
spot_data.to_excel(writer, sheet_name="SpotData")
mtm_df.to_excel(writer, sheet_name="MTM")
avg_data.to_excel(writer, sheet_name="AvgPoints")

# Setting format of all sheets
for sheet in writer.sheets.keys():
    worksheet = writer.sheets[sheet]
    default_format = writer.book.add_format({"font_name": "Times New Roman", "font_size":10, 'num_format': '_ * #,##0_ ;_ * -#,##0_ ;_ * "-"_ ;_ @_ '})
    bad_format = writer.book.add_format({'bg_color' : '#ffc7ce', 'font_color' : '#960006'})
    good_format = writer.book.add_format({'bg_color' : '#c6efce', 'font_color' : '#006100'})
    
    if sheet in ["Master", "PL"]:
        c1, r1 = cell_name(row=1, col=iCount+3)
        c2, r2 = cell_name(row=len(master_df), col=iCount + 2 + len(master_df.columns))
        format_range = f"{c1}{r1}:{c2}{r2}"
        worksheet.conditional_format(format_range, {'type':'cell', 'criteria':'<', 'value': 0, 'format':bad_format})

    if sheet in ["MTM"]:
        worksheet.conditional_format('C2:ZZ1000', {'type':'cell', 'criteria':'<', 'value': 0, 'format':bad_format})

    _ = [worksheet.set_row(i, cell_format=default_format) for i in range(2000)]
    
writer.close()

print("ALL Done :)")
input("Press Enter to Exit :)")