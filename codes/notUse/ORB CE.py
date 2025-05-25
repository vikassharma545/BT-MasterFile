import sys, ctypes
CODE = sys.argv[0].split('\\')[-1].replace('.py', '')
ctypes.windll.kernel32.SetConsoleTitleW(CODE)

import shutil
import pandas as pd
import numpy as np
import os
import datetime
import sys
import time
import warnings
warnings.filterwarnings("ignore")
from IPython.display import clear_output
pd.set_option('display.max_columns', None)
import ctypes

#paths
pickle_path = 'C:/Users/admin/$$ Codes/$$ Data Model/PICKLE/'
parameter_path = f'../Parameter/{CODE}.csv'
output_csv_path = f'../Temp/{CODE}/'
parameter = pd.read_csv(parameter_path)
dte = pd.read_csv('../inbuilt/dte.csv')
# dte['Date'] = pd.to_datetime(dte['Date'], dayfirst=True)
# dte['Date'] = dte['Date'].dt.date
dte = dte.set_index('Date')

try:
    if not os.path.isdir(output_csv_path) and output_csv_path != '':
        os.mkdir(output_csv_path)
    else:
        shutil.rmtree(output_csv_path)
        os.mkdir(output_csv_path)
except Exception as e:
    print("dir already exist!!")

# pkl file reader 
def file_reader(index,from_date):
    global pickle_path
    if index.lower().strip()=='banknifty':
        ind='BN'
    elif index.lower().strip()=='nifty':
        ind='Nifty'
    elif index.lower().strip()=='midcpnifty':
        ind='MCN'
    else:
        ind='FN'
    #future and options
    future=pd.read_pickle(f"{pickle_path}{ind} Future/{str(from_date)}_{str(index).lower()}_future.pkl")
    options=pd.read_pickle(f"{pickle_path}{ind} Options/{str(from_date)}_{str(index).lower()}.pkl")  
    return future,options

def gap_calc(df):
    x = df.scrip.str[:-2].astype(int).unique()
    x.sort()
    
    mid = int(len(x) / 2)
    gap = x[mid+1] - x[mid]
    
    if gap > 100 and index == "FINNIFTY":
        return 100
    if gap > 50 and index == "MIDCPNIFTY":
        return 50
    return gap

def strangle_calculator(future, options, start_t, end_t, target = None):
    try:
        gap = gap_calc(options)
    except :
        return None, None, None, None, None, None
    #filter with start time
    future = future.loc[start_t:]
    options = options.loc[start_t:]
    
    while start_t < end_t:
        try:
            future_price = future.loc[start_t, 'close']
            
            if target == None:
                target = (int(future_price/step) * step) / 100 * om
            
            new_options = options[options.close > target].reset_index()
            new_options = new_options.sort_values(by=['date_time', 'close'])
            new_options = new_options.set_index('date_time')

            #Get First CE & PE Scrip from options data
            ce_scrip = new_options[new_options.scrip.str.contains('CE')].scrip.iloc[0]
            pe_scrip = new_options[new_options.scrip.str.contains('PE')].scrip.iloc[0]

            #Making list of the ce_scrips and pe_scrips
            ce_scrip_list = [ce_scrip, ce_scrip, ce_scrip, str(int(ce_scrip[:-2])-gap)+'CE', str(int(ce_scrip[:-2])+gap)+'CE']
            pe_scrip_list = [pe_scrip, str(int(pe_scrip[:-2])-gap)+'PE', str(int(pe_scrip[:-2])+gap)+'PE', pe_scrip, pe_scrip]

            ce_prices = []
            pe_prices = []

            for i in range(0,5):
                try:
                    ce_prices.append(options[options.scrip == ce_scrip_list[i]].loc[start_t].close)
                except:
                    ce_prices.append(0)
                try:
                    pe_prices.append(options[options.scrip == pe_scrip_list[i]].loc[start_t].close)
                except:
                    pe_prices.append(0)

            sum_ce_pe = [ce_prices[i] + pe_prices[i] for i in range(5)]
            diff = [abs(ce_prices[i] - pe_prices[i]) for i in range(5)]

            result_index = None
            min_diff = float('inf')

            for i in range(0, 5):
                if sum_ce_pe[i] >= target * 2 and diff[i] < min_diff:
                    result_idx = i 
                    min_diff = diff[i]

            ce_scrip, pe_scrip = ce_scrip_list[result_idx], pe_scrip_list[result_idx]
            ce_open = options[options.scrip == ce_scrip].loc[start_t].close
            pe_open = options[options.scrip == pe_scrip].loc[start_t].close
            
            return future_price, ce_scrip, pe_scrip, ce_open, pe_open, start_t

        except Exception as e :
#             print("Error in STRANGLE_CALCULATOR function in line no :",sys.exc_info()[-1].tb_lineno,type(e).__name__,e)
            start_t += datetime.timedelta(minutes = 1)
            continue
            
    return None, None, None, None, None, None

def straddle_calculator(ft,ot,start,end):
    new_s=start
    opts=ot
    while new_s<=end:
        try:
            futr=ft
            #getting futr prices
            future_price=futr.loc[new_s]
            
            #unq strikes
            unq_strikes=opts[(opts.index>=new_s)&(opts.index<=end)]['scrip'].str[:-2].astype(float).unique()
            
            #let's get
            strad=unq_strikes[np.argmin(list(map(lambda x:abs(x-future_price.close),unq_strikes)))]
            
            # float scrip  can cause error
            if str(strad)[str(strad).index('.')+1:]=='0':
                future_price['straddle']=[str(int(strad))+'PE',str(int(strad))+'CE']
                strike=int(future_price.straddle[0][:-2])
            else:
                future_price['straddle']=[str(strad)+'PE',str(strad)+'CE']
                strike=float(future_price.straddle[0][:-2])
            
            #ce and pe
            ce=opts[opts['scrip']==future_price.straddle[1]]
            pe=opts[opts['scrip']==future_price.straddle[0]]
            
            #ce and pe 
            ce=ce.loc[future_price.name:]
            pe=pe.loc[future_price.name:]
            
            #pe close and ce close
            pe_open=pe.loc[future_price.name].close
            ce_open=ce.loc[future_price.name].close          
            return future_price.close, f"{strike}CE", f"{strike}PE", ce_open, pe_open, new_s
        
        except Exception as e:
            new_s+=datetime.timedelta(minutes=1)
#           print(sys.exc_info()[-1].tb_lineno,e)
            continue
    return None, None, None, None, None, None

def SL_check(break_time, f_data, f_open) :
    
    if not break_time :
        return  False, '', 0
    
    else :
        
        if order_side == 'SELL':
            f_sl_price = f_open*(1+sl/100)
            f_exit = f_data.close.iloc[-1]

            f_data = f_data.loc[break_time:]

            #additional check: if sl hit at end time 
            if f_data.shape[0] == 0 :
                return False, '', 0
            try :
                f_sl_hit_time = f_data[f_data.high >= f_sl_price].iloc[0].name
                f_sl_hit = True
                PNL = (f_open - f_sl_price)
            except :
                f_sl_hit_time = ''
                f_sl_hit = False
                PNL = f_open - f_exit

            #deducting slipage
            PNL = PNL - (f_open * (1*slipage/100))

            return f_sl_hit, f_sl_hit_time, PNL 
        
        else : # if order_side == 'BUY'
            f_sl_price = f_open * (1 - sl/100)
            
            f_exit = f_data.close.iloc[-1]

            f_data = f_data.loc[break_time:]
            
            #additional check: if sl hit at end time 
            if f_data.shape[0] == 0 :
                return False, '', 0
            
            try :
                f_sl_hit_time = f_data[f_data.low <= f_sl_price].iloc[0].name
                f_sl_hit = True
                PNL = (f_sl_price - f_open)
            except :
                f_sl_hit_time = ''
                f_sl_hit = False
                PNL = f_exit - f_open
                
            #deducting slipage
            PNL = PNL - (f_open * (1*slipage/100))

            return f_sl_hit, f_sl_hit_time, PNL
            
t1=time.time()
for row in range(parameter.shape[0]):
    if parameter.loc[row, 'run']:
        try:
            index = parameter.loc[row, 'index']
            day = parameter.loc[row,'day']
            start_date = parameter.loc[row, 'from_date']
            end_date = parameter.loc[row, 'to_date']
            start_time = parameter.loc[row, 'start_time']
            end_time = parameter.loc[row, 'end_time']
            om = parameter.loc[row, 'options_multiplier']
            gap = parameter.loc[row,'gap']
            order_side = parameter.loc[row,'type']
            slipage = parameter.loc[row,'slipage']
            sl = parameter.loc[row,'sl']
            
            # into datetime format
            start_date = pd.to_datetime(start_date, dayfirst=True).date()
            end_date = pd.to_datetime(end_date, dayfirst=True).date()
            start_time = pd.to_datetime(start_time).time()
            end_time = pd.to_datetime(end_time).time()
            
            #step
            if index.lower().strip()=='banknifty':
                step=5000
            elif index.lower().strip()=='nifty':
                step=1000
            else:
                step=1000
                
            #file name    
            file_name = f"{index} ORB {str(start_time).replace(':','')[:4]} {str(end_time).replace(':','')[:4]} {sl} {gap} {om} {order_side} {day}"
            
            print(f"RUNNING ROW :{file_name}")
            main = []  ### will append all our dictionery values
            
            
            while start_date <= end_date:
                try:
                    #reading options and future's pkl
                    future, options = file_reader(index, start_date)
                except:
                    start_date += datetime.timedelta(days=1)
                    continue
                
                future.set_index('date_time', inplace=True)
                options.set_index('date_time', inplace=True)
                    
                # start_dt and end_dt
                start_dt, end_dt = datetime.datetime.combine(start_date,start_time), datetime.datetime.combine(start_date,end_time) 
                
                # filtering with start_dt and end_dt
                future = future.sort_index().loc[start_dt:end_dt]
                options = options.sort_index().loc[start_dt:end_dt]
                
                # exception for diwali
                if future.shape[0] == 0 :
                    start_date += datetime.timedelta(days=1)
                    print("HAPPY DIWALI")
                    continue
                
                #expiry 
                expiry = True if options.dte.iloc[0] ==0 else False
                
                if day != dte.loc[str(start_date), index]:
                    start_date += datetime.timedelta(days=1)
                    continue
                
                #strike selections method based on OM given
                if om == 0:
                    strike_selection = straddle_calculator
                else :
                    strike_selection = strangle_calculator
                    
                # ce strike and pe strike
                future_price, ce_scrip, pe_scrip, ce_open, pe_open, start_dt = strike_selection(future, options, start_dt, end_dt)
                
                #if scrips not found
                if ce_scrip == None or pe_scrip == None:
                    start_date += datetime.timedelta(days = 1)
                    continue
                
                #ce data and pe_data
                ce_data = options[options.scrip == ce_scrip].loc[start_dt:]
                pe_data = options[options.scrip == pe_scrip].loc[start_dt:]
                
                #time gap
                time_gap = start_dt + datetime.timedelta(minutes = int(gap))
                
                #min and max between a time range
                pe_min = pe_data.loc[start_dt:time_gap].low.min()
                pe_max= pe_data.loc[start_dt:time_gap].high.max()

                ce_min = ce_data.loc[start_dt:time_gap].low.min()
                ce_max= ce_data.loc[start_dt:time_gap].high.max()
                
                
                #filter data again
                start_dt = time_gap
                pe_data = pe_data.loc[start_dt + datetime.timedelta(minutes = 1):]
                ce_data = ce_data.loc[start_dt + datetime.timedelta(minutes = 1):]
                
                
                #check low break
                if order_side == 'SELL' :
                    try :
                        pe_break_time = pe_data[pe_data.low <= pe_min].index[0]
                        pe_open = pe_min
                    except :
                        pe_break_time = ''

                    try :
                        ce_break_time= ce_data[ce_data.low <= ce_min].index[0]
                        ce_open = ce_min
                    except :
                        ce_break_time = ''
                else : # if order side == "BUY"
                    try :
                        pe_break_time = pe_data[pe_data.high >= pe_max].index[0]
                        pe_open = pe_max
                    except :
                        pe_break_time = ''

                    try :
                        ce_break_time= ce_data[ce_data.high >= ce_max].index[0]
                        ce_open = ce_max
                    except :
                        ce_break_time = ''
                    
                # CE SL hit check
                ce_sl_hit, ce_sl_hit_time, ce_pnl = SL_check(ce_break_time, ce_data, ce_open)
                
                # PE SL hit check
                pe_sl_hit, pe_sl_hit_time, pe_pnl = SL_check(pe_break_time, pe_data, pe_open)

                print(start_date)

                #append
                main.append((start_dt.date(), start_dt.strftime('%A'), expiry, start_time, future_price, ce_scrip,pe_scrip, ce_open, pe_open, ce_break_time, pe_break_time, ce_sl_hit, pe_sl_hit, ce_sl_hit_time, pe_sl_hit_time,ce_pnl,pe_pnl))
                
                # to next day
                start_date += datetime.timedelta(days=1)
            
            #to dataframe
            main = pd.DataFrame(main,columns = ['Date','Day','Expiry', 'Start_time', 'Future','CE_scrip','PE_scrip','CE_open','PE_open','CE_break_time','PE_break_time','CE_sl_hit','PE_sl_hit','CE_sl_hit_time','PE_sl_hit_time','CE_PNL','PE_PNL'])
            main['Total PNL'] = main['CE_PNL'] # + main['PE_PNL'] 
            #to_csv
            main.to_csv(f"{output_csv_path}\\{file_name}.csv",index = False)
            #udpating parameter values
            # parameter.loc[row,'run_dt'] = False
            #parameter to_csv
            # parameter.to_csv(parameter_path,index = False)
            
            clear_output(wait=True)
        except Exception as e :
            print(sys.exc_info()[-1].tb_lineno,type(e).__name__,e)
            
