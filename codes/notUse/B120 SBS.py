import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import pandas as pd
import datetime 
import requests
import os
import shutil

pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
dte = dte.set_index('Date')

if not os.path.isdir(output_path) and output_path != '':
    os.mkdir(output_path)
else:
    shutil.rmtree(output_path)
    os.mkdir(output_path)

def Cal_slipage(open_price):
    return open_price * slipage_var

def get_gap(df):
    try:
        x = df.scrip.str[:-2].astype(int).unique()
        x.sort()
        
        mid = int(len(x) / 2)
        gap = x[mid+1] - x[mid]
        
        if gap > 100 and index == 'FINNIFTY':
            return 100
        if gap > 50 and index == 'MIDCPNIFTY':
            return 50
        return gap
    except Exception:
        return 0
    
def Sell_OHLC_SL(fdataframe, entry_f, sl_price_f):
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]
    
    try:
        high_f = fdata.high.max()
        low_f = fdata.low.min()
        exit_f = fdata.close.iloc[-1]

        temp = fdata[fdata.high >= sl_price_f]

        try:
            sl_time = temp.date_time.iloc[0]
            sl_flag = True
            pnl = -entry_f * (sell_sl - 1)
            pnl = round(pnl - Cal_slipage(entry_f), 2)
        except:
            sl_time, sl_flag = '', False
            pnl = entry_f - exit_f
            pnl = round(pnl - Cal_slipage(entry_f), 2)
        
        return sl_flag, sl_time, pnl
    except:
        return False, '', 0
    
def Buy_OHLC_SL(fdataframe, entry_f, sl_price_f):
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]
    
    try:
        high_f = fdata.high.max()
        low_f = fdata.low.min()
        exit_f = fdata.close.iloc[-1]

        temp = fdata[fdata.low <= sl_price_f]

        try:
            sl_time = temp.date_time.iloc[0]
            sl_flag = True
            pnl = -entry_f * (1 - buy_sl)
            pnl = round(pnl - Cal_slipage(entry_f), 2)
        except:
            sl_time, sl_flag = '', False
            pnl = exit_f - entry_f
            pnl = round(pnl - Cal_slipage(entry_f), 2)   
        
        return sl_flag, sl_time, pnl
    except:
        return False, '', 0
    
def Sell_OHLC_SL_trail(fdataframe,  entry_f, sl_price_f):
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]

    try:
        t_time = fdata.date_time.iloc[0]
        high_f = fdata.high.max()
        low_f = fdata.low.min()
        exit_f = fdata.close.iloc[-1]
        
        dec_val = entry_f * trail_pl_sell
        trail_price = entry_f - dec_val
        
        temp = fdata[((fdata.high >= sl_price_f ) | (fdata.low <= trail_price)) & (fdata.date_time >= t_time)]
        
        if temp.empty:
            sl_flag, sl_time = False, ''
            pnl = round(entry_f - exit_f - Cal_slipage(entry_f), 2)
        
        while(not(temp.empty)): 
            
            if(temp.high.iloc[0] >= sl_price_f):
                sl_flag = True
                sl_time = temp.date_time.iloc[0]
                pnl = round(entry_f - sl_price_f - Cal_slipage(entry_f), 2)
                break
            else:
                sl_price_f = sl_price_f - dec_val * trail_sl
                trail_price = trail_price - dec_val
                t_time = temp.date_time.iloc[0]
            
            temp = fdata[((fdata.high >= sl_price_f ) | (fdata.low <= trail_price)) & (fdata.date_time >= t_time)]
            
            if temp.empty:
                sl_flag, sl_time = False, ''
                pnl = round(entry_f - exit_f - Cal_slipage(entry_f), 2)
                break
            
        return sl_flag, sl_time, pnl
    except:
        return False, '', 0

def Buy_OHLC_SL_trail(fdataframe,  entry_f, sl_price_f):
    fdata = fdataframe.copy()
    fdata = fdata.iloc[1:]
    
    try:
        t_time = fdata.date_time.iloc[0]
        high_f = fdata.high.max()
        low_f = fdata.low.min()
        exit_f = fdata.close.iloc[-1]
        
        inc_val = entry_f * trail_pl_buy
        trail_price = entry_f + inc_val
        
        temp = fdata[((fdata.high >= trail_price) | (fdata.low <= sl_price_f)) & (fdata.date_time > t_time)]
        
        if temp.empty:
            sl_flag, sl_time = False, ''
            pnl = round(exit_f- entry_f - Cal_slipage(entry_f), 2)
    
        while(not(temp.empty)): 

            if(temp.low.iloc[0] <= sl_price_f):
                sl_flag = True
                sl_time = temp.date_time.iloc[0]
                pnl = round(sl_price_f - entry_f - Cal_slipage(entry_f), 2)
                break
            else:
                sl_price_f = sl_price_f + inc_val * trail_sl
                trail_price = trail_price + inc_val
                t_time = temp.date_time.iloc[0]
                
            temp = fdata[((fdata.high >= trail_price) | (fdata.low <= sl_price_f)) & (fdata.date_time > t_time)]
            
            if temp.empty:
                sl_flag, sl_time = False, ''
                pnl = round(exit_f- entry_f - Cal_slipage(entry_f), 2)
                break
            
        return sl_flag, sl_time, pnl
    except:
        return False, '', 0

def straddle_strike(start_dt):
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

            return ce_scrip, pe_scrip, ce_price, pe_price, start_dt, future_price, syn_future
        except Exception as e:
            start_dt += datetime.timedelta(minutes = 1)
            
    return None, None, None, None, None, None, None

def new_straddle_strike(new_start, signal, target):
    new_scrip, new_price, new_data = '', '', ''
   
    ce_scrip, pe_scrip, ce_price, pe_price, start_dt, _, _ = straddle_strike(new_start)
    
    if ce_scrip is not None:
        if signal == "PE":
            new_scrip, new_price = pe_scrip, pe_price
        elif signal == "CE":
            new_scrip, new_price = ce_scrip, ce_price

        if new_scrip != '':
            temp = current_od[current_od['date_time'] >= start_dt]
            new_data = temp[temp['scrip'] == new_scrip]

    return new_scrip, new_price, new_data

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

def new_strangle_strike(new_start, signal, target):
    new_scrip, new_price, new_data = '', '', ''
    
    temp = current_od[current_od['date_time'] >= new_start]
    target_od = temp[temp['close'] > target].sort_values(by = ['date_time', 'close'])

    for i in range(len(target_od)):
        if target_od['scrip'].iloc[i][-2:] == signal:
            new_scrip = target_od.scrip.iloc[i]
            new_price = target_od.close.iloc[i]
            break

    if(new_scrip != ''):
        new_data = temp[temp['scrip'] == new_scrip]

    return new_scrip, new_price, new_data

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
            p_buy_sl, p_sell_sl = parameter.loc[row, 'buy_sl'], parameter.loc[row, 'sell_sl']
            p_trail_pl_buy, p_trail_pl_sell = parameter.loc[row, 'trail_pl_buy'], parameter.loc[row, 'trail_pl_sell']
            p_trail_sl, options_multiplier = parameter.loc[row, 'trail_sl'], parameter.loc[row,'options_multiplier']
            
            if options_multiplier <= 0:
                find_strike = straddle_strike
                find_new_strike = new_straddle_strike
            else:
                find_strike = strangle_strike
                find_new_strike = new_strangle_strike

            data= []
                        
            buy_sl, sell_sl = (100 - p_buy_sl)/100, (100 + p_sell_sl)/100
            trail_pl_buy, trail_pl_sell = p_trail_pl_buy/100, p_trail_pl_sell/100
            trail_sl = p_trail_sl /100
            trail_op =  False if trail_pl_sell == 0 else True
            
            print(f'Running Row : {row} {index} B120SBS' + ' ' + str(start_time).replace(':','')[:4] + ' ' +str(end_time).replace(':','')[:4] + ' ' + f'B.SL {p_buy_sl} S.SL {p_sell_sl} Buy.T.PL {p_trail_pl_buy} Sell.T.PL {p_trail_pl_sell} T.SL {p_trail_sl} OM {options_multiplier:.2f}')
            
            if index == 'BANKNIFTY':
                future_folder_path = 'BN Future/'
                option_folder_path = 'BN Options/'
                future_file_path = '_banknifty_future.pkl'
                option_file_path = '_banknifty.pkl'
                gap = 100
                step = 5000
                slipage_var = 0.0125
            if index == 'FINNIFTY':
                future_folder_path = 'FN Future/'
                option_folder_path = 'FN Options/'
                future_file_path = '_finnifty_future.pkl'
                option_file_path = '_finnifty.pkl'
                gap = None
                step = 1000
                slipage_var = 0.0125
            if index == "NIFTY":
                future_folder_path = 'Nifty Future/'
                option_folder_path = 'Nifty Options/'
                future_file_path = '_nifty_future.pkl'
                option_file_path = '_nifty.pkl'
                gap = 50
                step = 1000
                slipage_var = 0.01
            if index == 'MIDCPNIFTY':
                future_folder_path = 'MCN Future/'
                option_folder_path = 'MCN Options/'
                future_file_path = '_midcpnifty_future.pkl'
                option_file_path = '_midcpnifty.pkl'
                gap = None
                step = 1000
                slipage_var = 0.0125

            while from_date <= to_date:
                d= []

                try:
                    future_data = pd.read_pickle(''.join((pickle_path,future_folder_path,str(from_date)[0:10],future_file_path))).set_index(['date_time'])
                    options = pd.read_pickle(''.join((pickle_path,option_folder_path,str(from_date)[0:10],option_file_path)))
                    options_data = options.set_index(['date_time', 'scrip'])
                except Exception as g:
                    from_date += datetime.timedelta(days=1)
                    continue
                
                if index in ['FINNIFTY', 'MIDCPNIFTY']:
                    gap = get_gap(options)
                
                start_dt = datetime.datetime.combine(from_date, start_time)
                end_dt = datetime.datetime.combine(from_date, end_time)

                options = options[options['date_time'] <= end_dt]
                
                exp_day = 'TRUE' if options_data.dte.iloc[0] == 0 else 'FALSE' 
                
                if day != dte.loc[str(from_date.date()), index]:
                    from_date += datetime.timedelta(days=1)
                    continue
                
                ce_scrip_sell, pe_scrip_sell, ce_entry_sell, pe_entry_sell, start_dt, future_price, target = find_strike(start_dt)
                
                if ce_scrip_sell == None:
                    from_date += datetime.timedelta(days=1)
                    continue
                
                entry_reference_time = start_dt
                d.extend((index, entry_reference_time.date(), from_date.day_name(), exp_day, entry_reference_time.time()))
                
                current_od = options[options['date_time'] >= start_dt]
                ce_data_sell = current_od[current_od.scrip == ce_scrip_sell]
                pe_data_sell = current_od[current_od.scrip == pe_scrip_sell]
                
                ce_sl_price_sell, pe_sl_price_sell = ce_entry_sell * sell_sl, pe_entry_sell * sell_sl
                
                original_ce_sl , original_pe_sl = ce_sl_price_sell, pe_sl_price_sell
                
                if(trail_op):
                    ce_sl_trigger_sell, ce_sl_time_sell, ce_pnl_sell = Sell_OHLC_SL_trail(ce_data_sell,ce_entry_sell,ce_sl_price_sell)
                    pe_sl_trigger_sell, pe_sl_time_sell, pe_pnl_sell = Sell_OHLC_SL_trail(pe_data_sell, pe_entry_sell, pe_sl_price_sell)                
                else:
                    ce_sl_trigger_sell, ce_sl_time_sell, ce_pnl_sell = Sell_OHLC_SL(ce_data_sell,ce_entry_sell,ce_sl_price_sell)
                    pe_sl_trigger_sell, pe_sl_time_sell, pe_pnl_sell = Sell_OHLC_SL(pe_data_sell, pe_entry_sell, pe_sl_price_sell)
                
                ce_scrip_buy, ce_entry_buy, ce_sl_trigger_buy, ce_sl_time_buy, ce_pnl_buy = '', '', '', '', 0
                pe_scrip_buy, pe_entry_buy, pe_sl_trigger_buy, pe_sl_time_buy, pe_pnl_buy = '', '', '', '', 0
                
                if(ce_sl_trigger_sell):
                    temp_data = ce_data_sell[(ce_data_sell.high >= original_ce_sl)]
                    
                    if(not(temp_data.empty)):
                        new_time = temp_data.date_time.iloc[0]
                        ce_scrip_buy, ce_entry_buy, ce_data_buy = find_new_strike(new_time, 'CE', target)
                    
                if(ce_scrip_buy != ''):
                    ce_sl_price_buy = ce_entry_buy * buy_sl
                    original_ce_sl = ce_sl_price_buy
                    
                    if(trail_op):
                        ce_sl_trigger_buy, ce_sl_time_buy, ce_pnl_buy = Buy_OHLC_SL_trail(ce_data_buy, ce_entry_buy, ce_sl_price_buy)
                    else:
                        ce_sl_trigger_buy, ce_sl_time_buy, ce_pnl_buy = Buy_OHLC_SL(ce_data_buy, ce_entry_buy, ce_sl_price_buy)
                    
                if(pe_sl_trigger_sell):
                    temp_data = pe_data_sell[(pe_data_sell.high >= original_pe_sl)]

                    if(not(temp_data.empty)):
                        new_time = temp_data.date_time.iloc[0]
                        pe_scrip_buy, pe_entry_buy, pe_data_buy = find_new_strike(new_time, 'PE', target)
                    
                if(pe_scrip_buy != ''):
                    pe_sl_price_buy = pe_entry_buy * buy_sl
                    original_pe_sl = pe_sl_price_buy

                    if(trail_op):
                        pe_sl_trigger_buy, pe_sl_time_buy, pe_pnl_buy = Buy_OHLC_SL_trail(pe_data_buy, pe_entry_buy, pe_sl_price_buy)
                    else:
                        pe_sl_trigger_buy, pe_sl_time_buy, pe_pnl_buy = Buy_OHLC_SL(pe_data_buy, pe_entry_buy, pe_sl_price_buy)
                
                ce_scrip_sell2, ce_entry_sell2, ce_sl_trigger_sell2, ce_sl_time_sell2, ce_pnl_sell2 = '', '', '', '', 0
                pe_scrip_sell2, pe_entry_sell2, pe_sl_trigger_sell2, pe_sl_time_sell2, pe_pnl_sell2 = '', '', '', '', 0
                
                
                if(ce_sl_trigger_buy):
                    temp_data = ce_data_buy[ce_data_buy.low <= original_ce_sl]
                    
                    if(not(temp_data.empty)):
                        new_time = temp_data.date_time.iloc[0]
                        ce_scrip_sell2, ce_entry_sell2, ce_data_sell2 = find_new_strike(ce_sl_time_buy, 'CE', target)
                    
                if(ce_scrip_sell2 != ''):
                    ce_sl_price_sell2 = ce_entry_sell2 * sell_sl

                    if(trail_op):
                        ce_sl_trigger_sell2, ce_sl_time_sell2, ce_pnl_sell2 = Sell_OHLC_SL_trail(ce_data_sell2, ce_entry_sell2, ce_sl_price_sell2)
                    else:
                        ce_sl_trigger_sell2, ce_sl_time_sell2, ce_pnl_sell2 = Sell_OHLC_SL(ce_data_sell2, ce_entry_sell2, ce_sl_price_sell2)
                
                if(pe_sl_trigger_buy):
                    temp_data = pe_data_buy[pe_data_buy.low <= original_pe_sl]

                    if(not(temp_data.empty)):
                        new_time = temp_data.date_time.iloc[0]
                        pe_scrip_sell2, pe_entry_sell2, pe_data_sell2 = find_new_strike(pe_sl_time_buy, 'PE', target)
        
                if(pe_scrip_sell2 != ''):
                    pe_sl_price_sell2 = pe_entry_sell2 * sell_sl

                    if(trail_op):
                        pe_sl_trigger_sell2, pe_sl_time_sell2, pe_pnl_sell2 = Sell_OHLC_SL_trail(pe_data_sell2, pe_entry_sell2, pe_sl_price_sell2)
                    else:
                        pe_sl_trigger_sell2, pe_sl_time_sell2, pe_pnl_sell2 = Sell_OHLC_SL(pe_data_sell2, pe_entry_sell2, pe_sl_price_sell2)
                
                ce_pnl = ce_pnl_sell + ce_pnl_buy + ce_pnl_sell2
                pe_pnl = pe_pnl_sell + pe_pnl_buy + pe_pnl_sell2
                total_pnl = ce_pnl + pe_pnl
                
                print(from_date)
                d.extend((future_price, target, ce_scrip_sell, ce_entry_sell, ce_sl_trigger_sell, ce_sl_time_sell, ce_pnl_sell, ce_scrip_buy, ce_entry_buy, ce_sl_trigger_buy, ce_sl_time_buy, ce_pnl_buy, ce_scrip_sell2, ce_entry_sell2, ce_sl_trigger_sell2, ce_sl_time_sell2, ce_pnl_sell2, pe_scrip_sell, pe_entry_sell, pe_sl_trigger_sell, pe_sl_time_sell, pe_pnl_sell, pe_scrip_buy, pe_entry_buy, pe_sl_trigger_buy, pe_sl_time_buy, pe_pnl_buy, pe_scrip_sell2, pe_entry_sell2, pe_sl_trigger_sell2, pe_sl_time_sell2, pe_pnl_sell2, ce_pnl, pe_pnl, total_pnl ))
                data.append(d)
                
                from_date += datetime.timedelta(days = 1)
                
            output = pd.DataFrame(data, columns = ['Index', 'Date', 'Day', 'Expiry', 'Time', 'Future', 'Target', 'C.Scrip.S', 'C.Open.S', 'C.Sl_hit.S', 'C.Sl_time.S', 'C.Pnl.S','C.Scrip.B', 'C.Open.B', 'C.Sl_hit.B', 'C.Sl_time.B', 'C.Pnl.B', 'C.Scrip.S2', 'C.Open.S2', 'C.Sl_hit.S2', 'C.Sl_time.S2', 'C.Pnl.S2', 'P.Scrip.S', 'P.Open.S', 'P.Sl_hit.S', 'P.Sl_time.S', 'P.Pnl.S','P.Scrip.B', 'P.Open.B', 'P.Sl_hit.B', 'P.Sl_time.B', 'P.Pnl.B', 'P.Scrip.S2', 'P.Open.S2', 'P.Sl_hit.S2', 'P.Sl_time.S2', 'P.Pnl.S2', 'Total CE PNL', 'Total PE PNL', 'Total PNL'])
            output.to_csv(output_path + index + ' B120SBS ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + f' {p_sell_sl} {p_buy_sl} {p_trail_pl_sell} {p_trail_pl_buy} {p_trail_sl} OM-{options_multiplier:.2f}.csv', index=False)

            t2 = datetime.datetime.now()
            print(t2-t1)

        except Exception as e:
            msg = 'Error in row ' + str(row) + ": \n" + str(e) + "\n" + "Parameter : \n" + index + ' B120SBS ' + str(start_time).replace(':','')[:4] + ' ' + str(end_time).replace(':','')[:4] + ' ' + f'B.SL {p_buy_sl} S.SL {p_sell_sl} Buy.T.PL {p_trail_pl_buy} Sell.T.PL {p_trail_pl_sell} T.SL {p_trail_sl} OM-{options_multiplier:.2f}'
            print(msg)
            requests.get(f'https://api.telegram.org/bot5156026417:AAExQbrMAPrV0qI8tSYplFDjZltLBzXTm1w/sendMessage?chat_id=-607631145&text={msg}')
            from_date += datetime.timedelta(days=1)

print('END')