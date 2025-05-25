import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)
print(CODE)

import os
import time
import json
import pickle
import shutil
import datetime
import requests
import numpy as np
import pandas as pd
from glob import glob
from time import sleep
from IPython.display import clear_output

## reading json data
json_data = json.load(open("../datalink.json", "r"))

pickle_path = json_data["picklePath"]
parameter_path = f'../parameters/{CODE}.csv'
output_csv_path = f'../backend_files/codes_output/{CODE}/'
parameter = pd.read_csv(parameter_path)
dte = pd.read_csv(json_data["dtePath"])
dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
dte = dte.set_index('Date')

if not os.path.isdir(output_csv_path) and output_csv_path != '':
    os.mkdir(output_csv_path)
else:
    shutil.rmtree(output_csv_path)
    os.mkdir(output_csv_path)

def Cal_slipage(open_price):
    return open_price * slipage_var

def get_gap(df):
    try:
        x = df.scrip.str[:-2].astype(int).unique()
        x.sort()
        
        mid = int(len(x) / 2)
        gap = x[mid+1] - x[mid]
        
        if gap > 100 and index == "FINNIFTY":
            return 100
        if gap > 50 and index == "MIDCPNIFTY":
            return 50
        if gap > 100 and index == "SENSEX":
            return 100
        if gap > 100 and index == "BANKEX":
            return 100
        
        return gap
    except :
        return 0

def straddle_strike(start_dt):
    while (start_dt < end_dt):
        try:
            # Future price at start
            future_price = future_data.loc[start_dt,'close']
            round_future_price = round(future_price/gap)*gap

            ce_scrip = str(round_future_price) + 'CE'
            pe_scrip = str(round_future_price) + 'PE'
            ce_price = options_data.loc[(start_dt, ce_scrip),'close']
            pe_price = options_data.loc[(start_dt, pe_scrip),'close']

            #### to Find out minimum difference strike for straddle
            
            # Synthetic future
            syn_future = ce_price - pe_price + round_future_price
            round_syn_future = round(syn_future/gap)*gap

            # Scrip lists
            ce_scrip_list = [str(round_syn_future)+'CE', str(round_syn_future+gap)+'CE',str(round_syn_future-gap)+'CE']
            pe_scrip_list = [str(round_syn_future)+'PE', str(round_syn_future+gap)+'PE',str(round_syn_future-gap)+'PE']

            difference = []
            for i in range(3):
                try:
                    ce_price = options_data.loc[(start_dt,ce_scrip_list[i]),'close']
                    pe_price = options_data.loc[(start_dt,pe_scrip_list[i]),'close']
                    difference.append(abs(ce_price-pe_price))
                except:
                    difference.append(-1)

            min_value = 999999
            for i in range(3):
                if ((min_value > difference[i]) & (difference[i] != -1)):
                    min_value = difference[i]
                    scrip_index = i
                    
            # Required scrip and their price
            ce_scrip = ce_scrip_list[scrip_index]
            pe_scrip = pe_scrip_list[scrip_index]
            ce_price = options_data.loc[(start_dt,ce_scrip),'close']
            pe_price = options_data.loc[(start_dt,pe_scrip),'close']

            return ce_scrip, pe_scrip, start_dt, ce_price, pe_price, future_price
        except Exception as e:
            start_dt += datetime.timedelta(minutes = 1)

    return None, None, None, None, None, None

def strangle_strike(start_dt):
    while start_dt < end_dt:
        try:
            future_price = future_data.loc[start_dt,'close']
            target = (int(future_price/step) * step) / 100 * options_multiplier
            
            current_od = options[options['date_time'] >= start_dt]
            target_od = current_od[current_od['close'] > target].sort_values(by = ['date_time', 'close'])  
            
            for i in range(len(target_od)):
                if target_od['scrip'].iloc[i][-2:] == 'CE':
                    ce_scrip = target_od.iloc[i]['scrip']
                    break
            
            for i in range(len(target_od)):
                if target_od['scrip'].iloc[i][-2:] == 'PE':
                    pe_scrip = target_od.iloc[i]['scrip']
                    break

            ce_scrip_list = [ce_scrip, str(int(ce_scrip[:-2])-gap)+'CE', str(int(ce_scrip[:-2])+gap)+'CE']
            pe_scrip_list = [pe_scrip, str(int(pe_scrip[:-2])-gap)+'PE', str(int(pe_scrip[:-2])+gap)+'PE']
                    
            call_list_prices = []
            put_list_prices = []

            for z in range(0,3):
                try:
                    call_list_prices.append(options_data.loc[(start_dt, ce_scrip_list[z]), 'close'])
                except:
                    call_list_prices.append(0)
                try:
                    put_list_prices.append(options_data.loc[(start_dt, pe_scrip_list[z]), 'close'])
                except:
                    put_list_prices.append(0)
            
            call = call_list_prices[0]
            put = put_list_prices[0]
            target_2 = target*2
            min_diff = 999999
            diff = abs(put-call)
            if (put+call >= target_2) & (min_diff > diff):
                min_diff = diff
                required_call, required_put = call, put            

            for i in range(1,3):
                if (min_diff > abs(put_list_prices[i] - call)) & (put_list_prices[i]+call >= target_2):
                    min_diff = abs(put_list_prices[i] - call)
                    required_call, required_put = call, put_list_prices[i]
                if (min_diff > abs(call_list_prices[i] - put)) & (call_list_prices[i]+put >= target_2):
                    min_diff = abs(call_list_prices[i] - put)
                    required_call, required_put = call_list_prices[i], put

            ce_scrip = ce_scrip_list[call_list_prices.index(required_call)]
            pe_scrip = pe_scrip_list[put_list_prices.index(required_put)]
            
            ce_entry = options_data.loc[(start_dt, ce_scrip), 'close']
            pe_entry = options_data.loc[(start_dt, pe_scrip), 'close']
            
            return ce_scrip, pe_scrip, start_dt, ce_entry, pe_entry, future_price
        except :
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None

for row in range(len(parameter)):
    if parameter['run_sut'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
            day = parameter.loc[row,'day']
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            start_time = pd.to_datetime(parameter.loc[row,'start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', '')[0:5], format="%H:%M").time()
            straddle_sl = parameter.loc[row,'strangle_sl']
            target = parameter.loc[row,'target']
            slipage_var = parameter.loc[row, 'slipage']
            slipage_var /= 100
            options_multiplier = parameter.loc[row,'strangle_om']

            if options_multiplier <= 0:
                strike_selection = straddle_strike
            else:
                strike_selection = strangle_strike

            print('Running Row :', row , index + ' SUT Strangle ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(straddle_sl) + ' ' + str(target) + ' OM-' + str(options_multiplier)) 
            log = pd.DataFrame(columns =('Date/Day/Expiry.Day/Time/Future/Strike/CE Price/PE Price/Premium/SL.Time/Target.Time/Total PNL').split('/') )

            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                gap = 100
                step = 5000
            if index == 'NIFTY':
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                gap = 50
                step = 1000
            if index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                gap = None
                step = 1000
            if index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                gap = None
                step = 1000
            if index == 'BANKEX':
                future_folder_path = 'BX Future/'
                option_folder_path = 'BX Options/'
                future_file_path = '_bankex_future.pkl'
                option_file_path = '_bankex.pkl'
                gap = None
                step = 5000
            if index == 'SENSEX':
                future_folder_path = 'SX Future/'
                option_folder_path = 'SX Options/'
                future_file_path = '_sensex_future.pkl'
                option_file_path = '_sensex.pkl'
                gap = None
                step = 5000

            while from_date <= to_date:
                try:
                    future_data = pd.read_pickle(''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))).set_index(['date_time'])
                    options = pd.read_pickle(''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path)))
                    options_data = options.set_index(['date_time', 'scrip'])
                except:
                    from_date += datetime.timedelta(days=1)
                    continue

                if index in ['FINNIFTY', 'MIDCPNIFTY','SENSEX', 'BANKEX']:
                    gap = get_gap(options)


                exp_day = 'TRUE' if options_data.dte.iloc[0] == 0 else 'FALSE'

                if day != dte.loc[str(from_date.date()), index]:
                    from_date += datetime.timedelta(days=1)
                    continue

                start_dt = datetime.datetime.combine(from_date, start_time)
                end_dt = datetime.datetime.combine(from_date, end_time)

                options = options[options['date_time'] <= end_dt]

                ce_scrip, pe_scrip, start_dt, ce_price, pe_price, future_price = strike_selection(start_dt)

                if ce_scrip == None:
                    from_date += datetime.timedelta(days=1)
                    continue

                straddle_open = ce_price + pe_price
                straddle_slipage = Cal_slipage(straddle_open) 
                straddle_entry_time = start_dt

                # straddle sl check
                start_dt += datetime.timedelta(minutes=1)

                ce_data = options.loc[(options['scrip'] == ce_scrip) & (options['date_time'] >= start_dt), :]
                pe_data = options.loc[(options['scrip'] == pe_scrip) & (options['date_time'] >= start_dt), :]

                ce_data = ce_data[ce_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
                pe_data = pe_data[pe_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)

                ce_data = ce_data.sort_values(by=['date_time'])
                pe_data = pe_data.sort_values(by=['date_time'])
                
                if ce_data.empty:
                    from_date += datetime.timedelta(days=1)
                    continue

                straddle_exit = ce_data.close.iloc[-1] + pe_data.close.iloc[-1]
                
                l3 = list(ce_data.close + pe_data.close)
                
                # sl calculation
                straddle_sl_time, sl_hit,sl_index = '',False,''
                straddle_sl_price = straddle_open * (1 - (straddle_sl/100))
                # if sl not hit i.e hit value is null throw error
                try:
                    sl_hit_value = [ele for ele in l3 if ele <= straddle_sl_price][0]
                    sl_hit = True
                    sl_index = l3.index(sl_hit_value)
                    straddle_sl_time = ce_data['date_time'].iloc[sl_index]
                except:
                    pass

                # target calulation
                target_hit_time, target_hit, target_index = '', False, ''
                target_price = straddle_open * (1 + (target / 100))
                try:
                    target_hit_value = [ele for ele in l3 if ele >= target_price][0]
                    target_hit = True
                    target_index = l3.index(target_hit_value)
                    target_hit_time = ce_data['date_time'].iloc[target_index]
                except:
                    pass
                
                if sl_hit and target_hit and target_hit_time < straddle_sl_time:
                    straddle_pl = target_hit_value - straddle_open 
                elif sl_hit and target_hit and straddle_sl_time < target_hit_time:
                    straddle_pl = sl_hit_value - straddle_open
                elif sl_hit and not target_hit:
                    straddle_pl = sl_hit_value - straddle_open
                elif not sl_hit and target_hit:
                    straddle_pl = target_hit_value - straddle_open 
                else:
                    straddle_pl = straddle_exit - straddle_open
                    
                straddle_pl -= straddle_slipage
                pl = straddle_pl

                print(from_date)
                log.loc[len(log.index)] = [str(from_date)[0:10], from_date.day_name(), exp_day, straddle_entry_time.time(), future_price , (ce_scrip, pe_scrip) ,ce_price, pe_price,straddle_open, straddle_sl_time, target_hit_time, pl]
                from_date += datetime.timedelta(days=1)

            log.to_csv(output_csv_path + index + ' SUT Strangle ' + str(day) + ' ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(straddle_sl) + ' ' + str(target)  + ' OM-' + str(options_multiplier) +'.CSV', index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            print(sys.exc_info()[-1].tb_lineno,type(e).__name__,asfd)
            msg = 'Error in row ' + str(row) + ": \n" + str(e) + "\n" + "Parameter : \n" + index + ' SUT Strangle ' + str(start_time).replace(':','')[:-2] + ' ' + str(end_time).replace(':','')[:-2] + ' ' + str(straddle_sl) + ' ' + str(target)  + ' OM-' + str(options_multiplier) 
            print(msg)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
            from_date += datetime.timedelta(days=1)

print('END')

