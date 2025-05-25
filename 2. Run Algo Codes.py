import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import os
import sys
import json
import subprocess
import pandas as pd
from glob import glob
from time import sleep
import pygetwindow as gw

### Check Files ###
print("Checking Codes and their parameters files...")

## reading json data
json_data = json.load(open("datalink.json", "r"))

## strategy in which we work
needed_strategies = list(json_data['strategyOrder'])

missing_codes = [s for s in needed_strategies if not os.path.exists(f"codes/{s}.py")]
missing_parameters = [s for s in needed_strategies if not os.path.exists(f"parameters/{s}.csv")]

if len(missing_codes) > 0:
    input(f"\n\nMissing Codes !!! Pls Check... \n{missing_codes} \nPress Enter to Exit")
    sys.exit(0)
    
if len(missing_parameters) > 0:
    input(f"\n\nMissing Parameters !!! Pls Check... \n{missing_parameters} \nPress Enter to Exit")
    sys.exit(0)
    
print("Checking Codes and parameters files Done :)")

### run algo codes
print("Start running algo Codes ...")

os.chdir(os.getcwd() + "\\codes")

python_path = [p for p in sys.path if p.endswith("\\Lib\\site-packages")][0].replace("\\Lib\\site-packages", "") + "\\python.exe"
python_path = python_path.replace("\\", "/")

codes = glob("*.py")

max_codes = 18
for idx, code in enumerate(codes):

    while True:
        if len([c for c in gw.getAllTitles() if c in needed_strategies]) < max_codes:
            
            #run code
            print(code)
            subprocess.run(["start", python_path, code], shell=True)
            break
        else:
            sleep(10)

    sleep(2)
    
print("ALL Done :)")
input("Press Enter to Exit :)")