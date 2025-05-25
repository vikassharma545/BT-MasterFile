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
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
dte = dte.set_index('Date')

files = glob("C:/PICKLE/BN Future/*")
total_trading_day = pd.Series([i.split('\\')[1][0:10] for i in files])

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
        return gap
    except :
        return 0

def straddle_strike(start_dt, wkly_future, wkly_option, wkly_option_data):
    entry_time = start_dt.time()
    while (start_dt < frame_end_dt):
        try:
            # future price
            future_price = wkly_future.loc[start_dt,'close']
            round_future_price = round(future_price/gap)*gap
            
            ce_scrip = str(round_future_price) + 'CE'
            pe_scrip = str(round_future_price) + 'PE'
            ce_price = wkly_option_data.loc[(start_dt, ce_scrip),'close']
            pe_price = wkly_option_data.loc[(start_dt, pe_scrip),'close']
            
            #### to Find out minimum difference strike for straddle
            syn_future = ce_price - pe_price + round_future_price
            round_syn_future = round(syn_future/gap)*gap
            
            ce_scrip_list = [str(round_syn_future)+'CE', str(round_syn_future+gap)+'CE',str(round_syn_future-gap)+'CE']
            pe_scrip_list = [str(round_syn_future)+'PE', str(round_syn_future+gap)+'PE',str(round_syn_future-gap)+'PE']
            
            difference = []
            for i in range(len(ce_scrip_list)):
                try:
                    ce_price = wkly_option_data.loc[(start_dt,ce_scrip_list[i]),'close']
                    pe_price = wkly_option_data.loc[(start_dt,pe_scrip_list[i]),'close']
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
            ce_price = wkly_option_data.loc[(start_dt,ce_scrip),'close']
            pe_price = wkly_option_data.loc[(start_dt,pe_scrip),'close']
            
            return ce_scrip, pe_scrip, start_dt, ce_price, pe_price, future_price, syn_future           
        except:
            start_dt += datetime.timedelta(minutes = 1)
            if start_dt.time() == pd.Timestamp('15:30').time():
                start_dt = pd.Timestamp.combine(start_dt.date() + pd.Timedelta(days=1), pd.Timestamp('09:15').time())
                
    return None, None, None, None, None, None, None           

for row in range(len(parameter)):
    # reading rows of parameter
    if parameter['run'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            start_time = pd.to_datetime(parameter.loc[row,'start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', '')[0:5], format="%H:%M").time()
            trading_day = parameter.loc[row,'trading_day']
            SD = parameter.loc[row,'SD']
            print('Running Row :', row , index + ' IFW ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SD-' + str(SD) + ' ' + str(trading_day))

            log = pd.DataFrame(columns=('Start.Date/Trading.Day/End.Date/End.Day/Start.Time/End.Time/entry_time/Strike/CE Price/PE Price/Straddle_Entry_price/straddle_exit_price/ce_wing/pe_wing/ce_wing_price/pe_wing_price/wing_entry_price/wing_exit_price/Entry_Price/Exit_price/Total PNL').split('/'))

            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                gap = 100
                step = 5000
                slipage_var = 0.0125
            elif index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                gap = 0
                step = 1000
                slipage_var = 0.015
            elif index == 'NIFTY':
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                gap = 50
                step = 1000
                slipage_var = 0.01
            elif index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                gap = None
                step = 1000
                slipage_var = 0.0125

            while from_date <= to_date:
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
                weekly_future.set_index('date_time', inplace=True)
                weekly_options.sort_values(by=['date_time','close'], inplace=True)
                frame_start_dt = pd.Timestamp.combine(weekly_options['date_time'].iloc[0], start_time)
                frame_end_dt = pd.Timestamp.combine(weekly_options['date_time'].iloc[-1], end_time)
                weekly_options = weekly_options[(weekly_options['date_time'] >= frame_start_dt) & (weekly_options['date_time'] <= frame_end_dt)]
                weekly_options_data = weekly_options.set_index(['date_time', 'scrip'])

                if index in ['FINNIFTY', 'MIDCPNIFTY']:
                    gap = get_gap(weekly_options)
                
                ce_scrip, pe_scrip, frame_start_dt, ce_price, pe_price, future_price, syn_future = straddle_strike(frame_start_dt,weekly_future,weekly_options,weekly_options_data)
                
                if ce_scrip == None:
                    from_date += datetime.timedelta(days=1)
                    continue
                    
                straddle_open = ce_price + pe_price
                straddle_entry_time = frame_start_dt
                print(straddle_entry_time, frame_end_dt)
                    
                ce_data = weekly_options.loc[(weekly_options['scrip'] == ce_scrip) & (weekly_options['date_time'] >= frame_start_dt), :]
                pe_data = weekly_options.loc[(weekly_options['scrip'] == pe_scrip) & (weekly_options['date_time'] >= frame_start_dt), :]

                ce_data = ce_data[ce_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
                pe_data = pe_data[pe_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)
                
                other_limit = 0
                limit = SD * straddle_open
                limit = round(limit/100)*100

                ce_wing = str(int(ce_scrip[:-2]) + limit) + 'CE'
                pe_wing = str(int(pe_scrip[:-2]) - limit) + 'PE'
                
                while(int(ce_scrip[:-2]) <= int(ce_wing[:-2])):
                    try:                          
                        ce_wing_price = weekly_options_data.loc[(frame_start_dt,ce_wing),'close']
                        pe_wing_price = weekly_options_data.loc[(frame_start_dt,pe_wing),'close']
                        break
                    except:
                        other_limit += 100
                        ce_wing = str(int(ce_scrip[:-2]) + limit - other_limit) + 'CE'
                        pe_wing = str(int(pe_scrip[:-2]) - limit + other_limit) + 'PE'

                ce_wing_price = weekly_options_data.loc[(frame_start_dt,ce_wing),'close']
                pe_wing_price = weekly_options_data.loc[(frame_start_dt,pe_wing),'close']

                wing_ce_data = weekly_options.loc[(weekly_options['scrip'] == ce_wing) & (weekly_options['date_time'] >= frame_start_dt), :]
                wing_pe_data = weekly_options.loc[(weekly_options['scrip'] == pe_wing) & (weekly_options['date_time'] >= frame_start_dt), :]
                
                wing_ce_data = wing_ce_data[wing_ce_data['date_time'].isin(wing_pe_data['date_time'])].reset_index(drop=True)
                wing_ce_data = wing_ce_data[wing_ce_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)

                wing_pe_data = wing_pe_data[wing_pe_data['date_time'].isin(wing_ce_data['date_time'])].reset_index(drop=True)
                wing_pe_data = wing_pe_data[wing_pe_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
                
                ce_data = ce_data[ce_data['date_time'].isin(wing_ce_data['date_time'])].reset_index(drop=True)
                pe_data = pe_data[pe_data['date_time'].isin(wing_pe_data['date_time'])].reset_index(drop=True)
                
                ce_data = ce_data.sort_values(by=['date_time'])
                pe_data = pe_data.sort_values(by=['date_time'])

                wing_ce_data = wing_ce_data.sort_values(by=['date_time'])
                wing_pe_data = wing_pe_data.sort_values(by=['date_time'])

                straddle_exit = ce_data.close.iloc[-1] + pe_data.close.iloc[-1]
                strangle_exit = wing_ce_data.close.iloc[-1] + wing_pe_data.close.iloc[-1]
                
                strangle_open = ce_wing_price + pe_wing_price
                entry_price = straddle_open - (ce_wing_price + pe_wing_price)
                slipage = Cal_slipage(strangle_open + straddle_open)
                slipage_price = entry_price - slipage
                exit_price = straddle_exit - strangle_exit
                pnl = slipage_price - exit_price
                log.loc[len(log.index)] = [frame_start_dt.date(), frame_start_dt.day_name() , frame_end_dt.date(), frame_end_dt.day_name() , start_time, end_time, straddle_entry_time.time() ,pe_scrip[:-2],ce_price, pe_price, straddle_open, straddle_exit, ce_wing, pe_wing, ce_wing_price, pe_wing_price, strangle_open, strangle_exit, entry_price, exit_price, pnl ]
                
            log.to_csv(output_csv_path + index + ' IFW ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SD-' + str(SD) + ' ' + str(trading_day) + '.csv', index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            msg = 'Error in row ' + str(row) + ": \n" + str(e) + "\n" + "Parameter : \n" + index + ' IFW ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SD' + str(SD) + ' ' + str(trading_day)
            print(e)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
print('END')
