import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import pandas as pd
import numpy as np
import datetime
import pickle
import requests
import os
import shutil
import json
from glob import glob

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
dte_file = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
dte_file = dte_file.set_index('Date')

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

def find_my_strangle(start_dt, options_multiplier, check_inverted=False):
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

for row_idx in range(len(parameter)):
    if parameter.loc[row_idx,'run'] == True:
        try:
            t1 = datetime.datetime.now()
            index = parameter.loc[row_idx,'index']
            day = parameter.loc[row_idx,'day']
            try:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d-%m-%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d-%m-%Y")
            except:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d/%m/%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d/%m/%Y")
                
            start_time = pd.to_datetime(parameter.loc[row_idx,'start_time'].replace(' ', ''), format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row_idx,'end_time'].replace(' ', ''), format="%H:%M").time()
            
            # SL = parameter.loc[row_idx,'SL']
            SD = parameter.loc[row_idx,'SD']

            file_name = f"{index} IronFly {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} {day} SD-{SD:.2f}"

            log = pd.DataFrame(columns =('Date/Day/DTE/Expiry.Day/Time/Future/Std.Strike/CE.Price/PE.Price/Wing.Width/CE.Wing/PE.Wing/CE.Wing.Price/PE.Wing.Price/Std.Premium/Wing.Premium/Initial.Premium/STD.EOD.Exit/Wing.EOD.Exit/EOD.Premium/Total PNL').split('/'))

            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                gap = 100
                step = 5000
                slipage = 0.0125
            if index == 'NIFTY':
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                gap = 50
                step = 1000
                slipage = 0.01
            if index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                gap = None
                step = 1000
                slipage = 0.0125
            if index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                gap = None
                step = 1000
                slipage = 0.0125

            while from_date <= to_date:
                try:
                    try:
                        future_data = pd.read_pickle(''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))).set_index(['date_time'])         
                        options = pd.read_pickle(''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path)))
                        options_data = options.set_index(['date_time', 'scrip'])
                    except:
                        from_date += datetime.timedelta(days=1) 
                        continue

                    gap = get_gap(options)
                    if gap is None:
                        from_date += datetime.timedelta(days=1)
                        continue

                    exp_day = 'TRUE' if options_data['dte'].iloc[0] == 0 else 'FALSE'
                    dte = int(dte_file.loc[str(from_date.date()), index])
                    
                    if day != dte:
                        from_date += datetime.timedelta(days=1)
                        continue

                    # start time and end time
                    start_dt = datetime.datetime.combine(from_date, start_time)
                    end_dt = datetime.datetime.combine(from_date, end_time) 

                    # options data below end time
                    options = options[options['date_time'] <= end_dt]

                    # Straddle data
                    ce_scrip, pe_scrip, ce_price, pe_price, future_price, start_dt = find_my_straddle(start_dt)

                    if ce_scrip == None:
                        from_date += datetime.timedelta(days=1)  
                        continue

                    straddle_entry_time = start_dt
                    straddle_open = ce_price + pe_price

                    ce_data = options.loc[(options['scrip'] == ce_scrip) & (options['date_time'] >= start_dt), :]
                    pe_data = options.loc[(options['scrip'] == pe_scrip) & (options['date_time'] >= start_dt), :]

                    ce_data = ce_data[ce_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
                    pe_data = pe_data[pe_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)

                    # strangle data or wing data
                    wing_width = SD * straddle_open
                    wing_width = int(((wing_width//gap) + 1) * gap)

                    ce_wing = str(int(int(ce_scrip[:-2]) + wing_width)) + 'CE'
                    pe_wing = str(int(int(pe_scrip[:-2]) - wing_width)) + 'PE'

                    while(int(ce_scrip[:-2]) < int(ce_wing[:-2])):
                        try:                       
                            ce_wing_price = options_data.loc[(start_dt,ce_wing),'close']
                            pe_wing_price = options_data.loc[(start_dt,pe_wing),'close']
                            break
                        except:
                            wing_width -= gap
                            ce_wing = str(int(int(ce_scrip[:-2]) + wing_width)) + 'CE'
                            pe_wing = str(int(int(pe_scrip[:-2]) - wing_width)) + 'PE'

                    wing_open = ce_wing_price + pe_wing_price

                    ce_wing_data = options.loc[(options['scrip'] == ce_wing) & (options['date_time'] >= start_dt), :]
                    pe_wing_data = options.loc[(options['scrip'] == pe_wing) & (options['date_time'] >= start_dt), :]

                    ce_wing_data = ce_wing_data[ce_wing_data['date_time'].isin(pe_wing_data['date_time'])].reset_index(drop=True)
                    pe_wing_data = pe_wing_data[pe_wing_data['date_time'].isin(ce_wing_data['date_time'])].reset_index(drop=True)

                    ce_wing_data = ce_wing_data[ce_wing_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
                    pe_wing_data = pe_wing_data[pe_wing_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)

                    ce_data = ce_data[ce_data['date_time'].isin(ce_wing_data['date_time'])].reset_index(drop=True)
                    pe_data = pe_data[pe_data['date_time'].isin(ce_wing_data['date_time'])].reset_index(drop=True) 

                    ce_data = ce_data.sort_values(by=['date_time'])
                    pe_data = pe_data.sort_values(by=['date_time'])

                    ce_wing_data = ce_wing_data.sort_values(by=['date_time'])
                    pe_wing_data = pe_wing_data.sort_values(by=['date_time'])

                    if ce_data.empty or ce_wing_data.empty:
                        from_date += datetime.timedelta(days=1)  
                        continue

                    # entry and exit price
                    initial_premium = straddle_open - wing_open
                    max_loss = wing_width - initial_premium

                    straddle_exit = ce_data.close.iloc[-1] + pe_data.close.iloc[-1]
                    wing_exit = ce_wing_data.close.iloc[-1] + pe_wing_data.close.iloc[-1]

                    entry_price = straddle_open - wing_open
                    slipage_price = entry_price - Cal_slipage(straddle_open + wing_open)

                    # sl_price = entry_price * (1 + (SL/100))
                    eod_exit_price = straddle_exit - wing_exit
                    pl_without_sl = round(slipage_price - eod_exit_price, 2)

                    # sl_time, sl_hit, sl_index, pnl, exit_price = '', False, '', 0, ''
                    # candle_close_price_list = ((ce_data.close + pe_data.close) - (ce_wing_data.close + pe_wing_data.close)).tolist()

                    # # if sl not hit i.e hit value is null throw error
                    # try:
                    #     hit_value = [ele for ele in candle_close_price_list if ele >= sl_price][0]
                    #     sl_hit = True
                    #     sl_index = candle_close_price_list.index(hit_value)
                    #     sl_time = ce_data['date_time'].iloc[sl_index].time()
                    #     pnl = round(slipage_price - hit_value, 2)
                    #     exit_price = hit_value
                    # except:
                    #     pnl = round(slipage_price - eod_exit_price, 2)
                    #     exit_price = eod_exit_price

                    print(from_date)
                    log.loc[len(log.index)] = [str(from_date)[0:10], from_date.day_name(), dte, exp_day, straddle_entry_time.time(), int(future_price), pe_scrip[:-2], ce_price, pe_price, wing_width, ce_wing, pe_wing, ce_wing_price, pe_wing_price, straddle_open, wing_open, initial_premium, straddle_exit, wing_exit, eod_exit_price, pl_without_sl]

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