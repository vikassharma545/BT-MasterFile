import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import os
import sys
import json
import pandas as pd
from glob import glob
from tqdm import tqdm
## reading json data
json_data = json.load(open("datalink.json", "r"))

print("Checking Output Files ...")

indices = eval(json_data['indices'])
needed_strategies = list(json_data['strategyOrder'])

missing_file = False
for strategy in needed_strategies:

    parameter_file = pd.read_csv(f"parameters/{strategy}.csv")
    parameter_file = parameter_file[parameter_file['index'].isin(indices)].reset_index(drop=True)
    no_of_rows = len(parameter_file)

    no_of_output_files = 0
    for index in indices:
        no_of_output_files += len(glob(f'backend_files/codes_output/{strategy}/{index} *.csv'))

    if no_of_rows != no_of_output_files:
        print(strategy, "- No of Parameter file Rows and Output File Not Match !!!")
        missing_file = True

if missing_file:
    input("\nPress Enter to Exit !!!")
    sys.exit(0)

print("Checking Output Files Done :)")

print("\nCreating Master Files ...")

prefix_from_index = eval(json_data['prefix_from_index'])
parameter_files = [f"parameters/{param}.csv" for param in json_data["strategyOrder"]]

for parameter_path in tqdm(parameter_files):
    param_name = os.path.basename(parameter_path).replace(".csv", "")

    parameter = pd.read_csv(parameter_path)
    parameter = parameter[parameter['index'].isin(indices)].reset_index(drop=True)

    output_files = []
    for index in indices:
        output_files += glob(f'backend_files/codes_output/{param_name}/{index} *.csv')

    strategies = parameter["index"] + " " + parameter["start_time"].str[:5].str.replace(":", "")
    strategies = strategies.unique()
    strategies.sort()

    Master_data = pd.DataFrame()

    for strategy in strategies:
        index, time = strategy.split()
        fstrategy_name = f"{prefix_from_index[index]} {param_name} {{order}} {time}"

        strategy_data = []
        for o_file in output_files:
            file_name = o_file.split("\\")[-1]
            if file_name.startswith(index) and time in file_name:
                df = pd.read_csv(o_file)
                strategy_data.append(df)

        strategy_df = pd.concat(strategy_data)
        strategy_df.set_index(['Date'], inplace=True)
        strategy_df = strategy_df.rename(columns={'Total PNL':'Total SPNL'})
        
        if 'Total SPNL' in strategy_df.columns and 'Total BPNL' in strategy_df.columns:
            strategy_df = strategy_df[['Total SPNL', 'Total BPNL']]
            strategy_df.columns = [fstrategy_name.format(order='SELL'), fstrategy_name.format(order='BUY')]

        elif 'Total SPNL' in strategy_df.columns:
            strategy_df = strategy_df[['Total SPNL']]
            strategy_df.columns = [fstrategy_name.format(order='SELL')]

        elif 'Total BPNL' in strategy_df.columns:
            strategy_df = strategy_df[['Total BPNL']]
            strategy_df.columns = [fstrategy_name.format(order='BUY')]
            
        Master_data = pd.concat([Master_data, strategy_df.T])
    
    Master_data = Master_data.T
    Master_data = Master_data.reindex(sorted(Master_data.columns), axis=1)
    Master_data.sort_index(inplace=True)
    Master_data.to_excel(f"backend_files/codes_master_file/{param_name} Master File.xlsx")

print("\nCombine Master Files...")

master_files = [f"backend_files/codes_master_file/{param} Master File.xlsx" for param in json_data["strategyOrder"]]

combine_master = pd.DataFrame()
for master_file in master_files:
    df = pd.read_excel(master_file)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df.set_index("Date", inplace=True)
    combine_master = pd.concat([combine_master, df], axis=1)

sorted_col = sorted(sorted(combine_master.columns, key=lambda x : 0 if 'SELL' in x else 1), key=lambda x: x.split()[0])
combine_master = combine_master.reindex(sorted_col, axis=1)
combine_master.sort_index(inplace=True)

print("Adding DTE...")
dte = pd.read_csv(json_data['dtePath'])
dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
dte = dte.set_index("Date")
dte.fillna(0, inplace=True)

### creating master with dte
for index in reversed(indices):
    combine_master.insert(loc=0, column=f"{prefix_from_index[index]} DTE", value=list(dte.loc[combine_master.index, index]))

combine_master.insert(loc=0, column="Day", value=pd.to_datetime(combine_master.index.to_series()).dt.day_name().to_list())

print("Saving Combine Master File...")
combine_master.to_excel(f"Combine Master File.xlsx")
print("ALL Done :)")
input("Press Enter to Exit :)")