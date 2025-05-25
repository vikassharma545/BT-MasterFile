import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import os
import datetime
import requests
import pandas as pd
import shutil

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'

parameter = pd.read_csv(parameter_path)
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
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

def find_my_retime(start_dt, ce_scrip, pe_scrip, straddle_open_0):
    while start_dt < end_dt:
        try:
            ce_price = options_data.loc[(start_dt, ce_scrip),'close']
            pe_price = options_data.loc[(start_dt, pe_scrip),'close']

            if (ce_price + pe_price) <= straddle_open_0:
                return ce_scrip, pe_scrip, ce_price, pe_price, None, start_dt

            start_dt += datetime.timedelta(minutes = 1)
        except:
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None

def find_sl(ce_scrip, pe_scrip, start_dt, ce_close, pe_close):
   
    start_dt += datetime.timedelta(minutes=1)
    straddle_open_f = ce_close + pe_close
    slipage = Cal_slipage(straddle_open_f)
    
    ce_sl_price = ce_close * (1 + (straddle_sl/100))
    pe_sl_price = pe_close * (1 + (straddle_sl/100))

    ce_data = options.loc[(options['scrip'] == ce_scrip) & (options['date_time'] >= start_dt) , :]
    pe_data = options.loc[(options['scrip'] == pe_scrip) & (options['date_time'] >= start_dt) , :]

    ce_data = ce_data[ce_data['date_time'].isin(pe_data['date_time'])].reset_index(drop=True)
    pe_data = pe_data[pe_data['date_time'].isin(ce_data['date_time'])].reset_index(drop=True)
    
    ce_data = ce_data.sort_values(by=['date_time'])
    pe_data = pe_data.sort_values(by=['date_time'])
    
    try:
        straddle_exit_f = (ce_data['close'].iloc[-1] + pe_data['close'].iloc[-1])
    except:
        straddle_exit_f = straddle_open_f
    
    ce_high_list = ce_data.high.to_list()
    pe_high_list = pe_data.high.to_list()

    call_hit = False
    call_SL_time = end_dt + datetime.timedelta(hours = 1)
    try:
        call_hit_value = [ele for ele in ce_high_list if ele >= ce_sl_price][0]
        call_hit = True
        call_index = ce_high_list.index(call_hit_value)
        call_SL_time = ce_data['date_time'].iloc[call_index]
        pe_sl_close = pe_data['close'].iloc[call_index]
    except:
        pass
   
    put_hit = False
    put_SL_time = end_dt + datetime.timedelta(hours = 1)
    try:
        put_hit_value = [ele for ele in pe_high_list if ele >= pe_sl_price][0]
        put_hit = True
        put_index = pe_high_list.index(put_hit_value)
        put_SL_time = ce_data['date_time'].iloc[put_index]
        ce_sl_close = ce_data['close'].iloc[put_index]
    except:
        pass
   
    if (call_hit == False) & (put_hit == False):
        straddle_pnl = straddle_open_f - straddle_exit_f - slipage
        return False,'', straddle_pnl
   
    if call_SL_time < put_SL_time:
        straddle_sl_time = call_SL_time
        straddle_pnl = straddle_open_f - (ce_sl_price + pe_sl_close) - slipage       
    elif put_SL_time < call_SL_time:
        straddle_sl_time = put_SL_time
        straddle_pnl = straddle_open_f - (pe_sl_price + ce_sl_close) - slipage
    else:
        if call_SL_time == end_dt + datetime.timedelta(hours = 1):
            straddle_pnl = straddle_open_f - straddle_exit_f - slipage
            return False,'', straddle_pnl
        else:
            straddle_sl_time = call_SL_time
            straddle_pnl = straddle_open_f - (pe_sl_close + ce_sl_close) - slipage
   
    return True, straddle_sl_time, straddle_pnl

for row_idx in range(len(parameter)):
    if parameter.loc[row_idx,'run'] == True:
        
        try:
            t1 = datetime.datetime.now()
            day = parameter.loc[row_idx, 'day']
            index = parameter.loc[row_idx,'index']

            try:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d-%m-%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d-%m-%Y")
            except:
                from_date = pd.to_datetime(parameter.loc[row_idx,'from_date'].replace(' ', ''), format="%d/%m/%Y")
                to_date = pd.to_datetime(parameter.loc[row_idx,'to_date'].replace(' ', ''), format="%d/%m/%Y")

            start_time = pd.to_datetime(parameter.loc[row_idx,'start_time'].replace(' ', ''), format="%H:%M").time()
            end_time = pd.to_datetime(parameter.loc[row_idx,'end_time'].replace(' ', ''), format="%H:%M").time()
            
            straddle_sl = parameter.loc[row_idx,'straddle_sl']
            options_multiplier = parameter.loc[row_idx,'options_multiplier']
            re_straddle = parameter.loc[row_idx,'re_straddle']
            re_entries = int(parameter.loc[row_idx, 're_entry'])

            if options_multiplier == 0:
                file_name = f"{index} SRE SLS {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} {re_entries} SL-{straddle_sl} OM-{options_multiplier} RESTD-{re_straddle} {day}"
            else:
                options_multiplier = float(options_multiplier)
                file_name = f"{index} SRE SLS {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} {re_entries} SL-{straddle_sl} OM-{options_multiplier:.2f} RESTD-{re_straddle} {day}"

            print(file_name)
            
            col = ""
            for c in range(10+1):
                col += f"/ST{c}/ST{c}.O/ST{c}.SL.Trigg/ST{c}.SL.Time/ST{c}.PL"
                
            log = pd.DataFrame(columns=('Date/Day/DTE/Expiry.Day/Time/Future' + col).split('/') + ['Total PNL'])

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
                slipage = 0.015
            if index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                step = 1000
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
                    
                    # options data below end time
                    options = options[options['date_time'] <= end_dt]

                    for i in range(0, 10+1):
                        vars()['straddle_strike_' + str(i)] = ''
                        vars()['ce_close_' + str(i)] = 0
                        vars()['pe_close_' + str(i)] = 0
                        vars()['straddle_open_' + str(i)] = ''
                        vars()['straddle_sl_trigger_' + str(i)] = False
                        vars()['straddle_sl_time_' + str(i)] = ''
                        vars()['straddle_pl_' + str(i)] = 0

                    #straddle 0
                    if options_multiplier == 0:
                        ce_scrip, pe_scrip, ce_close_0, pe_close_0, initial_future_price, start_dt = find_my_straddle(start_dt)
                    else:
                        ce_scrip, pe_scrip, ce_close_0, pe_close_0, initial_future_price, start_dt = find_my_strangle(start_dt, options_multiplier)

                    if ce_scrip == None:
                        from_date += datetime.timedelta(days=1)
                        continue

                    straddle_open_0 = ce_close_0 + pe_close_0
                    straddle_strike_0 = (ce_scrip, pe_scrip)
                    entry_reference_time = start_dt
                    straddle_sl_trigger_0, straddle_sl_time_0, straddle_pl_0 = find_sl(ce_scrip, pe_scrip, start_dt, ce_close_0, pe_close_0)
                    
                    re_entrie_flag = True
                    if (straddle_sl_trigger_0 == False):
                        re_entrie_flag = False
                    else:
                        if (straddle_sl_time_0 == end_dt):
                            re_entrie_flag = False

                    for z in range(1, re_entries+1):
                        if re_entrie_flag == False:
                            break
                        else:
                            if re_straddle == "SAME":
                                ce_scrip, pe_scrip, vars()['ce_close_' + str(z)], vars()['pe_close_' + str(z)], future_price, start_dt = find_my_retime(vars()['straddle_sl_time_' + str(z - 1)], ce_scrip, pe_scrip, straddle_open_0)
                            elif re_straddle == "NEW":
                                if options_multiplier == 0:
                                    ce_scrip, pe_scrip, vars()['ce_close_' + str(z)], vars()['pe_close_' + str(z)], future_price, start_dt = find_my_straddle(vars()['straddle_sl_time_' + str(z - 1)])
                                else:
                                    ce_scrip, pe_scrip, vars()['ce_close_' + str(z)], vars()['pe_close_' + str(z)], future_price, start_dt = find_my_strangle(vars()['straddle_sl_time_' + str(z - 1)], options_multiplier)
                                    
                            if ce_scrip is None:
                                break

                            vars()['straddle_strike_' + str(z)] = (ce_scrip, pe_scrip)
                            vars()['straddle_open_' + str(z)] = vars()['ce_close_' + str(z)] + vars()['pe_close_' + str(z)]
                            vars()['straddle_sl_trigger_' + str(z)] , vars()['straddle_sl_time_' + str(z)], vars()['straddle_pl_' + str(z)] = find_sl(ce_scrip, pe_scrip, start_dt, vars()['ce_close_' + str(z)], vars()['pe_close_' + str(z)])

                            if (vars()['straddle_sl_trigger_' + str(z)] == False):
                                re_entrie_flag = False
                            else:
                                if (vars()['straddle_sl_time_' + str(z)] == end_dt):
                                    re_entrie_flag = False

                    l1 = []
                    total_pnl = 0
                    for i in range(0, 10+1):
                        l1.append(vars()['straddle_strike_' + str(i)])
                        l1.append(vars()['straddle_open_' + str(i)])
                        l1.append(vars()['straddle_sl_trigger_' + str(i)])
                        if type(vars()['straddle_sl_time_' + str(i)]) != str:
                            vars()['straddle_sl_time_' + str(i)] =  vars()['straddle_sl_time_' + str(i)].time()
                        l1.append(vars()['straddle_sl_time_' + str(i)])
                        l1.append(vars()['straddle_pl_' + str(i)])
                        total_pnl += vars()['straddle_pl_' + str(i)]
                    
                    print(from_date)
                    log.loc[len(log.index)] = [str(from_date)[0:10], from_date.day_name(), dte, exp_day, entry_reference_time.time(), initial_future_price] + l1 + [total_pnl]
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