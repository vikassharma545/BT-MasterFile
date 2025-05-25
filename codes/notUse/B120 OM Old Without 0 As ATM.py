import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import pandas as pd
import datetime
import pickle
import requests
import os
import shutil
import json
from glob import glob

pickle_path = "C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/"
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
parameter = parameter.fillna('')
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].str.split('-').map(lambda x: "-".join(x[::-1]))
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
        return gap
    except :
        return 0

def OHLC_SL(ftime, fdataframe, entry_f, fsl, flag):
    fdata = fdataframe.copy()

    if flag:
        fdata = fdata[fdata.date_time >= ftime]
        try:
            entry_f = fdata.close.iloc[0]
            sl_price_f = ((100 + fsl)/100) * entry_f
            fdata = fdata[1:]
        except:
            pass
    else:
        fdata = fdata[fdata.date_time > ftime]
        sl_price_f = ((100 + fsl)/100) * entry_f
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
            return entry_f, high_f, low_f, exit_f, sl_price_f, sl_flag,sl_time, pnl
        else:
            return high_f, low_f, exit_f, sl_price_f, sl_flag, sl_time, pnl
    except:
        if flag:
            return '', '', '', '', '', '','', 0
        else:
            return '', '', '', '', False, end_dt_1m, 0

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
            
            return ce_scrip, pe_scrip, ce_entry, pe_entry, start_dt, future_price, target
        except:
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
            ut_end_time = parameter.loc[row,'ut_end_time']
            if ut_end_time:
                ut_end_time = pd.to_datetime(ut_end_time.replace(' ', '')[0:5], format="%H:%M").time()
            sl = parameter.loc[row,'sl']
            ut_sl = parameter.loc[row,'ut_sl']
            options_multiplier = parameter.loc[row,'options_multiplier']
            slipage_var = parameter.loc[row, 'slipage']
            slipage_var /= 100

            print(f"Running Row : {row}  {index}  B120 OM  {day}  {str(start_time).replace(':','')[:4]}  {str(end_time).replace(':','')[:4]}  SL-{sl}  UTSL-{ut_sl}  {' OM-{0:.2f}'.format(options_multiplier)}")

            log = pd.DataFrame(columns =('Date/Day/Future/Expiry.Day/Start.Time/End.Time/Target/CE.Strike/CE.Open/CE.High/CE.Low/CE.Close/CE.SL.Price/CE.SL.Flag/CE.SL.Time/CE.PNL/PE.Strike/PE.Open/PE.High/PE.Low/PE.Close/PE.SL.Price/PE.SL.Flag/PE.SL.Time/PE.PNL/UT.Strike/UT.Open/UT.High/UT.Low/UT.Close/UT.SL.Price/UT.SL.Flag/UT.SL.Time/BPL/TT PL at SL/UT PL at SL/UT PL/Total PNL').split('/'))

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
                    future_data = pd.read_pickle(''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))).set_index(['date_time'])
                    options = pd.read_pickle(''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path)))
                    options_data = options.set_index(['date_time', 'scrip'])
                except:
                    from_date += datetime.timedelta(days=1)
                    continue

                if index in ['FINNIFTY', 'MIDCPNIFTY']:
                    gap = get_gap(options)

                if options_data.dte.iloc[0] == 0:
                    exp_day = 'TRUE'
                else:
                    exp_day = 'FALSE'
                        
                if day != dte.loc[str(from_date.date()), index]:
                    from_date += datetime.timedelta(days=1)
                    continue

                start_dt = datetime.datetime.combine(from_date, start_time)
                end_dt = datetime.datetime.combine(from_date, end_time)
                end_dt_1m = end_dt + datetime.timedelta(minutes=10)
                current_end_time = end_dt.time()
                if ut_end_time:
                    ut_end_dt = datetime.datetime.combine(from_date, ut_end_time)
                else:
                    ut_end_dt = end_dt

                options = options[options['date_time'] <= end_dt]

                ce_scrip, pe_scrip, ce_entry, pe_entry, start_dt, future_price, target = strangle_strike(start_dt)

                if ce_scrip == None:
                    from_date += datetime.timedelta(days=1)
                    continue

                entry_reference_time = start_dt

                ce_data = options[options.scrip == ce_scrip]
                ce_high, ce_low, ce_exit, ce_sl_price, ce_sl_trigger, ce_sl_time, ce_pnl = OHLC_SL(start_dt, ce_data, ce_entry, sl, False)

                pe_data = options[options.scrip == pe_scrip]
                pe_high, pe_low, pe_exit, pe_sl_price, pe_sl_trigger, pe_sl_time, pe_pnl = OHLC_SL(start_dt, pe_data, pe_entry, sl, False)

                ut_scrip, ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, ut_pnl = '', '', '', '', '', '', False, '', 0
                B_PL, TT_PL_at_SL, UT_PL_at_SL = 0,0,0

                if ce_sl_time < pe_sl_time:
                    ut_scrip = pe_scrip
                    
                    if ce_sl_time < ut_end_dt:
                        pe_data = pe_data[pe_data['date_time'] <= ut_end_dt]
                        ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, ut_pnl = OHLC_SL(ce_sl_time, pe_data, None, ut_sl, True)
                        current_end_time = ut_end_dt.time()
                    else:
                        ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, ut_pnl = OHLC_SL(ce_sl_time, pe_data, None, ut_sl, True)

                    if ut_open != '':
                        TT_PL_at_SL = ce_pnl
                        UT_PL_at_SL = pe_entry - ut_open - Cal_slipage(pe_entry)
                elif pe_sl_time < ce_sl_time:
                    ut_scrip = ce_scrip
                    
                    if pe_sl_time < ut_end_dt:
                        ce_data = ce_data[ce_data['date_time'] <= ut_end_dt]
                        ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, ut_pnl = OHLC_SL(pe_sl_time, ce_data, None, ut_sl, True)
                        current_end_time = ut_end_dt.time()
                    else:
                        ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, ut_pnl = OHLC_SL(pe_sl_time, ce_data, None, ut_sl, True)

                    if ut_open != '':
                        TT_PL_at_SL = pe_pnl
                        UT_PL_at_SL = ce_entry - ut_open - Cal_slipage(ce_entry)
                else:
                    if ce_sl_time == end_dt_1m:
                        B_PL = ce_pnl + pe_pnl
                        ce_sl_time , pe_sl_time = '', ''
                    else:
                        print('Rare Case call and put hit same time', from_date)

                if ut_sl_time == end_dt_1m:
                    ut_sl_time = ''
                if ce_sl_time == end_dt_1m:
                    ce_sl_time = ''
                if pe_sl_time == end_dt_1m:
                    pe_sl_time = ''

                total_pnl = B_PL + TT_PL_at_SL + UT_PL_at_SL + ut_pnl

                print(from_date)
                log.loc[len(log.index)] = [str(from_date)[0:10], from_date.day_name(), future_price, exp_day, entry_reference_time.time(), current_end_time, target, ce_scrip, ce_entry, ce_high, ce_low, ce_exit, ce_sl_price, ce_sl_trigger, ce_sl_time, ce_pnl, pe_scrip, pe_entry, pe_high, pe_low, pe_exit, pe_sl_price, pe_sl_trigger, pe_sl_time, pe_pnl, ut_scrip, ut_open, ut_high, ut_low, ut_close, ut_sl_price, ut_sl_trigger, ut_sl_time, B_PL, TT_PL_at_SL, UT_PL_at_SL, ut_pnl, total_pnl ]
                from_date += datetime.timedelta(days=1)

            log.to_csv (output_csv_path + f"{index} B120 OM {day} {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} SL-{sl} UTSL-{ut_sl} {' OM-{0:.2f}'.format(options_multiplier)}.csv", index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            msg = f"Error in row {row} : \n {e} \nParameter : \n {index} B120 OM {day} {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} SL-{sl} UTSL-{ut_sl} {' OM-{0:.2f}'.format(options_multiplier)}"   
            try:
                print(msg, from_date)
                requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
            except Exception as e:
                print(e)
            from_date += datetime.timedelta(days=1)
    
print('END')
