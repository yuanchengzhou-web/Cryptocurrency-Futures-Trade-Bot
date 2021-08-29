import pandas as pd
import numpy as np
import talib
import time
from datetime import datetime, timedelta
from pyecharts import options as opts
from binance.enums import *
from binance.client import Client
from IPython.display import clear_output, display

### Connects to Binance 
client=Client(api_key = "YOUR API KEY" ,
              api_secret = "YOUR SCECRET KEY")


### The function of SAR technical indicator
def sar(acceleration, maximum):   
    low = []    ### create new lists of lowest & highest price to be used for SAR calculation by Talib
    high = []
    for i in range(len(kline_data_extract.close)):   ### Because Talib needs the data to be an array, so we have to put the highest
        low.append(kline_data_extract.low[i])        ### And Lowest data into the new lists created and made it into a dataframe so
        high.append(kline_data_extract.high[i])      ### it becomes an array.
    data = {"high":high,"low":low}   
    df = pd.DataFrame(data)
    tab_sar = talib.SAR(df['high'],df['low'],acceleration,maximum)
    
    list_sar = tab_sar.tolist()   ### The output from talib isn't a dataframe yet, so use .tolist() to make it into a dataframe
    return list_sar               

### The function of KDJ technical indicator
def kdj(kdj_length, k, d, ret):   
    RSV = []    ### create new lists to store values for calculation
    kvalue = []
    dvalue = []
    jvalue = []
    c = 1
                           ### Please checkout KDJ indicator formula.
    while c < k:        
        kvalue.append(50)    ### based on k and d period, we have to wait till the end of that period has reached 
        dvalue.append(50)    ### so we can start calculating the values, just like moving average.
        RSV.append(50)
        jvalue.append(3*kvalue[-1]-2*dvalue[-1])
        c = c + 1
    
    for j in range(k-1, len(kline_data_extract.close)):

        k_period_close = kline_data_extract.close[j-k+1:j+1]
        k_period_high = kline_data_extract.high[j-k+1:j+1]
        k_period_low = kline_data_extract.low[j-k+1:j+1]
 
        lowest = min(k_period_low)
        highest = max(k_period_high)
        if highest - lowest == 0:
            RSV.append(50)
        else:
            RSV.append(100*(kline_data_extract.close[j] - lowest)/(highest-lowest))
        kvalue.append(2/3*kvalue[j-1]+RSV[j]/3)
        dvalue.append(2/3*dvalue[j-1]+kvalue[j]/3)
        jvalue.append(3*kvalue[j]-2*dvalue[j]) 
    
    if ret == 'k':       ### based on the call in back_test function the KDJ fucntion will return different values
        return kvalue
    
    elif ret == 'd':
        return dvalue
    
    elif ret == 'j':
        return jvalue

### The function of Bollinger Bands technical indicator
def boll(boll_length, boll_multipler, boll_ret): 
    result: List[Union[float, str]] = []         ### Create new lists to store values for caluclation
    upper: List[Union[float, str]] = []          ### Please chechout BOLL formula
    lower: List[Union[float, str]] = []
    
    for i in range(len(kline_data_extract.close)):        
        if i < boll_length:                      ### Similiar as KDJ, where we have to wait untill the end of the 
            result.append("-")
            upper.append("-")
            lower.append("-")
            continue
        sum_total = 0.0
        close = []

        for j in range(boll_length):
            close.append(float(kline_data_extract.close[i - j]))
            sum_total += float(kline_data_extract.close[i - j])
        result.append(abs(float("%.6f" % (sum_total / boll_length))))
        std = np.std(close)
        upper.append(result[-1] + std*2)
        lower.append(result[-1] - std*2)
        
    if boll_ret == "sma":    ### Same as KDJ where BOLL function will return various results based on calls from back_test function
        return result
    elif boll_ret == "upper":
        return upper
    elif boll_ret == "lower":
        return lower


### The function to extract futures candlestick data from binance and to create down & up lists for profit sell and stop loss limits
def kline_data_extract(usdt_symbol, kdj_length, k, d, boll_length, boll_multipler, acceleration, maximum, get_data):
    
    dict_setup = {"time":[],"open":[], "high":[], "low":[], "close":[]}
    kline_data = []
    
    current_time = datetime.today()
    start_at = current_time - timedelta(minutes=15*60)
    start_at_mili = round(start_at.timestamp()*1000)
    start_at_mili
    
    klines = client.futures_klines(symbol = usdt_symbol, contractType = "PERPETUAL", 
                                   interval = Client.KLINE_INTERVAL_15MINUTE,startTime=start_at_mili)
    kline_data.append(klines)   ### store all the imported data into a list
    time.sleep(0.07)          


    for m in range(len(kline_data)):
        for l in range(len(kline_data[m])):
            raw_date = kline_data[m][l][0]
            close = float(kline_data[m][l][4])
            op = float(kline_data[m][l][1])
            high = float(kline_data[m][l][2])      ### This part is where the data will be stored into previously created empty
            low = float(kline_data[m][l][3])       ### dictionary in order to form a dataframe
            date = datetime.fromtimestamp(int(raw_date/1000))
            readable_date = date.strftime("%Y/%m/%d, %H:%M")
            dict_setup["time"].append(readable_date)
            dict_setup['open'].append(op)
            dict_setup['high'].append(high)
            dict_setup['low'].append(low)
            dict_setup['close'].append(close)

    kline_data_extract.close = dict_setup['close']
    kline_data_extract.high = dict_setup['high']
    kline_data_extract.low = dict_setup['low']

    dict_setup['k'] = kdj(kdj_length, k, d, 'k')           ### calling kdj, boll & sar data from the respective functions
    dict_setup['d'] = kdj(kdj_length, k, d, 'd')
    dict_setup['j'] = kdj(kdj_length, k, d, 'j')
    dict_setup['boll upper'] = boll(boll_length, boll_multipler, 'upper')
    dict_setup['boll lower'] = boll(boll_length, boll_multipler, 'lower')
    dict_setup['boll mid'] = boll(boll_length, boll_multipler, 'sma')
    dict_setup['sar'] = sar(acceleration, maximum)

    df = pd.DataFrame(dict_setup)
    df.sort_values('time',inplace=True,ascending=False)    ### creates a dataframe and sort the order from start datetime to 
    df.set_index('time',inplace=True)                     ### end datetime

    had = df     ### use the previously created dataframe and start from 20 because boll only begins to show data from 

    

    down_l = []            ### These are the variables for various conditions during backtest
    up_l = []
    
    
    for i in range(5,len(had)): 
        a = 60-i   
        ### Starts storing kline, technical values into down_l list where it only stores candles that is negative and has
        ### lower closing price than the previous candle in down_l consecutively.
        ### This starts the backtest where since trade type is "N/A" so no trade has happened yet, so starts storing data
        ### for technical indicators signals
        if had.iloc[a,0] > had.iloc[a,3] and len(down_l)== 0 and len(up_l) == 0 and had.iloc[a,10] >= had.iloc[a,1]:
            down_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,4],had.iloc[a,5],had.iloc[a,6],had.iloc[a,7],had.iloc[a,8],had.iloc[a,9]])
        
        elif had.iloc[a,0] < had.iloc[a,3] and len(down_l)== 0 and len(up_l) == 0 and had.iloc[a,2] >= had.iloc[a,10]:
            up_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,7],had.iloc[a,8],
                            had.iloc[a,9]])
            
        ### This part will avoid the situation where the kline data begins with positive candles because
        ### without negative candles going down for a period of time, this strategy can not figure out
        ### whether it is time to buy in, such as buy the dip
        if had.iloc[a,0] > had.iloc[a,3] and len(down_l) == 0 and len(up_l) != 0 and had.iloc[a,10] >= had.iloc[a,1]:
            up_l = []
            down_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,4],had.iloc[a,5],had.iloc[a,6],had.iloc[a,7],had.iloc[a,8],had.iloc[a,9]])

        ### This part will continue to store negative candles after the backtest started to simulate trade.
        elif had.iloc[a,0] > had.iloc[a,3] and len(down_l) != 0 and len(up_l) == 0 and had.iloc[a,10] >= had.iloc[a,1]:
            if had.iloc[a,3] < down_l[-1][3]:
                down_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,4],had.iloc[a,5],had.iloc[a,6],had.iloc[a,7],had.iloc[a,8],had.iloc[a,9]])
        
        elif had.iloc[a,0] > had.iloc[a,3] and len(down_l) != 0 and len(up_l) != 0 and had.iloc[a,10] >= had.iloc[a,1]:
            up_l = []
            down_l = []
            
            down_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,4],had.iloc[a,5],had.iloc[a,6],had.iloc[a,7],had.iloc[a,8],had.iloc[a,9]])
        
        if had.iloc[a,0] < had.iloc[a,3] and len(up_l) == 0 and had.iloc[a,2] >= had.iloc[a,10]:
            up_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,7],had.iloc[a,8],
                            had.iloc[a,9]])
        
        elif had.iloc[a,0] < had.iloc[a,3] and len(up_l) != 0 and had.iloc[a,2] >= had.iloc[a,10]:
            if had.iloc[a,3] > up_l[-1][3]:
                up_l.append([had.iloc[a,0],had.iloc[a,1],had.iloc[a,2],had.iloc[a,3],had.iloc[a,7],had.iloc[a,8],
                            had.iloc[a,9]])

        ### This part will check which border of BOLL did the last 3 negative candles in down_l have touched
        ### so the backtest can buy in by looking where which border of BOLL did down_l candles crossed.
        if len(down_l) != 0:
            check_pass_mid1 = 0
            check_oversell1 = 0
            check_pass_upper1 = 0
            
            if len(down_l) < 3:
                for s1 in range(len(down_l)):
                    if down_l[s1][9] != '-' and down_l[s1][8] != '-' and down_l[s1][7] != '-':
                        if down_l[s1][3] < down_l[s1][8]:
                            check_oversell1 = 1
                            check_pass_mid1 = 1
                            check_pass_upper1 = 1
                            
                        elif down_l[s1][3] < down_l[s1][9] and down_l[s1][3] >= down_l[s1][8]:
                            check_pass_mid1 = 1
                            check_pass_upper1 = 1
                            
                        elif down_l[s1][3] < down_l[s1][7] and down_l[s1][3] >= down_l[s1][9]:
                            check_pass_upper1 = 1
                            

            elif len(down_l) >= 3:
                for s1 in range(len(down_l)-3,len(down_l)):
                    if down_l[s1][9] != '-' and down_l[s1][8] != '-' and down_l[s1][7] != '-':
                        if down_l[s1][3] < down_l[s1][8]:
                            check_oversell1 = 1
                            check_pass_mid1 = 1
                            check_pass_upper1 = 1
                            
                        elif down_l[s1][3] < down_l[s1][9] and down_l[s1][3] >= down_l[s1][8]:
                            check_pass_mid1 = 1
                            check_pass_upper1 = 1
                            
                        elif down_l[s1][3] < down_l[s1][7] and down_l[s1][3] >= down_l[s1][9]:
                            check_pass_upper1 = 1
                            
    
    if get_data == 'down':
        return down_l
    elif get_data == 'up':
        return up_l
    elif get_data == 'df':
        return had
    elif get_data == 'check upper':
        if len(down_l) != 0:
            return check_pass_upper1
        else:
            return 'N/A'
    elif get_data == 'check mid':
        if len(down_l) != 0:
            return check_pass_mid1
        else:
            return 'N/A'
    elif get_data == 'check oversell':
        if len(down_l) != 0:
            return check_oversell1
        else:
            return 'N/A'


### The trade bot function that will use all the functions above for trade signal
def trade_bot(kdj_length, k, d, boll_length, boll_multipler, acceleration, maximum,
              usdt_symbol,buy_qty_pct = 0.7,profit1=1.5, profit2=2.0, profit3=2.8, profit4=3.8, 
              stop_loss_force=0.015, stop_loss_pct=1.5, final_stop_loss=0.07,leverage_level=1):
    
    sos = {'Symbol':[], 'Total Realized Gain/Loss %':[], 'Average Realized Gain/Loss %':[], 
           'Positive Liquidation Average % Gain':[], 'Negative Liquidation Average % Loss':[], 'Positive Liquidation Probability':[]}
    
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    client.futures_change_leverage(symbol = usdt_symbol, leverage = leverage_level)
    begin_balance = float(client.futures_account_balance()[1]['balance'])
    
    running = True
    refresh_data = 0
    initial_refresh = 1
    
    last_trade_type = 'Sell'
    remaining_qty = 0
    buy_ID = 0
    buy_lock = 0
    buy_price = 0
    profit_sell_qty_4 = 0
    profit_sell_qty_3 = 0
    profit_sell_qty_2 = 0
    profit_sell_qty_1 = 0
    
    while running == True:
        
        current_time = datetime.today()
        current_minute = current_time.minute
        current_time_str = current_time.strftime("%Y/%m/%d, %H:%M")
        current_time_datetime = datetime.strptime(current_time_str, "%Y/%m/%d, %H:%M")
        
        candles_30 = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "df")
        
        market_price = float(client.futures_mark_price(symbol=usdt_symbol)['markPrice'])
        
        buy_quantity = round((begin_balance*buy_qty_pct)/candles_30.iloc[0][3],0)
        
        time_left = current_time_datetime - datetime.strptime(candles_30.index[1], "%Y/%m/%d, %H:%M")
        
        time_left_minute = 30 - int((time_left.seconds)/60)
        
        twenty_history_data = candles_30.loc[candles_30.index[1]:candles_30.index[21]]
        twenty_history_sum_chg_pct = 0
        for t in range(len(twenty_history_data.index)):
            twenty_history_sum_chg_pct += np.absolute((twenty_history_data.iloc[t,1] - twenty_history_data.iloc[t,2])/
                                           twenty_history_data.iloc[t,2])
        avg_thcp = twenty_history_sum_chg_pct / len(twenty_history_data.index)
        
        if (current_minute == (0 or 15 or 30 or 45) and refresh_data == 1) or initial_refresh == 1:
            
            down_l = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "down")
        
            up_l = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "up")
            
            below_boll_upper = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "check upper")
            
            below_boll_mid = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "check mid")
            
            below_boll_lower = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum, get_data = "check oversell")
            
            intial_refresh = 0
            
            if refresh_data == 1:
                refresh_data = 0
        
        elif current_minute != (0 or 15 or 30 or 45) and refresh_data == 0 and initial_refresh == 0:
            refresh_data = 1
        
        if len(up_l) == 0 and buy_lock == 1:
            buy_lock = 0
        
        clear_output(wait=True) 
        print("THE TRADE BOT IS RUNNING!")
        print("MARKET PRICE:",market_price)
        print("THE AVERAGE AMPLITUDE",round(avg_thcp*100,3),"%")
        print("TIME TILL NEXT CANDLE",time_left_minute,"MINUTES")
        display(candles_30.head(5))
        ### This is the buy in part where backtest will use the conditions set on 
        ### the technical indicators and various requirements to decide whether to buy or not.
        ### If buy in, this part will create an up_l list storing the positive candles higher than the previous one 
        ### consecutively for profit sell conditions.
        ### This part will also create trade data in had_calc_df dataframe for gain/loss calculation.
        if len(down_l) != 0 and candles_30.iloc[0,0] < candles_30.iloc[0,3] and buy_lock == 0 and candles_30.iloc[0,2] >= candles_30.iloc[0,10] and \
        ((candles_30.iloc[0,4] > candles_30.iloc[0,5] and time_left_minute < 14) or (candles_30.iloc[0,3] - candles_30.iloc[0,0])/candles_30.iloc[0,0] > avg_thcp*1.5) and \
        last_trade_type == 'Sell':

            if below_boll_mid == 1 or below_boll_upper == 1 or below_boll_lower == 1:
                
                long = client.futures_create_order(
                            symbol=usdt_symbol,
                            side=SIDE_BUY,
                            positionSide='LONG',
                            type=ORDER_TYPE_MARKET,
                            quantity=buy_quantity)
                
                remaining_qty = buy_quantity
                buy_ID = long['orderId']
                last_trade_type = 'Buy'
                down_l = []

        elif len(up_l) != 0 and last_trade_type == ("Buy" or "Profit Sell"):
            ### this calculates the average % change of the canldes in up_l list for a general understanding of how
            ### much avg % u currently have gained and to secure profit before price dropping down
            
            buy_price = float(client.futures_get_order(symbol=usdt_symbol, orderId = buy_ID)['avgPrice'])
            
            sum_up_chg_pct = 0 
            for u in range(len(up_l)):
                sum_up_chg_pct += (up_l[u][1] - up_l[u][2])/up_l[u][2]
            avg_up_chg_pct = sum_up_chg_pct / len(up_l)

            ### this part will setup values to secure profit when the current closing price have reached 
            ### specified limits
            if candles_30.iloc[0,2] >= candles_30.iloc[0,10] and market_price > buy_price and (market_price - buy_price)/buy_price >= avg_thcp*profit4:
                
                sell_price = buy_price + buy_price*avg_thcp*profit4
                profit_sell_qty_4 = buy_quantity -  profit_sell_qty_1 - profit_sell_qty_2 - profit_sell_qty_3
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    price = sell_price,
                    positionSide='LONG',
                    type=ORDER_TYPE_LIMIT,
                    timeInFORCE = 'GTC',
                    quantity=profit_sell_qty_4)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                remaining_qty = 0
                last_trade_type = 'Sell'
                profit_sell_qty_4 = 0
                profit_sell_qty_3 = 0
                profit_sell_qty_2 = 0
                profit_sell_qty_1 = 0
                buy_lock = 1

            elif candles_30.iloc[0,2] >= candles_30.iloc[0,10] and market_price > buy_price and (market_price - buy_price)/buy_price >= avg_thcp*profit3:
                
                sell_price = buy_price + buy_price*avg_thcp*profit3
                if profit_sell_qty_1 == 0 and profit_sell_qty_2 == 0:
                    profit_sell_qty_3 = round(buy_quantity*0.75,0)
                
                elif profit_sell_qty_1 != 0 and profit_sell_qty_2 == 0:
                    profit_sell_qty_3 = buy_quantity - profit_sell_qty_1 - round(buy_quantity/2,0)
                
                elif profit_sell_qty_1 == 0 and profit_sell_qty_2 != 0:
                    profit_sell_qty_3 = buy_quantity - profit_sell_qty_2 - round(buy_quantity/4,0)
                    
                elif profit_sell_qty_1 != 0 and profit_sell_qty_2 != 0:
                    profit_sell_qty_3 = buy_quantity - profit_sell_qty_1 - profit_sell_qty_2
                
                    client.futures_create_order(
                        symbol = usdt_symbol,
                        side=SIDE_SELL,
                        price = sell_price,
                        positionSide='LONG',
                        type=ORDER_TYPE_LIMIT,
                        timeInFORCE = 'GTC',
                        quantity=profit_sell_qty_3)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Profit Sell"
                remaining_qty = buy_quantity - profit_sell_qty_3
                
            elif candles_30.iloc[0,2] >= candles_30.iloc[0,10] and market_price > buy_price and (market_price - buy_price)/buy_price >= avg_thcp*profit2:
                
                sell_price = buy_price + buy_price*avg_thcp*profit2
                if profit_sell_qty_1 == 0:
                    profit_sell_qty_2 = buy_quantity - round(buy_quantity/2,0)
                
                elif profit_sell_qty_1 != 0:
                    profit_sell_qty_2 = buy_quantity - profit_sell_qty_1 - round(buy_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    price = sell_price,
                    positionSide='LONG',
                    type=ORDER_TYPE_LIMIT,
                    timeInFORCE = 'GTC',
                    quantity=profit_sell_qty_2)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Profit Sell"
                remaining_qty = buy_quantity - profit_sell_qty_2
                
            elif candles_30.iloc[0,2] >= candles_30.iloc[0,10] and market_price > buy_price and (market_price - buy_price)/buy_price >= avg_thcp*profit1:
                
                sell_price = buy_price + buy_price*avg_thcp*profit1
                profit_sell_qty_1 = buy_quantity - round(buy_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    price = sell_price,
                    positionSide='LONG',
                    type=ORDER_TYPE_LIMIT,
                    timeInFORCE = 'GTC',
                    quantity=profit_sell_qty_1)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Profit Sell"
                remaining_qty = buy_quantity - profit_sell_qty_1

            ### this part is the loss reduction
            ### it calculates and compares the price drop % to average amplitude % of pass 20 candles 
            ### if the price dropping too low, it will trigger the condition and sell immediately
            if ((candles_30.iloc[0,2] >= candles_30.iloc[0,10] and up_l[-1][3] > market_price and (up_l[-1][3] - market_price)/up_l[-1][3] > avg_thcp*stop_loss_pct) or \
                candles_30.iloc[0,10] >= candles_30.iloc[0,1] or (candles_30.iloc[0,2] >= candles_30.iloc[0,10] and up_l[-1][3] > market_price and \
                (up_l[-1][3] - market_price)/up_l[-1][3] > stop_loss_force)) and last_trade_type != 'Sell':
                    
                final_quantity = remaining_qty

                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    positionSide='LONG',
                    type=ORDER_TYPE_MARKET,
                    quantity=final_quantity)

                buy_lock = 1
                last_trade_type = "Sell"
                new_balance = float(client.futures_account_balance()[1]['balance'])
                balance_diff_pct = (begin_balance - new_balance)/begin_balance
                
                if balance_diff_pct > final_stop_loss:
                    running = False
                    print("STOP LOSS TRIGGERED!")
                    print("THE % OF LOSS HAS REACHED",final_stop_loss*100,"% of the Total Futures Balance!")
                    print("THE TRADE BOT IS NOW TERMINATED!")
        
        time.sleep(1)  ### Refreshes every second

### Execute the trade bot to start trading with various settings!
trade_bot(kdj_length = 3, k = 9, d = 3, boll_length = 20, boll_multipler = 2, acceleration = 0.02, maximum = 0.2,
              usdt_symbol = "DOGEUSDT",buy_qty_pct = 0.7,profit1=1.5, profit2=2.0, profit3=2.5, profit4=3.0, 
              stop_loss_force=0.015, stop_loss_pct=1.5, final_stop_loss=0.05,leverage_level=1)





