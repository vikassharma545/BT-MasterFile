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

def OHLC_SL(ftime, frame_end_dt, fdataframe, fsl, slipage):
    fdata = fdataframe.copy()        
    fdata = fdata[fdata.date_time >= ftime]

    try:
        O = fdata.close.iloc[0]

        if slipage == '':
            slipage = Cal_slipage(O)

        C = fdata.close.iloc[-1]

        fdata = fdata.iloc[1:,:].reset_index(drop=True)
        H = fdata.high.max()
        L = fdata.low.min()

        sl_price = O + (O*(fsl/100))
        high_list = fdata.high.to_list()
        close_index_data = fdata.reset_index().groupby('dte',sort=False,as_index=False).first().iloc[1:,:]
        gap_time_list = close_index_data.date_time.to_list()
        gap_sl = False

        for i in range(len(close_index_data)):
            try:
                high_list[close_index_data.loc[i+1,'index']] = close_index_data.loc[i+1,'close']
            except:
                high_list[close_index_data.loc[i+1,'level_0']] = close_index_data.loc[i+1,'close']

        try:
            hit_value = [ele for ele in high_list if ele >= sl_price][0]
            sl_flag = True
            hit_index = high_list.index(hit_value)
            sl_time = fdata['date_time'].iloc[hit_index]
            pnl = round(O-sl_price,2)

            if sl_time in gap_time_list:
                gap_sl = True
                pnl = round(O-hit_value,2)

        except:
            sl_flag = False
            sl_time = frame_end_dt + datetime.timedelta(hours=1)
            pnl = round(O - C,2)

        # Slipage added 
        pnl = pnl - slipage
        
        return O,H,L,C,sl_flag,sl_time.date(),sl_time.time(),gap_sl,pnl,sl_price
    except:
        return None,None,None,None,None,None,None,None,None,None

def straddle_strike(start_dt, wkly_future, wkly_option, wkly_option_data, frame_end_dt):
    entry_time = start_dt.time()
    while (start_dt < frame_end_dt):
        try:
            #future price
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
            
            return ce_scrip, pe_scrip, start_dt, future_price            
        except:
            start_dt += datetime.timedelta(minutes = 1)
            if start_dt.time() == pd.Timestamp('09:15').time():
                start_dt = pd.Timestamp.combine(start_dt.date() + pd.Timedelta(days=1) , entry_time)
    
    return None, None, None, None            

# d = {'thursday':1, 'wednesday':2, 'tuesday':3, 'monday':4, 'friday':5}

for row in range(len(parameter)):
    if parameter['run'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', '').replace('/', '-'), format="%d-%m-%Y")
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', '')[0:5], format="%H:%M").time()
            ce_start_time = pd.to_datetime(parameter.loc[row,'ce_start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            pe_start_time = pd.to_datetime(parameter.loc[row, 'pe_start_time'].replace(' ', '')[0:5], format="%H:%M").time()
            ce_sl = parameter.loc[row,'ce_sl']
            pe_sl = parameter.loc[row, 'pe_sl']
            ce_trading_day = parameter.loc[row,'ce_entry']
            pe_trading_day = parameter.loc[row, 'pe_entry']
            slipage_var = parameter.loc[row, 'slipage']
            slipage_var /= 100
#             ce_trading_day = d[ce_day.lower()]
#             pe_trading_day = d[pe_day.lower()]

            print(f"Running Row : {row} {index} B120W {str(ce_start_time).replace(':','')[:-2]} {str(pe_start_time).replace(':','')[:-2]} {str(end_time).replace(':','')[:-2]} {ce_sl} {pe_sl} {ce_trading_day} {pe_trading_day}")

            log = pd.DataFrame(columns=('CE.Start.Date/CE.Trading.Day/PE.Start.Date/PE.Trading.Day/End.Date/End.Time/StrikeCE/CE.Open/CE.High/CE.Low/CE.Close/StrikePE/PE.Open/PE.High/PE.Low/PE.Close/CE.SL.Trigg/CE.Gap.SL/CE.SL.Date/CE.SL.Time/PE.SL.Trigg/PE.Gap.SL/PE.SL.Date/PE.SL.Time/B120.CE/B120.PE/Total PNL').split('/'))
            
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
                ce_weekly_future = pd.DataFrame()
                ce_weekly_options = pd.DataFrame()
                pe_weekly_future = pd.DataFrame()
                pe_weekly_options = pd.DataFrame()

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
                
                ce_future_week_list = future_week_list[-(ce_trading_day):] 
                ce_option_week_list = option_week_list[-(ce_trading_day):]
                pe_future_week_list = future_week_list[-(pe_trading_day):] 
                pe_option_week_list = option_week_list[-(pe_trading_day):]

                for i in range(len(ce_future_week_list)):
                    
                    future_data = pd.read_pickle(str(ce_future_week_list[i]))
                    options = pd.read_pickle(str(ce_option_week_list[i]))
                    
                    ce_weekly_future = pd.concat([ce_weekly_future,future_data], ignore_index=True)
                    ce_weekly_options = pd.concat([ce_weekly_options,options], ignore_index=True)
  
                for i in range(len(pe_future_week_list)):
                    
                    future_data = pd.read_pickle(str(pe_future_week_list[i]))
                    options = pd.read_pickle(str(pe_option_week_list[i]))
                    
                    pe_weekly_future = pd.concat([pe_weekly_future,future_data], ignore_index=True)
                    pe_weekly_options = pd.concat([pe_weekly_options,options], ignore_index=True)
    
                if ce_weekly_future.empty == True or pe_weekly_future.empty == True:
                    from_date += datetime.timedelta(days=1)
                    continue
                
                ce_weekly_future.sort_values(by='date_time',inplace=True)
                ce_weekly_future.set_index('date_time', inplace=True)
                ce_weekly_options.sort_values(by=['date_time','close'], inplace=True)
                ce_frame_start_dt = pd.Timestamp.combine(ce_weekly_options['date_time'].iloc[0], ce_start_time)
                ce_frame_end_dt = pd.Timestamp.combine(ce_weekly_options['date_time'].iloc[-1], end_time)
                ce_weekly_options = ce_weekly_options[(ce_weekly_options['date_time'] >= ce_frame_start_dt) & (ce_weekly_options['date_time'] <= ce_frame_end_dt)]
                ce_weekly_options_data = ce_weekly_options.set_index(['date_time', 'scrip'])
                
                pe_weekly_future.sort_values(by='date_time',inplace=True)
                pe_weekly_future.set_index('date_time', inplace=True)
                pe_weekly_options.sort_values(by=['date_time','close'], inplace=True)
                pe_frame_start_dt = pd.Timestamp.combine(pe_weekly_options['date_time'].iloc[0], pe_start_time)
                pe_frame_end_dt = pd.Timestamp.combine(pe_weekly_options['date_time'].iloc[-1], end_time)
                pe_weekly_options = pe_weekly_options[(pe_weekly_options['date_time'] >= pe_frame_start_dt) & (pe_weekly_options['date_time'] <= pe_frame_end_dt)]
                pe_weekly_options_data = pe_weekly_options.set_index(['date_time', 'scrip'])

                if index in ['FINNIFTY', 'MIDCPNIFTY']:
                    gap = get_gap(options)
                
                ce_scrip, t_pe_scrip, ce_frame_start_dt, t_future_price = straddle_strike(ce_frame_start_dt,ce_weekly_future,ce_weekly_options,ce_weekly_options_data, ce_frame_end_dt)
                t_ce_scrip, pe_scrip, pe_frame_start_dt, t_future_price = straddle_strike(pe_frame_start_dt,pe_weekly_future,pe_weekly_options,pe_weekly_options_data, pe_frame_end_dt)
                
                del(t_ce_scrip, t_pe_scrip, t_future_price)
                
                if ce_scrip == None:
                    continue
                
                ce_data = ce_weekly_options[ce_weekly_options.scrip == ce_scrip].reset_index(drop = True)
                pe_data = pe_weekly_options[pe_weekly_options.scrip == pe_scrip].reset_index(drop = True)

                ce_open, ce_high, ce_low, ce_close, ce_sl_trigger, ce_sl_date, ce_sl_time, ce_gap_sl, ce_pnl, ce_sl_price = OHLC_SL(ce_frame_start_dt, ce_frame_end_dt, ce_data, ce_sl, '')
                pe_open, pe_high, pe_low, pe_close, pe_sl_trigger, pe_sl_date, pe_sl_time, pe_gap_sl, pe_pnl, pe_sl_price = OHLC_SL(pe_frame_start_dt, pe_frame_end_dt, pe_data, pe_sl, '')
                
                if ce_open == None:
                    continue
                    
                if pe_open == None:
                    continue
                
                total_pnl = ce_pnl + pe_pnl
                    
                print(ce_frame_start_dt, pe_frame_start_dt,ce_frame_end_dt)
                log.loc[len(log.index)] = [ce_frame_start_dt, ce_frame_start_dt.day_name(), pe_frame_start_dt, pe_frame_start_dt.day_name(), ce_frame_end_dt.date(), ce_frame_end_dt.time() ,ce_scrip, ce_open, ce_high, ce_low, ce_close, pe_scrip, pe_open, pe_high, pe_low, pe_close, ce_sl_trigger, ce_gap_sl, ce_sl_date, ce_sl_time , pe_sl_trigger, pe_gap_sl, pe_sl_date, pe_sl_time, ce_pnl, pe_pnl, total_pnl]

            log.to_csv(output_csv_path+f"{index} B120W {str(ce_start_time).replace(':','')[:-2]} {str(pe_start_time).replace(':','')[:-2]} {str(end_time).replace(':','')[:-2]} {ce_sl} {pe_sl} {ce_trading_day} {pe_trading_day}.csv", index=False)
            
            t2 = datetime.datetime.now()
            print(t2 - t1)
        except Exception as e:
            msg = f"Error in row {row}\n {e}\nParameter:\n {index} B120W {str(ce_start_time).replace(':','')[:-2]} {str(pe_start_time).replace(':','')[:-2]} {str(end_time).replace(':','')[:-2]} {ce_sl} {pe_sl} {ce_trading_day} {pe_trading_day}"
            print(msg)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
            
print('END')
