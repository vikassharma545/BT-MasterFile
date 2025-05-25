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

def OHLC_SL(ftime, fdataframe, entry_f, sl_price_f, flag):
    fdata = fdataframe.copy()

    if flag:
        fdata = fdata[fdata.date_time >= ftime]
        try:
            entry_f = fdata.close.iloc[0]
            if sl_price_f == '':
                sl_price_f = entry_f * ut_sl_per
            fdata = fdata[1:]
        except:
            pass
    else:
        fdata = fdata[fdata.date_time > ftime]
        slipage = Cal_slipage(entry_f)
        entry_f = entry_f - slipage
    
    try:
        high_f = fdata.high.max()
        low_f = fdata.low.min()
        exit_f = fdata.close.iloc[-1]

        temp = fdata[fdata.high >= sl_price_f]

        try:
            sl_time = temp.date_time.iloc[0]
            sl_flag = True
            pnl = round(entry_f - sl_price_f, 2)
        except:
            sl_time = end_dt_1m
            sl_flag = False
            pnl = round(entry_f - exit_f, 2)

        if flag:
            return entry_f, sl_flag, sl_time, pnl
        else:
            return sl_flag, sl_time, pnl
    except:
        if flag:
            return '', '', '', 0
        else:
            return False, end_dt_1m, 0

def strangle_strike(start_dt):
    while start_dt < end_dt:
        try:
            future_price = future_data.loc[start_dt,'close']
            target = int(future_price / 100) * options_multiplier
            
            current_od = options[options['date_time'] >= start_dt]
            target_od = current_od[current_od['close'] > target * 0.625].sort_values(by = ['date_time', 'close'])  
            
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
            target_2 = target*2*0.625
            target_3 = target*3
            min_diff = 999999
            diff = abs(put-call)
            if (put+call >= target_2) & (min_diff > diff) & (call+put <= target_3):
                min_diff = diff
                required_call, required_put = call, put            

            for i in range(1,3):
                if (min_diff > abs(put_list_prices[i] - call)) & (put_list_prices[i]+call >= target_2) & (put_list_prices[i]+call <= target_3):
                    min_diff = abs(put_list_prices[i] - call)
                    required_call, required_put = call, put_list_prices[i]
                if (min_diff > abs(call_list_prices[i] - put)) & (call_list_prices[i]+put >= target_2) & (call_list_prices[i]+put <= target_3):
                    min_diff = abs(call_list_prices[i] - put)
                    required_call, required_put = call_list_prices[i], put

            ce_scrip = ce_scrip_list[call_list_prices.index(required_call)]
            pe_scrip = pe_scrip_list[put_list_prices.index(required_put)]
            
            ce_entry = options_data.loc[(start_dt, ce_scrip), 'close']
            pe_entry = options_data.loc[(start_dt, pe_scrip), 'close']
            
            return ce_scrip, pe_scrip, ce_entry, pe_entry, start_dt, future_price, target
        except :
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None, None

for row in range(len(parameter)):
    if parameter['run'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
            day = parameter.loc[row,'day']
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            start_time = pd.to_datetime(parameter.loc[row,'start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', '')[0:5], format="%H:%M").time()
            sl = parameter.loc[row,'sl']
            ut_sl = parameter.loc[row, 'ut_sl']
            options_multiplier = parameter.loc[row, 'options_multiplier']
            re_entries = parameter.loc[row, 're_entry']
            slipage_var = parameter.loc[row, 'slipage']
            slipage_var /= 100
            sl_per = ((100 + sl) / 100)
            ut_sl_per = ((100 + ut_sl) / 100)

            msg = f"{index} B120 IRE {day} {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} {sl} {ut_sl} {re_entries}"
            print(f"Running Row: {row} {msg}")

            cols = 'Date/Day/Future/Expiry.Day/Time/'
            for i in range(1, re_entries+2):
                cols += f'CE.Strike.{i}/CE.Open.{i}/CE.SL.Flag.{i}/CE.SL.Time.{i}/CE.PNL.{i}/PE.Strike.{i}/PE.Open.{i}/PE.SL.Flag.{i}/PE.SL.Time.{i}/PE.PNL.{i}/UT.Strike.{i}/UT.Open.{i}/UT.SL.Flag.{i}/UT.SL.Time.{i}/UT.PNL.{i}/BPL.{i}/TT Pl at SL {i}/UT PL at SL{i}/PNL {i}/'

            log = pd.DataFrame( columns = (cols+'Total PNL').split('/'))

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

                for i in range(0, re_entries + 1):
                    vars()['ce_scrip_' + str(i)] = ''
                    vars()['pe_scrip_' + str(i)] = ''
                    vars()['ut_scrip_' + str(i)] = ''
                    vars()['ce_entry_' + str(i)] = 0
                    vars()['pe_entry_' + str(i)] = 0
                    vars()['ut_entry_' + str(i)] = 0
                    vars()['ce_sl_trigger_' + str(i)] = False
                    vars()['pe_sl_trigger_' + str(i)] = False
                    vars()['ut_sl_trigger_' + str(i)] = False
                    vars()['ce_sl_time_' + str(i)] = ''
                    vars()['pe_sl_time_' + str(i)] = ''
                    vars()['ut_sl_time_' + str(i)] = ''
                    vars()['ce_pnl_' + str(i)] = 0
                    vars()['pe_pnl_' + str(i)] = 0
                    vars()['ut_pnl_' + str(i)] = 0
                    vars()['b_pl_' + str(i)] = 0
                    vars()['tt_pl_' + str(i)] = 0
                    vars()['ut_pl_' + str(i)] = 0
                    vars()['total_pl_' + str(i)] = 0

                exp_day = 'TRUE' if options_data.dte.iloc[0] == 0 else 'FALSE'

                if day != dte.loc[str(from_date.date()), index]:
                    from_date += datetime.timedelta(days=1)
                    continue

                start_dt = datetime.datetime.combine(from_date, start_time)
                end_dt = datetime.datetime.combine(from_date, end_time)
                end_dt_1m = end_dt + datetime.timedelta(minutes=10)

                options = options[options['date_time'] <= end_dt]

                ce_scrip_0, pe_scrip_0, ce_entry_0, pe_entry_0, start_dt, future_price, syn_future = strangle_strike(start_dt)

                if ce_scrip_0 == None:
                    from_date += datetime.timedelta(days=1)
                    continue

                entry_reference_time = start_dt

                ce_data = options[options.scrip == ce_scrip_0]
                ce_sl_trigger_0, ce_sl_time_0, ce_pnl_0 = OHLC_SL(start_dt, ce_data, ce_entry_0, ce_entry_0 * sl_per, False)

                pe_data = options[options.scrip == pe_scrip_0]
                pe_sl_trigger_0, pe_sl_time_0, pe_pnl_0 = OHLC_SL(start_dt, pe_data, pe_entry_0, pe_entry_0 * sl_per, False)

                ut_scrip_0, ut_entry_0, ut_high_0, ut_low_0, ut_close_0, ut_sl_trigger_0, ut_sl_time_0, ut_pnl_0 = '', '', '', '', '', False, '', 0
                b_pl_0, tt_pl_0, ut_pl_0 = 0, 0, 0

                if ce_sl_time_0 < pe_sl_time_0:
                    ut_scrip_0 = pe_scrip_0
                    ut_entry_0, ut_sl_trigger_0, ut_sl_time_0, ut_pnl_0 = OHLC_SL(ce_sl_time_0, pe_data, None, '', True)

                    if ut_entry_0 != '':
                        tt_pl_0 = ce_pnl_0
                        ut_pl_0 = pe_entry_0 - ut_entry_0 - Cal_slipage(pe_entry_0)

                elif pe_sl_time_0 < ce_sl_time_0:
                    ut_scrip_0 = ce_scrip_0
                    ut_entry_0, ut_sl_trigger_0, ut_sl_time_0, ut_pnl_0 = OHLC_SL(pe_sl_time_0, ce_data, None, '', True)

                    if ut_entry_0 != '':
                        tt_pl_0 = pe_pnl_0
                        ut_pl_0 = ce_entry_0 - ut_entry_0 - Cal_slipage(ce_entry_0)

                else:
                    if ce_sl_time_0 == end_dt_1m:
                        b_pl_0 = ce_pnl_0 + pe_pnl_0
                        ce_sl_time_0, pe_sl_time_0 = '', ''
                    else:
                        print('Rare Case call and put hit same time', from_date)

                if ut_sl_time_0 == end_dt_1m:
                    ut_sl_time_0 = ''
                if ce_sl_time_0 == end_dt_1m:
                    ce_sl_time_0 = ''
                if pe_sl_time_0 == end_dt_1m:
                    pe_sl_time_0 = ''

                total_pl_0 = b_pl_0 + tt_pl_0 + ut_pl_0 + ut_pnl_0

                for i in range(1, re_entries+1):
                    if vars()['ut_sl_trigger_' + str(i-1)]:
                        new_dt = vars()['ut_sl_time_' + str(i-1)]
                        vars()['ce_scrip_'+str(i)], vars()['pe_scrip_'+str(i)], vars()['ce_entry_'+str(i)], vars()['pe_entry_'+str(i)], start_dt, future_price, syn_future = strangle_strike(new_dt)

                        if vars()['ce_scrip_'+str(i)] == None:
                            continue

                        ce_data = options[options.scrip == vars()['ce_scrip_'+str(i)]]
                        vars()['ce_sl_trigger_'+str(i)], vars()['ce_sl_time_' + str(i)], vars()['ce_pnl_' + str(i)] = OHLC_SL(start_dt, ce_data, vars()['ce_entry_'+str(i)], vars()['ce_entry_'+str(i)] * sl_per, False)

                        pe_data = options[options.scrip == vars()['pe_scrip_'+str(i)]]
                        vars()['pe_sl_trigger_'+str(i)], vars()['pe_sl_time_' + str(i)], vars()['pe_pnl_' + str(i)] = OHLC_SL(start_dt, pe_data, vars()['pe_entry_'+str(i)], vars()['pe_entry_'+str(i)] * sl_per, False)

                        if vars()['ce_sl_time_' + str(i)] < vars()['pe_sl_time_' + str(i)]:
                            vars()['ut_scrip_' + str(i)] = vars()['pe_scrip_' + str(i)]
                            vars()['ut_entry_' + str(i)], vars()['ut_sl_trigger_' + str(i)], vars()['ut_sl_time_' + str(i)], vars()['ut_pnl_' + str(i)] = OHLC_SL(vars()['ce_sl_time_' + str(i)], pe_data, None, '', True)

                            if vars()['ut_entry_' + str(i)] != '':
                                vars()['tt_pl_' + str(i)] = vars()['ce_pnl_' + str(i)]
                                vars()['ut_pl_' + str(i)] = vars()['pe_entry_' + str(i)] - vars()['ut_entry_' + str(i)] - Cal_slipage(vars()['pe_entry_' + str(i)])

                        elif vars()['pe_sl_time_' + str(i)] < vars()['ce_sl_time_' + str(i)]:
                            vars()['ut_scrip_' + str(i)] = vars()['ce_scrip_' + str(i)]
                            vars()['ut_entry_' + str(i)], vars()['ut_sl_trigger_' + str(i)], vars()['ut_sl_time_' + str(i)], vars()['ut_pnl_' + str(i)] = OHLC_SL(vars()['pe_sl_time_' + str(i)], ce_data, None, '', True) 

                            if vars()['ut_entry_' + str(i)] != '':
                                vars()['tt_pl_' + str(i)] = vars()['pe_pnl_' + str(i)]
                                vars()['ut_pl_' + str(i)] = vars()['ce_entry_' + str(i)] - vars()['ut_entry_' + str(i)] - Cal_slipage(vars()['ce_entry_' + str(i)])

                        else:
                            if vars()['ce_sl_time_' + str(i)] == end_dt_1m:
                                vars()['b_pl_' + str(i)] = vars()['ce_pnl_' + str(i)] + vars()['pe_pnl_' + str(i)]
                                vars()['ce_sl_time_' + str(i)], vars()['pe_sl_time_' + str(i)] = '', ''
                            else:
                                print('Rare Case call and put hit same time', from_date)

                        if vars()['ut_sl_time_' + str(i)] == end_dt_1m:
                            vars()['ut_sl_time_' + str(i)] = ''
                        if vars()['ce_sl_time_' + str(i)] == end_dt_1m:
                            vars()['ce_sl_time_' + str(i)] = ''
                        if vars()['pe_sl_time_' + str(i)] == end_dt_1m:
                            vars()['pe_sl_time_' + str(i)] = ''

                        vars()['total_pl_' + str(i)] = vars()['b_pl_' + str(i)] + vars()['tt_pl_' + str(i)] + vars()['ut_pl_' + str(i)] + vars()['ut_pnl_' + str(i)]

                l1, total_pnl = [], 0
                for i in range(0, re_entries + 1):
                    l1.append(vars()['ce_scrip_'+str(i)])
                    l1.append(vars()['ce_entry_' + str(i)])
                    l1.append(vars()['ce_sl_trigger_' + str(i)])
                    l1.append(vars()['ce_sl_time_' + str(i)])
                    l1.append(vars()['ce_pnl_' + str(i)])
                    l1.append(vars()['pe_scrip_'+str(i)])
                    l1.append(vars()['pe_entry_' + str(i)])
                    l1.append(vars()['pe_sl_trigger_' + str(i)])
                    l1.append(vars()['pe_sl_time_' + str(i)])
                    l1.append(vars()['pe_pnl_' + str(i)])
                    l1.append(vars()['ut_scrip_'+str(i)])
                    l1.append(vars()['ut_entry_' + str(i)])
                    l1.append(vars()['ut_sl_trigger_' + str(i)])
                    l1.append(vars()['ut_sl_time_' + str(i)])
                    l1.append(vars()['ut_pnl_' + str(i)])
                    l1.append(vars()['b_pl_' + str(i)])
                    l1.append(vars()['tt_pl_' + str(i)])
                    l1.append(vars()['ut_pl_' + str(i)])
                    l1.append(vars()['total_pl_' + str(i)])
                    total_pnl += vars()['total_pl_' + str(i)]

                print(from_date)
                l0 = [str(from_date)[0:10], from_date.day_name(), future_price, exp_day, entry_reference_time.time()]
                log.loc[len(log.index)] = l0 + l1 + [total_pnl]
                from_date += datetime.timedelta(days=1)

            log.to_csv (f"{output_csv_path}{msg}.csv", index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            war = f"Error in row {row} at date: {from_date.date()} \nError: {e}\nParameter : {msg}"
            print(war)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={war}')
            from_date += datetime.timedelta(days=1)

print('END')

