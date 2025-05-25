import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import json
from glob import glob

## reading json data
json_data = json.load(open("datalink.json", "r"))

codes = [c.split('\\')[-1] for c in glob("codes/*.py")]
parameters = [p.split('\\')[-1][:-4] for p in glob("parameters/*.csv")]

for code in codes:
    print(code)
    
    if not code.replace(".py", "") in parameters:
        print(code)
        input(f"{code} Exception Code Parameter not available !!! \nPress Enter to ignore")
        print()
        
codes = [c.replace(".py", "") for c in codes if c.replace(".py", "") in parameters]
json_data['strategyOrder'] = codes

with open("datalink.json", "w") as f:
    json.dump(json_data, f, indent=4)
    
print("ALL Done :)")
input("Press Enter to Exit :)")