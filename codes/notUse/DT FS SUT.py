import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import pandas as pd
import numpy as np
import datetime
import requests
import os
import shutil

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
dte = dte.set_index('Date')

if not os.path.isdir(output_csv_path):
    os.mkdir(output_csv_path)
else:
    shutil.rmtree(output_csv_path)
    os.mkdir(output_csv_path)

def Cal_slipage(open_price):
    return open_price * slipage

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
    
def Check_Rentry(ftime, fdataframe, decay_price):
    fdata = fdataframe.copy()

    fdata = fdata[fdata.date_time > ftime]
    fdata = fdata[fdata.low <= decay_price]

    try:
        low_time = fdata.date_time.iloc[0]
        low_flag = True
    except:
        low_time = end_dt + datetime.timedelta(minutes=60)
        low_flag = False

    return low_flag, low_time

def OHLC_SL(fdata, entry_time, entry_f, sl_price_f):
    fdata = fdata.copy()
    fdata = fdata[fdata.date_time > entry_time]
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

def find_my_straddle(start_dt):
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
            
            return ce_scrip, pe_scrip, start_dt, ce_price, pe_price, future_price , syn_future
        except:
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None, None

for row in range(len(parameter)):
    if parameter['run'].iloc[row] == True:
        try:
            t1 = datetime.datetime.now()
            day = parameter.loc[row,'day']
            index = parameter.loc[row,'index']
            from_date = pd.to_datetime(parameter.loc[row,'from_date'].replace(' ', ''), format="%d-%m-%Y")
            to_date = pd.to_datetime(parameter.loc[row,'to_date'].replace(' ', ''), format="%d-%m-%Y")
            start_time = pd.to_datetime(parameter.loc[row,'start_time'].replace(' ', ''), format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row,'end_time'].replace(' ', ''), format="%H:%M").time()
            fs_sl = parameter.loc[row,'fs_sl']
            decay = parameter.loc[row,'dt_trigger']
            options_multiplier = parameter.loc[row,'options_multiplier']
            straddle_sl = parameter.loc[row,'straddle_sl']
            straddle_ut_sl = parameter.loc[row,'ut_sl']
            ut_multiplier = parameter.loc[row,'ut_options_multiplier']

            print('Running Row :', row , index + ' DT_FS_SUT ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(fs_sl) + ' ' + str(decay) + ' ' + '{0:.2f}'.format(options_multiplier) + ' ' + str(straddle_sl) + ' ' + str(straddle_ut_sl) + ' ' + '{0:.2f}'.format(ut_multiplier) )
            
            file_name = output_csv_path + index + ' DT_FS_SUT ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(fs_sl) + ' ' + str(decay) + ' ' + '{0:.2f}'.format(options_multiplier) + ' ' + str(straddle_sl) + ' ' + str(straddle_ut_sl) + ' ' + str(ut_multiplier) + '.csv'
            
            if os.path.exists(file_name):
                continue
            
            log = pd.DataFrame(columns=('Date/Day/Future/Expiry.Day/DT.Start.Time/DT.Target/DT.Signal/DT.Decay.Price/DT.Decay.Time/DT.SL.Price/DT.SL.Flag/DT.SL.Time/DT_FS.PNL/Sut_sync_future/Straddle.Strike/Sut_call.price/Sut_put.price/Straddle.Open/Straddle.SL.Time/UT.Target/UT.strike/UT.Open/UT.High/UT.Low/UT.Close/Straddle.PNL/UT.PNL/Total PNL').split('/'))
            
            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                gap = 100
                step = 5000
                slipage = 0.0125
            elif index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                gap = None
                step = 1000
                slipage = 0.015
            elif index == "NIFTY":
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                gap = 50
                step = 1000
                slipage = 0.01
            elif index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                gap = None
                step = 1000
                slipage = 0.0125

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

                dt_ce_scrip, dt_pe_scrip, dt_ce_entry, dt_pe_entry, start_dt, dt_future_price, dt_target = strangle_strike(start_dt)
                
                if dt_ce_scrip == None:
                    from_date += datetime.timedelta(days=1)
                    continue
                                        
                dt_strike_time = start_dt
                dt_ce_decay_price = dt_ce_entry * decay
                dt_pe_decay_price = dt_pe_entry * decay
                dt_ce_sl_price = dt_ce_decay_price * (1+(fs_sl/100))
                dt_pe_sl_price = dt_pe_decay_price * (1+(fs_sl/100))
                
                dt_ce_data = options[options.scrip == dt_ce_scrip]                
                dt_ce_entry_flag, dt_ce_entry_time = Check_Rentry(dt_strike_time, dt_ce_data, dt_ce_decay_price)
                
                dt_pe_data = options[options.scrip == dt_pe_scrip]
                dt_pe_entry_flag, dt_pe_entry_time = Check_Rentry(dt_strike_time, dt_pe_data, dt_pe_decay_price)
                                                
                if dt_ce_entry_time < dt_pe_entry_time:
                    dt_signal = 'CALL'
                    dt_signal_time = dt_ce_entry_time
                elif dt_ce_entry_time > dt_pe_entry_time:
                    dt_signal= 'PUT'
                    dt_signal_time = dt_pe_entry_time
                else:
                    dt_signal = ''
                    
                dt_fs_high, _dt_fs_low, dt_fs_exit, dt_fs_sl_flag, dt_fs_sl_time, dt_fs_pnl = '', '', '', False, '', 0
                
                if dt_signal != '':
                    if dt_signal == 'CALL':
                        dt_fs_high, _dt_fs_low, dt_fs_exit, dt_fs_sl_flag, dt_fs_sl_time, dt_fs_pnl = OHLC_SL(dt_ce_data, dt_ce_entry_time, dt_ce_decay_price, dt_ce_sl_price)
                        dt_signal_decay_price = dt_ce_decay_price
                        dt_signal_sl_price = dt_ce_sl_price
                    else:
                        dt_fs_high, _dt_fs_low, dt_fs_exit, dt_fs_sl_flag, dt_fs_sl_time, dt_fs_pnl = OHLC_SL(dt_pe_data, dt_pe_entry_time, dt_pe_decay_price, dt_pe_sl_price)
                        dt_signal_decay_price = dt_pe_decay_price
                        dt_signal_sl_price = dt_pe_sl_price
                else:
                    from_date += datetime.timedelta(days=1)
                    continue
                    
                if dt_fs_sl_flag and dt_fs_sl_time < (end_dt - datetime.timedelta(minutes=5)):
                    
                    sut_sell_time = dt_fs_sl_time + datetime.timedelta(minutes=1)                    
                    sut_ce_scrip, sut_pe_scrip, start_dt, sut_ce_price, sut_pe_price, sut_future_price, sut_syn_future = find_my_straddle(sut_sell_time)
                    
                    if sut_ce_scrip is None:
                        from_date += datetime.timedelta(days=1)
                        continue
                        
                    straddle_strike = sut_ce_scrip[:-2]
                    straddle_open = sut_ce_price + sut_pe_price
                    straddle_slipage = Cal_slipage(straddle_open) 
                    straddle_entry_time = start_dt
                    
                    start_dt += datetime.timedelta(minutes=1)
                    
                    sut_ce_data = options.loc[(options['scrip'] == sut_ce_scrip) & (options['date_time'] >= start_dt), :]
                    sut_pe_data = options.loc[(options['scrip'] == sut_pe_scrip) & (options['date_time'] >= start_dt), :]

                    sut_ce_data = sut_ce_data[sut_ce_data['date_time'].isin(sut_pe_data['date_time'])].reset_index(drop=True)
                    sut_pe_data = sut_pe_data[sut_pe_data['date_time'].isin(sut_ce_data['date_time'])].reset_index(drop=True)

                    sut_ce_data = sut_ce_data.sort_values(by=['date_time'])
                    sut_pe_data = sut_pe_data.sort_values(by=['date_time'])
                    
                    if sut_ce_data.empty:
                        from_date += datetime.timedelta(days=1)
                        continue
                    
                    straddle_exit = sut_ce_data.close.iloc[-1] + sut_pe_data.close.iloc[-1]
                    
                    l3 = np.maximum(np.array(sut_ce_data.high + sut_pe_data.low), np.array(sut_ce_data.low + sut_pe_data.high)).tolist()

                    straddle_sl_time, sl_hit,sl_index = '',False,''
                    straddle_sl_price = straddle_open * (1 + (straddle_sl/100))

                    # if sl not hit i.e hit value is null throw error
                    try:
                        hit_value = [ele for ele in l3 if ele >= straddle_sl_price][0]
                        sl_hit = True
                        sl_index = l3.index(hit_value)
                        straddle_sl_time = sut_ce_data['date_time'].iloc[sl_index]
                    except:
                        pass
                                        
                    ut_target = (int(sut_future_price/step) * step) / 100 * ut_multiplier 
                    raw_ut_open, ut_scrip, ut_open, ut_high, ut_low, ut_close, ut_pl = '','','','','','',0

                    # enter in ut part if stoploss hit and its time is less then 5 min of end time
                    if (sl_hit == True):

                        straddle_pl = -straddle_open*(straddle_sl/100)
                        straddle_pl = straddle_pl - straddle_slipage
                        pl = straddle_pl

                        if (straddle_sl_time <= (end_dt - pd.Timedelta(minutes=5))):

                            # new future price at sl time
                            for i in range(10):
                                try:
                                    new_future_price = future_data.loc[straddle_sl_time + datetime.timedelta(minutes = i), 'close']
                                    straddle_sl_time = straddle_sl_time + datetime.timedelta(minutes = i)
                                    break
                                except:
                                    pass

                            if index != "FINNIFTY":
                                if new_future_price >= sut_future_price:
                                    signal = 'PE'
                                else:
                                    signal = 'CE'
                            else:
                                current_ce_price = sut_ce_data["close"].iloc[sl_index]
                                current_pe_price = sut_pe_data["close"].iloc[sl_index]
                                ce_inc_rate = current_ce_price / sut_ce_price * 100
                                pe_inc_rate = current_pe_price / sut_pe_price * 100
                                if ce_inc_rate > pe_inc_rate:
                                    signal = 'PE'
                                else:
                                    signal = 'CE'

                            current_od = options[options['date_time'] >= straddle_sl_time]
                            target_od = current_od[current_od['close'] > ut_target].sort_values(by = ['date_time', 'close'])

                            for i in range(len(target_od)):
                                if target_od['scrip'].iloc[i][-2:] == signal:
                                    ut_scrip = target_od.scrip.iloc[i]
                                    break

                            if ut_scrip != '':

                                # OHLC of ut 
                                ut_data = current_od[current_od['scrip'] == ut_scrip]
                                ut_open = ut_data['close'].iloc[0]
                                ut_slipage = Cal_slipage(ut_open)
                                ut_data = ut_data.iloc[1:]

                                # if ut data is empty error raise and pass
                                try:
                                    ut_high = ut_data['high'].max()
                                    ut_low = ut_data['low'].min()
                                    ut_close = ut_data['close'].iloc[-1]          

                                    if ut_high >= ut_open*(1+(straddle_ut_sl/100)):
                                        ut_pl = -ut_open*(straddle_ut_sl/100)
                                    else:
                                        ut_pl = ut_open - ut_close

                                    ut_pl = ut_pl - ut_slipage
                                except:
                                    pass

                                pl = straddle_pl + ut_pl
                    else:
                        straddle_pl = straddle_open - straddle_exit
                        straddle_pl = straddle_pl - straddle_slipage
                        pl = straddle_pl
                    
                    total_pl = pl + dt_fs_pnl   
                else:
                    sut_syn_future, straddle_strike, sut_ce_price, sut_pe_price, straddle_open, straddle_sl_time, ut_target, ut_scrip, ut_open, ut_high, ut_low, ut_close, straddle_pl, ut_pl = '', '', '', '', '', '', '', '', '', '', '', '', '', ''
                    total_pl = dt_fs_pnl
                    
                print(from_date)  
                log.loc[len(log.index)] = [str(from_date)[0:10], from_date.day_name(), dt_future_price, exp_day, dt_strike_time.time(), dt_target, dt_signal, dt_signal_decay_price, dt_signal_time, dt_signal_sl_price, dt_fs_sl_flag, dt_fs_sl_time, dt_fs_pnl, sut_syn_future, straddle_strike, sut_ce_price, sut_pe_price, straddle_open, straddle_sl_time, ut_target, ut_scrip, ut_open, ut_high, ut_low, ut_close, straddle_pl, ut_pl, total_pl]
                from_date += datetime.timedelta(days=1)
                
            log.to_csv(output_csv_path + index + ' DT_FS_SUT ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(fs_sl) + ' ' + str(decay) + ' ' + '{0:.2f}'.format(options_multiplier) + ' ' + str(straddle_sl) + ' ' + str(straddle_ut_sl) + ' ' + str(ut_multiplier) + '.csv', index = False)
            t2 = datetime.datetime.now()
            print(t2-t1)

        except Exception as e:
            msg = 'Error in row ' + str(row) + ": \n" + str(e) + "\n" + "Parameter : \n" + index + ' DT_FS_SUT ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + str(fs_sl) + ' ' + str(decay) + ' ' + '{0:.2f}'.format(options_multiplier) + ' ' + str(straddle_sl) + ' ' + str(straddle_ut_sl) + ' ' + str(ut_multiplier)   
            print(msg)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
print('END')