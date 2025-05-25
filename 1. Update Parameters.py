import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import os
import json
import shutil
import pandas as pd
from glob import glob
from time import sleep

## reading json data
json_data = json.load(open("datalink.json", "r"))

indices = eval(json_data['indices'])

## strategy in which we work
needed_strategies = list(json_data['strategyOrder'])

## reading all parameter files
all_parameters = [os.path.normpath(p) for p in (glob('parameters/*.csv') + glob('parameters/notUse/*.csv'))]

## reading all bt codes
all_codes = [os.path.normpath(c) for c in (glob('codes/*.py') + glob('codes/notUse/*.py'))]

## moving unuse parameter to unuse folder
for parameter in all_parameters:
    param_name = os.path.basename(parameter).replace(".csv", "")  
    
    if param_name in needed_strategies:
        shutil.move(parameter, f"parameters/{os.path.basename(parameter)}")
    else:
        shutil.move(parameter, f"parameters/notUse/{os.path.basename(parameter)}")
    
## moving unuse code to unuse folder
for code in all_codes:
    code_name = os.path.basename(code).replace(".py", "")
    
    # check needed
    if code_name in needed_strategies:
        shutil.move(code, f"codes/{os.path.basename(code)}")
    else:
        shutil.move(code, f"codes/notUse/{os.path.basename(code)}")
        
#------------------------------------------------------------------------------------------
needed_parameters = [os.path.normpath(p) for p in glob('parameters/*.csv')]

for parameter_path in needed_parameters:
    param_name = os.path.basename(parameter_path).replace(".csv", "")
    print(param_name)
    param_df = pd.read_csv(parameter_path)
    param_df = param_df[param_df['index'] != '']
    run_col = [c for c in param_df.columns if 'run' in c.lower()][0]
    param_df[run_col] = False
    
    for index in indices:
        param_df.loc[param_df["index"].isin([index]), "from_date"] = json_data["startDate"][index]
        param_df.loc[param_df["index"].isin([index]), run_col] = True
        
    param_df['to_date'] = json_data['endDate']
    param_df.to_csv(parameter_path, index=False)
    
print("ALL Done :)")
input("Press Enter to Exit :)")
