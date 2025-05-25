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
    return open_price * slipage

def send_tg_msg(msg):
    print(msg)
    try:
        requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
    except Exception as e:
        print(e)

def get_gap(df):
    try:
        strike = df.scrip.str[:-2].astype(int).unique()
        strike.sort()

        gap = min([abs(strike[i-1] - s) for i, s in enumerate(strike) if i !=0])
        
        if gap > 100 and index == "BANKNIFTY":
            return 100
        if gap > 50 and index == "NIFTY":
            return 50
        if gap > 100 and index == "FINNIFTY":
            return 100
        if gap > 50 and index == "MIDCPNIFTY":
            return 50
        if gap > 100 and index == "SENSEX":
            return 100
        if gap > 100 and index == "BANKEX":
            return 100
        return gap
    except:
        return None

def find_my_straddle(start_dt):
    while start_dt < end_dt:
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

            return ce_scrip, pe_scrip, ce_price, pe_price, future_price, start_dt
        except:
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None

def find_my_strangle(start_dt, options_multiplier, check_inverted=True):
    while start_dt < end_dt:
        try:
            future_price = future_data.loc[start_dt,'close']
            target = (int(future_price/step) * step) / 100 * options_multiplier
            
            current_od = options[options['date_time'] >= start_dt]
            target_od = current_od[current_od['close'] > target].sort_values(by = ['date_time', 'close'])  
            
            for scrip in target_od['scrip'].values:
                if scrip[-2:] == 'CE':
                    ce_scrip = scrip
                    break
            
            for scrip in target_od['scrip'].values:
                if scrip[-2:] == 'PE':
                    pe_scrip = scrip
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
            
            if int(ce_scrip[:-2]) < int(pe_scrip[:-2]) and check_inverted:
                print("Inverted Strike shift to straddle")
                return find_my_straddle(start_dt)
            else:
                return ce_scrip, pe_scrip, ce_entry, pe_entry, future_price, start_dt
        except:
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None

def sell_ohlc_sl(fdataframe, entry_f, sl_price_f):
    """Check sl and calculate pnl"""
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]

    try:
        exit_f = fdata.close.iloc[-1]

        temp = fdata[fdata.high >= sl_price_f]

        try:
            sl_time = temp.date_time.iloc[0]
            sl_flag = True
            pnl = -(sl/100)*entry_f
            pnl = round(pnl - Cal_slipage(entry_f), 2)

        except IndexError:
            sl_time = ''
            sl_flag = False
            pnl = entry_f - exit_f
            pnl = round(pnl - Cal_slipage(entry_f), 2)

        return sl_flag, sl_time, pnl
    except IndexError:
        return False, '', 0

def high_sl(ftime, fdataframe, entry_f, exit_f, sl_price):
    """Check SL"""
    fdata = fdataframe.copy()

    fdata = fdata[fdata.date_time > ftime]
    fdata = fdata[fdata.high >= sl_price]

    try:
        sl_time = fdata.date_time.iloc[0]
        sl_flag = True
        pnl = -(sl/100)*entry_f
        pnl = round(pnl - Cal_slipage(entry_f), 2)

    except IndexError:
        sl_time = ''
        sl_flag = False
        pnl = entry_f - exit_f
        pnl = round(pnl - Cal_slipage(entry_f), 2)

    return sl_flag,sl_time,pnl

def check_decay(ftime,fdataframe,val):
    """Check for decay"""
    fdata = fdataframe.copy()

    fdata = fdata[fdata.date_time > ftime]
    fdata = fdata[fdata.low <= val]

    try:
        decay_time = fdata.date_time.iloc[0]
        decay_flag = True

    except IndexError:
        decay_time = ''
        decay_flag = False

    return decay_flag, decay_time

for row_idx in range(len(parameter)):
    if parameter.loc[row_idx,'run'] == True:
        try:
            
            t1 = datetime.datetime.now()
            index = parameter.loc[row_idx,'index']

            try:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d-%m-%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d-%m-%Y")
            except:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d/%m/%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d/%m/%Y")

            start_time = pd.to_datetime(parameter.loc[row_idx,'start_time'].replace(' ', ''), format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row_idx,'end_time'].replace(' ', ''), format="%H:%M").time()
            day = parameter.loc[row_idx,'day']
            decay = parameter.loc[row_idx,'decay']
            sl = parameter.loc[row_idx,'sl']
            options_multiplier = parameter.loc[row_idx,'om']
            re_entries = int(parameter.loc[row_idx,'re_entry']) 
                
            if options_multiplier <= 0:
                file_name = f"{index} RED {day} {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} Decay-{decay:.2f} SL-{sl:.2f} OM-{options_multiplier} RE-{re_entries}"
            else:
                options_multiplier = float(options_multiplier)
                file_name = f"{index} RED {day} {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} Decay-{decay:.2f} SL-{sl:.2f} OM-{options_multiplier:.2f} RE-{re_entries}"

            col = '/ce_scrip/ce_price/ce_sl/ce_sl_time/ce_pnl'
            for i in range(1, re_entries+1):
                col += f"/ce_scrip_{i}/ce_price_{i}/ce_decay_{i}/ce_decay_time_{i}/ce_sl_hit_{i}/ce_sl_time_{i}/ce_pnl_{i}"

            col += '/pe_scrip/pe_price/pe_sl/pe_sl_time/pe_pnl'
            for i in range(1, re_entries+1):
                col += f"/pe_scrip_{i}/pe_pripe_{i}/pe_decay_{i}/pe_decay_time_{i}/pe_sl_hit_{i}/pe_sl_time_{i}/pe_pnl_{i}"

            log = pd.DataFrame(columns= ("Date/Day/DTE/Expiry.Day/Time/Future" + col).split("/") + ["Total PNL"])

            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                step = 5000
                slipage = 0.0125
            if index == 'NIFTY':
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                step = 1000
                slipage = 0.01
            if index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                step = 1000
                slipage = 0.01
            if index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                step = 1000
                slipage = 0.0125
            if index == 'BANKEX':
                future_folder_path = 'BX Future/'
                option_folder_path = 'BX Options/'
                future_file_path = '_bankex_future.pkl'
                option_file_path = '_bankex.pkl'
                step = 5000
                slipage = 0.0125
            if index == 'SENSEX':
                future_folder_path = 'SX Future/'
                option_folder_path = 'SX Options/'
                future_file_path = '_sensex_future.pkl'
                option_file_path = '_sensex.pkl'
                step = 5000
                slipage = 0.0125

            while from_date <= to_date:
                try:
                    try:
                        future_data = pd.read_pickle(''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))).set_index(['date_time'])
                        options = pd.read_pickle(''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path)))
                        options_data = options.set_index(['date_time', 'scrip'])
                    except FileNotFoundError:
                        from_date += datetime.timedelta(days=1)
                        continue

                    gap = get_gap(options)
                    if gap is None:
                        from_date += datetime.timedelta(days=1)
                        continue

                    exp_day = 'TRUE' if options_data.dte.iloc[0] == 0 else 'FALSE'
                    
                    if day != dte.loc[str(from_date.date()), index]:
                        from_date += datetime.timedelta(days=1)
                        continue

                    start_dt = datetime.datetime.combine(from_date, start_time)
                    end_dt = datetime.datetime.combine(from_date, end_time)

                    options = options[options['date_time'] <= end_dt]

                    for i in range(1, re_entries+1):
                        vars()['ce_re_entry_trigger_' + str(i)] = False
                        vars()['ce_re_entry_time_' + str(i)] = ''
                        vars()['pe_re_entry_trigger_' + str(i)] = False
                        vars()['pe_re_entry_time_' + str(i)] = ''

                    for i in range(0, re_entries+1):
                        vars()['ce_scrip_' + str(i)] = ''
                        vars()['pe_scrip_' + str(i)] = ''
                        vars()['ce_price_' + str(i)] = ''
                        vars()['pe_price_' + str(i)] = ''
                        vars()['ce_sl_trigger_' + str(i)] = False
                        vars()['pe_sl_trigger_' + str(i)] = False
                        vars()['ce_sl_time_' + str(i)] = ''
                        vars()['pe_sl_time_' + str(i)] = ''
                        vars()['ce_pnl_' + str(i)] = 0
                        vars()['pe_pnl_' + str(i)] = 0

                    if options_multiplier <= 0:
                        ce_scrip_0, pe_scrip_0, ce_price_0, pe_price_0, future_entry, new_dt = find_my_straddle(start_dt)
                    else:
                        ce_scrip_0, pe_scrip_0, ce_price_0, pe_price_0, future_entry, new_dt = find_my_strangle(start_dt, options_multiplier)

                    if ce_scrip_0 is None:
                        from_date += datetime.timedelta(days=1)
                        continue

                    entry_reference_time = new_dt
                    l1 = [entry_reference_time.date(), from_date.day_name(), dte, exp_day, entry_reference_time.time(), future_entry] 

                    current_od = options[options['date_time'] >= new_dt]
                    ce_data = current_od[current_od.scrip == ce_scrip_0]
                    pe_data = current_od[current_od.scrip == pe_scrip_0]

                    ce_sl_entry_0 = ((100 + sl)/100) * ce_price_0
                    ce_sl_trigger_0, ce_sl_time_0, ce_pnl_0 = sell_ohlc_sl(ce_data, ce_price_0, ce_sl_entry_0)
                    t_time = ce_sl_time_0.time() if ce_sl_time_0 != '' else ''
                    l2 = [ce_scrip_0, ce_price_0, ce_sl_trigger_0, t_time, ce_pnl_0]

                    if ce_sl_trigger_0 is not False:
                        for i in range(1, re_entries + 1):

                            if vars()['ce_sl_time_' + str(i-1)] == '':
                                break

                            if options_multiplier <= 0:
                                vars()['ce_scrip_' + str(i)], t_pe_scrip, vars()['ce_price_' + str(i)], t_pe_price, future_entry, new_dt = find_my_straddle(vars()['ce_sl_time_' + str(i-1)])
                            else:
                                vars()['ce_scrip_' + str(i)], t_pe_scrip, vars()['ce_price_' + str(i)], t_pe_price, future_entry, new_dt = find_my_strangle(vars()['ce_sl_time_' + str(i-1)], options_multiplier)

                            if vars()['ce_scrip_' + str(i)] is None:
                                break

                            decay_val = vars()['ce_price_' + str(i)] * decay
                            ce_data = options[options.scrip == vars()['ce_scrip_' + str(i)]]

                            if ce_data.empty:
                                break

                            ce_exit = ce_data.close.iloc[-1]

                            vars()['ce_re_entry_trigger_'+str(i)],vars()['ce_re_entry_time_'+str(i)] = check_decay(new_dt, ce_data, decay_val)

                            if vars()['ce_re_entry_trigger_' + str(i)] is True:
                                ce_sl_price = decay_val * ((100 + sl) / 100)
                                vars()['ce_sl_trigger_' + str(i)], vars()['ce_sl_time_' + str(i)], vars()['ce_pnl_' + str(i)] = high_sl(vars()['ce_re_entry_time_' + str(i)], ce_data, decay_val, ce_exit, ce_sl_price)
                            else:
                                break

                    total_ce_pnl = ce_pnl_0
                    for i in range(1, re_entries + 1):
                        l2.append(vars()['ce_scrip_' + str(i)])
                        l2.append(vars()['ce_price_' + str(i)])
                        l2.append(vars()['ce_re_entry_trigger_' + str(i)])
                        if vars()['ce_re_entry_time_' + str(i)] != '':
                            l2.append(vars()['ce_re_entry_time_' + str(i)].time())
                        else:
                            l2.append('')
                        l2.append(vars()['ce_sl_trigger_' + str(i)])
                        if vars()['ce_sl_time_' + str(i)] != '':
                            l2.append(vars()['ce_sl_time_' + str(i)].time())
                        else:
                            l2.append('')
                        l2.append(vars()['ce_pnl_' + str(i)])
                        total_ce_pnl += vars()['ce_pnl_' + str(i)]

                    pe_sl_entry_0 = ((100 + sl)/100) * pe_price_0
                    pe_sl_trigger_0, pe_sl_time_0, pe_pnl_0 = sell_ohlc_sl(pe_data, pe_price_0, pe_sl_entry_0)
                    t_time = pe_sl_time_0.time() if pe_sl_time_0 != '' else ''
                    l3 = [pe_scrip_0, pe_price_0, pe_sl_trigger_0, t_time, pe_pnl_0]
                    
                    if pe_sl_trigger_0 is not False:
                        for i in range(1, re_entries + 1):

                            if vars()['pe_sl_time_' + str(i-1)] == '':
                                break

                            if options_multiplier <= 0:
                                t_ce_scrip, vars()['pe_scrip_'+str(i)], t_ce_price, vars()['pe_price_'+str(i)], future_entry, new_dt = find_my_straddle(vars()['pe_sl_time_' + str(i-1)])
                            else:
                                t_ce_scrip, vars()['pe_scrip_'+str(i)], t_ce_price, vars()['pe_price_'+str(i)], future_entry, new_dt = find_my_strangle(vars()['pe_sl_time_' + str(i-1)], options_multiplier)

                            if vars()['pe_scrip_' + str(i)] is None:
                                break

                            decay_val = vars()['pe_price_' + str(i)] * decay
                            pe_data = options[options.scrip == vars()['pe_scrip_' + str(i)]]

                            if pe_data.empty:
                                break

                            pe_exit = pe_data.close.iloc[-1]

                            vars()['pe_re_entry_trigger_'+str(i)], vars()['pe_re_entry_time_'+str(i)] = check_decay(new_dt, pe_data, decay_val)

                            if vars()['pe_re_entry_trigger_' + str(i)] is True:
                                pe_sl_price = decay_val * ((100 + sl) / 100)
                                vars()['pe_sl_trigger_' + str(i)], vars()['pe_sl_time_' + str(i)], vars()['pe_pnl_' + str(i)] = high_sl(vars()['pe_re_entry_time_' + str(i)], pe_data, decay_val, pe_exit, pe_sl_price)
                            else:
                                break

                    total_pe_pnl = pe_pnl_0
                    for i in range(1, re_entries + 1):
                        l3.append(vars()['pe_scrip_' + str(i)])
                        l3.append(vars()['pe_price_' + str(i)])
                        l3.append(vars()['pe_re_entry_trigger_' + str(i)])
                        if vars()['pe_re_entry_time_' + str(i)] != '':
                            l3.append(vars()['pe_re_entry_time_' + str(i)].time())
                        else:
                            l3.append('')
                        l3.append(vars()['pe_sl_trigger_' + str(i)])
                        if vars()['pe_sl_time_' + str(i)]:
                            l3.append(vars()['pe_sl_time_' + str(i)].time())
                        else:
                            l3.append('')
                        l3.append(vars()['pe_pnl_' + str(i)])
                        total_pe_pnl += vars()['pe_pnl_' + str(i)]


                    print(from_date)
                    log.loc[len(log.index)] = l1+l2+l3+[total_ce_pnl + total_pe_pnl]
                    from_date += datetime.timedelta(days=1)
                except Exception as e:
                    msg = f"Error in Date {str(from_date)[0:10]}: \n{e} \nParameter : \n" + file_name 
                    send_tg_msg(msg)
                    from_date += datetime.timedelta(days=1)
                    
            log.to_csv(f"{output_csv_path}{file_name}.csv", index=False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            msg = f"Error in Row {row_idx}: \n{e} \nParameter : \n" + file_name 
            send_tg_msg(msg)

print('END')
