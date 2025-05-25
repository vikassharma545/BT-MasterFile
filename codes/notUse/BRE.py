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

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
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

def OHLC_SL(fdataframe, entry_f, sl_price_f):
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]
    
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
            sl_time = ''
            sl_flag = False
            pnl = round(entry_f - exit_f, 2)

        return high_f, low_f, exit_f, sl_flag,sl_time, pnl
    except:
        return '', '', '', '', '', 0

def high_SL(ftime, fdataframe, entry, exit, sl_price):
    fdata = fdataframe.copy()
    
    slipage = Cal_slipage(entry)
    entry = entry - slipage

    fdata = fdata[fdata.date_time > ftime]
    fdata = fdata[fdata.high >= sl_price]

    try:
        sl_time = fdata.date_time.iloc[0]
        sl_flag = True
        pnl = round(entry - sl_price ,2)
    except:
        sl_flag = False
        sl_time = ''
        pnl = round(entry - exit ,2)

    return sl_flag,sl_time,pnl

def low_SL(ftime,fdataframe,O):
    fdata = fdataframe.copy()

    fdata = fdata[fdata.date_time > ftime]
    fdata = fdata[fdata.low <= O]

    try:
        low_time = fdata.date_time.iloc[0]
        low_flag = 1
    except:
        low_time = ''
        low_flag = 0

    return low_flag, low_time

def find_strike(start_dt):
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
            sl = parameter.loc[row,'sl']
            options_multiplier = parameter.loc[row,'options_multiplier']
            re_entries = int(parameter.loc[row,'re_entry'])
            re_sl = parameter.loc[row,'re_sl']
            slipage_var = parameter.loc[row, 'slipage']
            slipage_var /= 100

            print('Running Row :', str(row), index + ' BRE ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SL-' + str(sl) + ' RE-SL-' + str(re_sl) + ' ' + '{0:.2f}'.format(options_multiplier))

            s, t, u = [], [], []
            for w in range(re_entries+1):
                s.append(f'PL{w}.CE')
                t.append(f'PL{w}.PE')
                u.append(f'PL{w}')

            col =('Date/Day/Future/Expiry.Day/Time/Target/StrikeCE/CE Open/CE High/CE Low/CE Close/StrikePE/PE Open/PE High/PE Low/PE Close').split('/') + s + t + u + ['Total PNL']
            log = pd.DataFrame(columns = col)

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

                start_dt = datetime.datetime.combine(from_date, start_time)
                end_dt = datetime.datetime.combine(from_date, end_time)

                options = options[options['date_time'] <= end_dt]

                if options_data.dte.iloc[0] == 0:
                    exp_day = 'TRUE'
                else:
                    exp_day = 'FALSE'
                    
                if day != dte.loc[str(from_date.date()), index]:
                    from_date += datetime.timedelta(days=1)
                    continue

                for i in range(1, re_entries+1):
                    vars()['ce_re_entry_trigger_' + str(i)] = 0
                    vars()['ce_re_entry_time_' + str(i)] = ''
                    vars()['pe_re_entry_trigger_' + str(i)] = 0 
                    vars()['pe_re_entry_time_' + str(i)] = ''


                for i in range(0, re_entries+1):
                    vars()['ce_pnl_' + str(i)] = 0
                    vars()['ce_sl_trigger_' + str(i)] = 0
                    vars()['pe_pnl_' + str(i)] = 0
                    vars()['pe_sl_trigger_' + str(i)] = 0
                    vars()['ce_sl_time_' + str(i)] = ''
                    vars()['pe_sl_time_' + str(i)] = ''
                    vars()['pl_' + str(i)] = ''

                ce_scrip, pe_scrip, ce_entry, pe_entry, start_dt, future_price, target = find_strike(start_dt)

                if ce_scrip == None:
                    from_date += datetime.timedelta(days=1)
                    continue

                entry_reference_time = start_dt

                current_od = options[options['date_time'] >= start_dt]
                ce_data = current_od[current_od.scrip == ce_scrip]
                pe_data = current_od[current_od.scrip == pe_scrip]

                #call
                ce_sl_price = ((100 + sl)/100) * ce_entry
                ce_high, ce_low, ce_exit, ce_sl_trigger_0, ce_sl_time_0, ce_pnl_0 = OHLC_SL(ce_data,ce_entry,ce_sl_price)

                ce_sl_price = ((100 + re_sl)/100) * ce_entry
                # call re_entry
                re_entry_time = ce_sl_time_0
                for i in range(1, re_entries+1):
                    if type(re_entry_time) == str:
                        break
                    else:
                        vars()['ce_re_entry_trigger_' + str(i)], vars()['ce_re_entry_time_' + str(i)] = low_SL(re_entry_time,ce_data,ce_entry)
                        if vars()['ce_re_entry_trigger_' + str(i)] == 1:
                            vars()['ce_sl_trigger_' + str(i)], vars()['ce_sl_time_' + str(i)], vars()['ce_pnl_' + str(i)] = high_SL(vars()['ce_re_entry_time_' + str(i)], ce_data, ce_entry, ce_exit, ce_sl_price)
                            re_entry_time = vars()['ce_sl_time_' + str(i)]
                        else:
                            break

                #put
                pe_sl_price = ((100 + sl)/100) * pe_entry
                pe_high, pe_low, pe_exit, pe_sl_trigger_0, pe_sl_time_0, pe_pnl_0 = OHLC_SL(pe_data,pe_entry,pe_sl_price)

                pe_sl_price = ((100 + re_sl)/100) * pe_entry
                #put re_entry
                re_entry_time = pe_sl_time_0
                for i in range(1, re_entries+1):
                    if type(re_entry_time) == str:
                        break
                    else:
                        vars()['pe_re_entry_trigger_' + str(i)], vars()['pe_re_entry_time_' + str(i)] = low_SL(re_entry_time,pe_data,pe_entry)                        
                        if vars()['pe_re_entry_trigger_' + str(i)] == 1:
                            vars()['pe_sl_trigger_' + str(i)], vars()['pe_sl_time_' + str(i)], vars()['pe_pnl_' + str(i)] = high_SL(vars()['pe_re_entry_time_' + str(i)], pe_data, pe_entry, pe_exit, pe_sl_price)
                            re_entry_time = vars()['pe_sl_time_' + str(i)]
                        else:
                            break

                total_pl = 0
                for m in range(0, re_entries+1):
                    vars()['pl_' + str(m)] = round(vars()['ce_pnl_' + str(m)] + vars()['pe_pnl_' + str(m)], 2)
                    total_pl += vars()['pl_' + str(m)]

                s, t, u = [], [], []
                for w in range(re_entries+1):
                    s.append(round(vars()['ce_pnl_' + str(w)], 2))
                    t.append(round(vars()['pe_pnl_' + str(w)], 2))
                    u.append(vars()['pl_'+str(w)])

                print(from_date)
                log.loc[len(log.index)] = [str(from_date)[0:10] ,from_date.day_name() , future_price, exp_day, entry_reference_time.time(), target, ce_scrip[:-2], ce_entry, ce_high, ce_low, ce_exit, pe_scrip[:-2], pe_entry, pe_high, pe_low, pe_exit] + s + t + u + [total_pl]
                from_date += datetime.timedelta(days=1)

            log.to_csv (output_csv_path + index + ' BRE ' + str(day) + ' ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SL-' + str(sl) + ' RE-SL-' + str(re_sl) + ' ' + '{0:.2f}'.format(options_multiplier) + '.csv', index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)
        except Exception as e:
            msg = 'Error in row ' + str(row) + ": \n" + str(e) + "\n" + "Parameter : \n" + index + ' BRE ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' SL-' + str(sl) + ' RE-SL-' + str(re_sl) + ' ' + '{0:.2f}'.format(options_multiplier)
            print(msg)
            try:
                requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
            except:
                pass
            from_date += datetime.timedelta(days=1)

print('END')
