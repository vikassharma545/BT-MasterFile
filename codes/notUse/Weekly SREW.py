import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import numpy as np
import pandas as pd
import datetime
import requests
from glob import glob
import os
import json
import shutil

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)

files = glob("C:/PICKLE/BN Future/*")
total_trading_day = pd.Series([i.split('\\')[1][0:10] for i in files])

if not os.path.isdir(output_csv_path) and output_csv_path != '':
    os.mkdir(output_csv_path)
else:
    shutil.rmtree(output_csv_path)
    os.mkdir(output_csv_path)

def Cal_slipage(open_price):
    slipage = open_price * (slipage_var/100)
    return slipage

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
        return gap
    except :
        return 0

def straddle_strike(start_dt):
    while (start_dt < frame_end_dt):
        try:
            # future price
            future_price = weekly_future.loc[start_dt,'close']
            round_future_price = round(future_price/gap)*gap
            
            ce_scrip = str(round_future_price) + 'CE'
            pe_scrip = str(round_future_price) + 'PE'
            ce_price = weekly_options_data.loc[(start_dt, ce_scrip),'close']
            pe_price = weekly_options_data.loc[(start_dt, pe_scrip),'close']
            
            #### to Find out minimum difference strike for straddle
            syn_future = ce_price - pe_price + round_future_price
            round_syn_future = round(syn_future/gap)*gap
            
            ce_scrip_list = [str(round_syn_future)+'CE', str(round_syn_future+gap)+'CE',str(round_syn_future-gap)+'CE']
            pe_scrip_list = [str(round_syn_future)+'PE', str(round_syn_future+gap)+'PE',str(round_syn_future-gap)+'PE']
            
            difference = []
            for i in range(len(ce_scrip_list)):
                try:
                    ce_price = weekly_options_data.loc[(start_dt,ce_scrip_list[i]),'close']
                    pe_price = weekly_options_data.loc[(start_dt,pe_scrip_list[i]),'close']
                    difference.append(abs(ce_price-pe_price))
                except:
                    difference.append(-1)
                                        
            min_value = 99999
            for i in range(3):
                if (min_value > difference[i]) & (difference[i] != -1):
                    min_value = difference[i]
                    scrip_index = i
                    
            # required scrip
            ce_scrip = ce_scrip_list[scrip_index]
            pe_scrip = pe_scrip_list[scrip_index]
            ce_price = weekly_options_data.loc[(start_dt,ce_scrip),'close']
            pe_price = weekly_options_data.loc[(start_dt,pe_scrip),'close']
            
            premium = ce_price + pe_price
            limit = premium * (range_sl/100)
            
            lower_range = int(ce_scrip[0:-2]) - limit
            upper_range = int(ce_scrip[0:-2]) + limit
            
            return ce_scrip, pe_scrip, start_dt, ce_price, pe_price, lower_range, upper_range      
        except:
            start_dt += datetime.timedelta(minutes = 1)
            if start_dt.time() == pd.Timestamp('15:30').time():
                start_dt = pd.Timestamp.combine(start_dt.date() + pd.Timedelta(days=1), datetime.time(9,15))
                
    return None, None, None, None, None, None, None

def straddle_strike_EOD(start_dt):
    try:
        # future price
        future_price = weekly_future.loc[start_dt,'close']
        round_future_price = round(future_price/gap)*gap

        ce_scrip = str(round_future_price) + 'CE'
        pe_scrip = str(round_future_price) + 'PE'
        ce_price = weekly_options_data.loc[(start_dt, ce_scrip),'close']
        pe_price = weekly_options_data.loc[(start_dt, pe_scrip),'close']

        #### to Find out minimum difference strike for straddle
        syn_future = ce_price - pe_price + round_future_price
        round_syn_future = round(syn_future/gap)*gap

        ce_scrip_list = [str(round_syn_future)+'CE', str(round_syn_future+gap)+'CE',str(round_syn_future-gap)+'CE']
        pe_scrip_list = [str(round_syn_future)+'PE', str(round_syn_future+gap)+'PE',str(round_syn_future-gap)+'PE']

        difference = []
        for i in range(len(ce_scrip_list)):
            try:
                ce_price = weekly_options_data.loc[(start_dt,ce_scrip_list[i]),'close']
                pe_price = weekly_options_data.loc[(start_dt,pe_scrip_list[i]),'close']
                difference.append(abs(ce_price-pe_price))
            except:
                difference.append(-1)

        min_value = 99999
        for i in range(3):
            if (min_value > difference[i]) & (difference[i] != -1):
                min_value = difference[i]
                scrip_index = i

        # required scrip
        ce_scrip = ce_scrip_list[scrip_index]
        pe_scrip = pe_scrip_list[scrip_index]
        ce_price = weekly_options_data.loc[(start_dt,ce_scrip),'close']
        pe_price = weekly_options_data.loc[(start_dt,pe_scrip),'close']

        premium = ce_price + pe_price
        limit = premium * (range_sl/100)

        lower_range = int(ce_scrip[0:-2]) - limit
        upper_range = int(ce_scrip[0:-2]) + limit

        return ce_scrip, pe_scrip, start_dt, ce_price, pe_price, lower_range, upper_range      
    except:
        return None, None, None, None, None, None, None

def find_sl(ce_scrip, pe_scrip, start_dt, straddle_open_f, upper_limit, lower_limit):

    start_dt += datetime.timedelta(minutes=1)
    slipage = Cal_slipage(straddle_open_f)    
    
    intra_limit = straddle_open_f * (intra_minute_sl/100)
    intra_lower_limit = int(ce_scrip[0:-2]) - intra_limit
    intra_upper_limit = int(ce_scrip[0:-2]) + intra_limit
        
    ce_data = weekly_options.loc[(weekly_options['scrip'] == ce_scrip) & (weekly_options['date_time'] >= start_dt) , :]
    pe_data = weekly_options.loc[(weekly_options['scrip'] == pe_scrip) & (weekly_options['date_time'] >= start_dt) , :]

    ce_data = ce_data[ce_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
    pe_data = pe_data[pe_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)
    
    ce_data = ce_data.sort_values(by=['date_time'])
    pe_data = pe_data.sort_values(by=['date_time'])

    try:
        straddle_exit_f = (ce_data['close'].iloc[-1] + pe_data['close'].iloc[-1])
    except:
        return False,'', 0, ''

    sl_flag, straddle_sl_time, straddle_pnl = False, '', 0
    
    for i in range(len(ce_data) - 1):
        
        straddle_close = ce_data.close.iloc[i] + pe_data.close.iloc[i]
        straddle_high_low_max = max(ce_data.low.iloc[i] + pe_data.high.iloc[i], ce_data.high.iloc[i] + pe_data.low.iloc[i])
        start_dt = ce_data['date_time'].iloc[i]
        
        try:
            present_future_price = weekly_future.loc[start_dt,'close']
            future_high_price = weekly_future.loc[start_dt,'high']
            future_low_price = weekly_future.loc[start_dt,'low']
            
            if start_dt.time() != datetime.time(9,15):
                if intra_upper_limit < future_high_price or future_low_price < intra_lower_limit:
                    sl_flag = True
                    straddle_sl_time = start_dt
                    straddle_pnl = straddle_open_f - straddle_high_low_max - slipage
                    is_intra_sl = True
                    break
            
            if upper_limit < present_future_price or present_future_price < lower_limit:
                sl_flag = True
                straddle_sl_time = start_dt
                straddle_pnl = straddle_open_f - straddle_close - slipage
                is_intra_sl = ''
                break
 
        except:
            pass
        
        if start_dt.date() != ce_data['date_time'].iloc[i + 1].date():
            for r in range(i, i-20, -1):
                try:
                    cs,ps,t,co,po, lower_limit, upper_limit = straddle_strike_EOD(ce_data['date_time'].iloc[r])
                    
                    limit_price = (co + po) * (range_sl/100)
                    intra_limit = (co + po) * (intra_minute_sl/100)
                    
                    lower_limit = int(ce_scrip[0:-2]) - limit_price
                    upper_limit = int(ce_scrip[0:-2]) + limit_price
                    intra_lower_limit = int(ce_scrip[0:-2]) - intra_limit
                    intra_upper_limit = int(ce_scrip[0:-2]) + intra_limit
                    break
                except:
                    pass
        
    if sl_flag:
        return sl_flag, straddle_sl_time, straddle_pnl, is_intra_sl
    else:
        straddle_pnl = straddle_open_f - straddle_exit_f - slipage
        return False,'', straddle_pnl, ''

# d = {'thursday':1, 'wednesday':2, 'tuesday':3, 'monday':4, 'friday':5}

for row in range(len(parameter)):
    # reading rows of parameter
    if parameter['run'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
#             strategy = parameter.loc[row, 'strategy']
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            start_time = pd.to_datetime(parameter.loc[row,'start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', '')[0:5], format="%H:%M").time()
            range_sl = parameter.loc[row,'range_sl']
            trading_day = parameter.loc[row,'entry']
#             trading_day = d[day.lower()]
            re_entries = parameter.loc[row,'re_entries']
            slipage_var = parameter.loc[row,'slipage']
            intra_minute_sl = parameter.loc[row,'intra_minute_sl']

            print(f"Running Row : {row}  {index}  SREW  {str(start_time).replace(':','')[:4]}  {str(end_time).replace(':','')[:4]}  SL-{range_sl} Intra.SL-{intra_minute_sl}  RE-{re_entries}  T-{trading_day}  Slipage-{slipage_var}  Dynamic Range")

            cols = ''
            for i in range(re_entries + 1):  
                cols += f"/ST{i}/ST{i}.O/ST{i}.SL.Trigg/Intra.SL{i}/ST{i}.SL.Time/ST{i}.PL"

            log = pd.DataFrame(columns =("Start.Date/Trading.Day/End.Date/Start.Time/End.Time/Entry.Time" + cols + '/Total PNL').split('/'))

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

            while from_date <= to_date:    
                try:
                    weekly_future = pd.DataFrame()
                    weekly_options = pd.DataFrame()

                    expiry_left = 7
                    future_week_list = []
                    option_week_list = []
                    dte_list = []

                    while True:
                        try:
                            future_path = ''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))
                            option_path = ''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path))
                            future_data = pd.read_pickle(future_path)         
                            options = pd.read_pickle(option_path)    
                        except:
                            from_date += datetime.timedelta(days=1)     
                            if from_date > to_date:
                                break
                            continue

                        if expiry_left >= options['dte'].iloc[0]:  
                            expiry_left = options['dte'].iloc[0]
                            dte_list.append(expiry_left)
                            future_week_list.append(future_path)
                            option_week_list.append(option_path)                        
                            from_date += datetime.timedelta(days=1)
                        else:
                            break


                    dte_list = dte_list[-(trading_day):] 
                    future_week_list = future_week_list[-(trading_day):] 
                    option_week_list = option_week_list[-(trading_day):]

                    for i in range(len(future_week_list)):

                        future_data = pd.read_pickle(str(future_week_list[i]))
                        options = pd.read_pickle(str(option_week_list[i]))

                        weekly_future = pd.concat([weekly_future,future_data], ignore_index=True)
                        weekly_options = pd.concat([weekly_options,options], ignore_index=True)

                    if weekly_future.empty == True:
                        from_date += datetime.timedelta(days=1)
                        continue

                    weekly_future.sort_values(by='date_time',inplace=True)
                    weekly_future = weekly_future[weekly_future.date_time.dt.time != datetime.time(15,30)]
                    weekly_future.set_index('date_time', inplace=True)
                    weekly_options.sort_values(by=['date_time','close'], inplace=True)
                    frame_start_dt = pd.Timestamp.combine(weekly_options['date_time'].iloc[0], start_time)
                    frame_end_dt = pd.Timestamp.combine(weekly_options['date_time'].iloc[-1], end_time)
                    weekly_options = weekly_options[(weekly_options['date_time'] >= frame_start_dt) & (weekly_options['date_time'] <= frame_end_dt)]
                    weekly_options = weekly_options[weekly_options.date_time.dt.time != datetime.time(15,30)]
                    weekly_options_data = weekly_options.set_index(['date_time', 'scrip'])

                    if index in ['FINNIFTY', 'MIDCPNIFTY']:
                        gap = get_gap(options)

                    for i in range(0, re_entries+1):
                        vars()['straddle_open_' + str(i)] = ''
                        vars()['straddle_pl_' + str(i)] = 0
                        vars()['straddle_sl_trigger_' + str(i)] = False
                        vars()['straddle_sl_time_' + str(i)] = ''
                        vars()['straddle_strike_' + str(i)] = ''
                        vars()['ce_close_' + str(i)] = 0
                        vars()['pe_close_' + str(i)] = 0
                        vars()['is_Intra_sl_' + str(i)] = ''

                    #straddle 0
                    ce_scrip, pe_scrip, frame_start_dt, ce_close_0, pe_close_0, lower_range, upper_range = straddle_strike(frame_start_dt)

                    if ce_scrip == None:
                        continue

                    straddle_strike_0 = pe_scrip[:-2]
                    straddle_open_0 = ce_close_0 + pe_close_0
                    entry_reference_time = frame_start_dt
                    straddle_sl_trigger_0, straddle_sl_time_0, straddle_pl_0, is_Intra_sl_0 = find_sl(ce_scrip, pe_scrip, frame_start_dt, straddle_open_0, upper_range, lower_range)    

                    # re-entries
                    re_entrie_flag = True
                    if (straddle_sl_trigger_0 == False):
                        re_entrie_flag = False
                    else:
                        if (straddle_sl_time_0 == frame_end_dt):
                            re_entrie_flag = False

                    for z in range(1, re_entries+1):
                        if re_entrie_flag == False:
                            break
                        else:
                            ce_scrip, pe_scrip, frame_start_dt, vars()['ce_close_' + str(z)], vars()['pe_close_' + str(z)], lower_range, upper_range = straddle_strike(vars()['straddle_sl_time_' + str(z - 1)])

                            if ce_scrip == None:
                                break

                            vars()['straddle_open_' + str(z)] = vars()['ce_close_' + str(z)] + vars()['pe_close_' + str(z)]
                            vars()['straddle_strike_' + str(z)] = pe_scrip[:-2]

                            vars()['straddle_sl_trigger_' + str(z)] , vars()['straddle_sl_time_' + str(z)], vars()['straddle_pl_' + str(z)], vars()['is_Intra_sl_' + str(z)] = find_sl(ce_scrip, pe_scrip, frame_start_dt, vars()['straddle_open_' + str(z)], upper_range, lower_range)

                            if (vars()['straddle_sl_trigger_' + str(z)] == False):
                                re_entrie_flag = False
                            else:
                                if (vars()['straddle_sl_time_' + str(z)] >= frame_end_dt - datetime.timedelta(minutes=5)):
                                    re_entrie_flag = False

                    l1 = []
                    total_pnl = 0
                    for i in range(0, re_entries+1):
                        l1.append(vars()['straddle_strike_' + str(i)])
                        l1.append(vars()['straddle_open_' + str(i)])
                        l1.append(vars()['straddle_sl_trigger_' + str(i)])
                        l1.append(vars()['is_Intra_sl_' + str(i)])
                        l1.append(vars()['straddle_sl_time_' + str(i)])
                        l1.append(vars()['straddle_pl_' + str(i)])
                        total_pnl += vars()['straddle_pl_' + str(i)]

                    print(entry_reference_time, frame_end_dt)
                    l0 = [entry_reference_time.date(), entry_reference_time.day_name() , frame_end_dt.date() , start_time, end_time, entry_reference_time.time()]
                    log.loc[len(log.index)] = l0 + l1 + [total_pnl]
                except Exception as e:
                    msg = f"Error in Week {frame_start_dt}-{frame_end_dt} : \n{e} \nParameter : \n{index} SREW {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} SL-{range_sl} Intra.SL-{intra_minute_sl} RE-{re_entries} T-{trading_day} Slipage-{slipage_var} Dynamic Range - CP-ATM-P"
                    print(msg)
                    try:
                        requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
                    except Exception as e:
                        print(e)
                    continue
                    
            log.to_csv(output_csv_path + f"{index} SREW {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} SL-{range_sl} Intra.SL-{intra_minute_sl} RE-{re_entries} T-{trading_day} Slipage-{slipage_var} Dynamic Range.csv", index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            msg = f"*Error in row {row} : \n{e} \nParameter : \n{index} SREW {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} SL-{range_sl} Intra.SL-{intra_minute_sl} RE-{re_entries} T-{trading_day} Slipage-{slipage_var} Dynamic Range - CP-ATM-P*"
            print(msg)
            try:
                requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&parse_mode=Markdown&text={msg}')
            except Exception as e:
                print(e)   
print('END')

