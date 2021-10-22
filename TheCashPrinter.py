### Version 2.0 
### Project Halted due to Binance banned in Ontario.

import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from binance.enums import *
from binance.client import Client

client=Client(api_key = "YOUR API KEY" ,
              api_secret = "YOUR SCECRET KEY")

def sar(acceleration, maximum):
    low = kline_data_extract.low
    high = kline_data_extract.high
    close = kline_data_extract.close
    psar = close[0:len(close)]
    bull = True
    af = acceleration
    maxaf = maximum
    lp = low[0]
    hp = high[0]
    
    for i in range(2,len(close)):
        if bull:
            psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
        else:
            psar[i] = psar[i - 1] + af * (lp - psar[i - 1])
        
        reverse = False
        
        if bull:
            if low[i] < psar[i]:
                bull = False
                reverse = True
                psar[i] = hp
                lp = low[i]
                af = acceleration
        else:
            if high[i] > psar[i]:
                bull = True
                reverse = True
                psar[i] = lp
                hp = high[i]
                af = acceleration
    
        if not reverse:
            if bull:
                if high[i] > hp:
                    hp = high[i]
                    af = min(af + acceleration, maxaf)
                if low[i - 1] < psar[i]:
                    psar[i] = low[i - 1]
                if low[i - 2] < psar[i]:
                    psar[i] = low[i - 2]
            else:
                if low[i] < lp:
                    lp = low[i]
                    af = min(af + acceleration, maxaf)
                if high[i - 1] > psar[i]:
                    psar[i] = high[i - 1]
                if high[i - 2] > psar[i]:
                    psar[i] = high[i - 2]
               
    return psar

def kdj(kdj_length, k, d, ret):   ### The function of KDJ technical indicator
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

def boll(boll_length, boll_multipler, boll_ret): ### The function of Bollinger Bands technical indicator
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

def kline_data_extract(usdt_symbol, kdj_length, k, d, boll_length, boll_multipler, acceleration, maximum):
    
    dict_setup = {"time":[],"open":[], "high":[], "low":[], "close":[]}
    kline_data = []
    
    current_time = datetime.today()
    start_at = current_time - timedelta(minutes=15*48)
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
    
    had = df
    
    return had


def trade_bot(kdj_length, k, d, boll_length, boll_multipler, acceleration, maximum,
              usdt_symbol,long_qty_pct,short_qty_pct,
              long_profit1=2.0, long_profit2=2.5, long_profit3=3.0, long_profit4=4.0, long_stop_loss_pct=1.5, long_force_stop_loss_pct=1.0,
              short_profit1=2.0, short_profit2=2.5, short_profit3=3.0, short_profit4=4.0, short_stop_loss_pct=1.5, short_force_stop_loss_pct=1.0,
              final_stop_loss=0.1,leverage_level=1):
    
    sos = {'Symbol':[], 'Total Realized Gain/Loss %':[], 'Average Realized Gain/Loss %':[], 'Positive Liquidation Average % Gain':[], 
           'Negative Liquidation Average % Loss':[], 'Positive Liquidation Probability':[]}
    
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    client.futures_change_leverage(symbol = usdt_symbol, leverage = leverage_level)
    begin_balance = float(client.futures_account_balance()[1]['balance'])
    
    running = True
    print("THE TRADE BOT IS RUNNING!")
    sar_above = 0
    sar_below = 0
    last_trade_type = 'N/A'
    long_sar_counter = 0
    long_remaining_qty = 0
    long_ID = 0
    long_lock = 0
    long_price = 0
    long_quantity = 0
    highest_market_price = 0
    long_profit_close_qty_4 = 0
    long_profit_close_qty_3 = 0
    long_profit_close_qty_2 = 0
    long_profit_close_qty_1 = 0
    short_sar_counter = 0
    short_remaining_qty = 0
    short_ID = 0
    short_lock = 0
    short_price = 0
    short_quantity = 0
    lowest_market_price = 0
    short_profit_close_qty_4 = 0
    short_profit_close_qty_3 = 0
    short_profit_close_qty_2 = 0
    short_profit_close_qty_1 = 0
    
    while running == True:
        
        current_time = datetime.today()
        current_minute = current_time.minute
        current_time_str = current_time.strftime("%Y/%m/%d, %H:%M")
        current_time_datetime = datetime.strptime(current_time_str, "%Y/%m/%d, %H:%M")
        
        candles_hd = kline_data_extract(usdt_symbol = usdt_symbol, kdj_length = kdj_length, k = k, d = d, 
                                        boll_length = boll_length, boll_multipler = boll_multipler, 
                                        acceleration = acceleration, maximum = maximum)
        
        market_price = float(client.futures_mark_price(symbol=usdt_symbol)['markPrice'])
        
        time_left = current_time_datetime - datetime.strptime(candles_hd.index[1], "%Y/%m/%d, %H:%M")
        
        minutes_left = 30 - int((time_left.seconds)/60)
        
        half_day_history_data = candles_hd
        half_day_history_sum_chg_pct = 0
        for t in range(len(half_day_history_data.index)):
            half_day_history_sum_chg_pct += np.absolute((half_day_history_data.iloc[t,1] - half_day_history_data.iloc[t,2])/
                                           half_day_history_data.iloc[t,2])
        avg_thcp = half_day_history_sum_chg_pct / len(half_day_history_data.index)
        
        if last_trade_type == "Long" or last_trade_type == "Long Profit Close":
            if market_price > highest_market_price:
                highest_market_price = market_price
        
        if last_trade_type == "Short" or last_trade_type == "Short Profit Close":
            if market_price < lowest_market_price:
                lowest_market_price = market_price
        
        if last_trade_type == 'N/A':
            
            candles_half_day_reversed = candles_hd.reindex(index=candles_hd.index[::-1])
            
            for h in range(28,len(candles_half_day_reversed)-1):
                if candles_half_day_reversed.iloc[h][10] >= candles_half_day_reversed.iloc[h][1]:
                    if long_sar_counter != 0:
                        long_sar_counter = 0
                    short_sar_counter += 1
                    long_lock = 0
                    if short_sar_counter > 1:
                        short_lock = 1
                elif candles_half_day_reversed.iloc[h][10] <= candles_half_day_reversed.iloc[h][2]:
                    if short_sar_counter != 0:
                        short_sar_counter = 0
                    long_sar_counter += 1
                    short_lock = 0
                    if long_sar_counter > 1:
                        long_lock = 1
            
            if candles_hd.iloc[0,0] > candles_hd.iloc[0,3] and ((candles_hd.iloc[0,4] < candles_hd.iloc[0,5] and candles_hd.iloc[0,3] <= candles_hd.iloc[0,9] and \
                                                                 candles_hd.iloc[0,10] <= candles_hd.iloc[0,2] and short_lock == 0 and minutes_left < 3) or \
                                                                (candles_hd.iloc[0,10] >= candles_hd.iloc[0,1] and candles_hd.iloc[0,4] < candles_hd.iloc[0,5] and \
                                                                short_lock == 0)):
                
                short_quantity = round((begin_balance*short_qty_pct)/candles_hd.iloc[0][3],0)
                
                short = client.futures_create_order(
                            symbol=usdt_symbol,
                            side=SIDE_SELL,
                            positionSide='SHORT',
                            type=ORDER_TYPE_MARKET,
                            quantity=short_quantity)
                
                short_remaining_qty = short_quantity
                short_ID = short['orderId']
                last_trade_type = 'Short'
                
                lowest_market_price = market_price
            
            elif candles_hd.iloc[0,0] < candles_hd.iloc[0,3] and ((candles_hd.iloc[0,4] > candles_hd.iloc[0,5] and candles_hd.iloc[0,3] >= candles_hd.iloc[0,9] and \
                                                                   candles_hd.iloc[0,10] >= candles_hd.iloc[0,1] and long_lock == 0 and minutes_left < 3) or \
                                                                  (candles_hd.iloc[0,10] <= candles_hd.iloc[0,2] and candles_hd.iloc[0,4] > candles_hd.iloc[0,5] and \
                                                                   long_lock == 0)):
                
                long_quantity = round((begin_balance*long_qty_pct)/candles_hd.iloc[0][3],0)
                
                long = client.futures_create_order(
                            symbol=usdt_symbol,
                            side=SIDE_BUY,
                            positionSide='LONG',
                            type=ORDER_TYPE_MARKET,
                            quantity=long_quantity)
                
                long_remaining_qty = long_quantity
                long_ID = long['orderId']
                last_trade_type = 'Long'
                
                highest_market_price = market_price
                
        ### This is the buy in part where backtest will use the conditions set on 
        ### the technical indicators and various requirements to decide whether to buy or not.
        ### If buy in, this part will create an up_l list storing the positive candles higher than the previous one 
        ### consecutively for profit sell conditions.
        ### This part will also create trade data in had_calc_df dataframe for gain/loss calculation.

        elif last_trade_type == "Long" or last_trade_type == "Long Profit Close":
            ### this calculates the average % change of the canldes in up_l list for a general understanding of how
            ### much avg % u currently have gained and to secure profit before price dropping down
            
            long_price = float(client.futures_get_order(symbol=usdt_symbol, orderId = long_ID)['avgPrice'])
            
            if candles_hd.iloc[0,10] <= candles_hd.iloc[0,2]:
                if sar_below == 0:
                    sar_below = 1
            
            ### this part will setup values to secure profit when the current closing price have reached 
            ### specified limits
            if market_price > long_price and (market_price - long_price)/long_price >= avg_thcp*long_profit4:
                
                long_profit_close_qty_4 = long_quantity -  long_profit_close_qty_1 - long_profit_close_qty_2 - long_profit_close_qty_3
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    positionSide='LONG',
                    type=ORDER_TYPE_MARKET,
                    quantity=long_profit_close_qty_4)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                long_remaining_qty = 0
                last_trade_type = 'Close Long'
                long_quantity = 0
                long_profit_close_qty_4 = 0
                long_profit_close_qty_3 = 0
                long_profit_close_qty_2 = 0
                long_profit_close_qty_1 = 0
                highest_market_price = 0
                sar_below = 0

            elif market_price > long_price and (market_price - long_price)/long_price >= avg_thcp*long_profit3 and long_profit_close_qty_3 == 0:
                
                if long_profit_close_qty_1 == 0 and long_profit_close_qty_2 == 0:
                    long_profit_close_qty_3 = round(long_quantity*0.75,0)
                
                elif long_profit_close_qty_1 != 0 and long_profit_close_qty_2 == 0:
                    long_profit_close_qty_3 = round(long_quantity/2,0)
                
                elif long_profit_close_qty_1 == 0 and long_profit_close_qty_2 != 0:
                    long_profit_close_qty_3 = round(long_quantity/4,0)
                    
                elif long_profit_close_qty_1 != 0 and long_profit_close_qty_2 != 0:
                    long_profit_close_qty_3 = round(long_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    positionSide='LONG',
                    type=ORDER_TYPE_MARKET,
                    quantity=long_profit_close_qty_3)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Long Profit Close"
                long_remaining_qty = long_remaining_qty - long_profit_close_qty_3

            elif market_price > long_price and (market_price - long_price)/long_price >= avg_thcp*long_profit2 and long_profit_close_qty_2 == 0:

                if long_profit_close_qty_1 == 0:
                    long_profit_close_qty_2 = round(long_quantity/2,0)
                
                elif long_profit_close_qty_1 != 0:
                    long_profit_close_qty_2 = round(long_quantity/4,0)

                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    positionSide='LONG',
                    type=ORDER_TYPE_MARKET,
                    quantity=long_profit_close_qty_2)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Long Profit Close"
                long_remaining_qty = long_remaining_qty - long_profit_close_qty_2
                
            elif market_price > long_price and (market_price - long_price)/long_price >= avg_thcp*long_profit1 and long_profit_close_qty_1 == 0:
                
                long_profit_close_qty_1 = round(long_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_SELL,
                    positionSide='LONG',
                    type=ORDER_TYPE_MARKET,
                    quantity=long_profit_close_qty_1)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Long Profit Close"
                long_remaining_qty = long_remaining_qty - long_profit_close_qty_1

            ### this part is the loss reduction
            ### it calculates and compares the price drop % to average amplitude % of pass 20 candles 
            ### if the price dropping too low, it will trigger the condition and sell immediately
            if last_trade_type != "Close Long":
                if (highest_market_price > market_price and (highest_market_price - market_price)/highest_market_price > avg_thcp*long_stop_loss_pct and last_trade_type == "Long Profit Close") or \
                   (candles_hd.iloc[0,10] >= candles_hd.iloc[0,1] and sar_below == 1) or (last_trade_type == "Long" and long_price > market_price and \
                   (long_price - market_price)/long_price > avg_thcp*long_force_stop_loss_pct):
                    
                    final_long_quantity = long_remaining_qty

                    client.futures_create_order(
                        symbol = usdt_symbol,
                        side=SIDE_SELL,
                        positionSide='LONG',
                        type=ORDER_TYPE_MARKET,
                        quantity=final_long_quantity)
                
                    long_profit_close_qty_4 = 0
                    long_profit_close_qty_3 = 0
                    long_profit_close_qty_2 = 0
                    long_profit_close_qty_1 = 0
                    highest_market_price = 0
                    long_quantity = 0
                    sar_below = 0
                    last_trade_type = "Close Long"
                    new_balance = float(client.futures_account_balance()[1]['balance'])
                    balance_diff_pct = (begin_balance - new_balance)/begin_balance
                
                    if balance_diff_pct > final_stop_loss:
                        running = False
                        print("STOP LOSS TRIGGERED!")
                        print("THE % OF LOSS HAS REACHED",final_stop_loss*100,"% of the Total Futures Balance!")
                        print("THE TRADE BOT HAS TERMINATED!")
        
        
        #### Close All Short Sell Openings 
        elif last_trade_type == "Short" or last_trade_type == "Short Profit Close":
            ### this calculates the average % change of the canldes in up_l list for a general understanding of how
            ### much avg % u currently have gained and to secure profit before price dropping down
            
            short_price = float(client.futures_get_order(symbol=usdt_symbol, orderId = short_ID)['avgPrice'])
            
            if candles_hd.iloc[0,10] >= candles_hd.iloc[0,1]:
                if sar_above == 0:
                    sar_above = 1
            
            ### this part will setup values to secure profit when the current closing price have reached 
            ### specified limits
            if market_price < short_price and (short_price - market_price)/short_price >= avg_thcp*short_profit4:
                
                short_profit_close_qty_4 = short_quantity -  short_profit_close_qty_1 - short_profit_close_qty_2 - short_profit_close_qty_3
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_BUY,
                    positionSide='SHORT',
                    type=ORDER_TYPE_MARKET,
                    quantity=short_profit_close_qty_4)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                short_remaining_qty = 0
                last_trade_type = 'Close Short'
                short_quantity = 0
                short_profit_close_qty_4 = 0
                short_profit_close_qty_3 = 0
                short_profit_close_qty_2 = 0
                short_profit_close_qty_1 = 0
                lowest_market_price = 0
                sar_above = 0

            elif market_price < short_price and (short_price - market_price)/short_price >= avg_thcp*short_profit3 and short_profit_close_qty_3 == 0:
                
                if short_profit_close_qty_1 == 0 and short_profit_close_qty_2 == 0:
                    short_profit_close_qty_3 = round(short_quantity*0.75,0)
                
                elif short_profit_close_qty_1 != 0 and short_profit_close_qty_2 == 0:
                    short_profit_close_qty_3 = round(short_quantity/2,0)
                
                elif short_profit_close_qty_1 == 0 and short_profit_close_qty_2 != 0:
                    short_profit_close_qty_3 = round(short_quantity/4,0)
                    
                elif short_profit_close_qty_1 != 0 and short_profit_close_qty_2 != 0:
                    short_profit_close_qty_3 = round(short_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_BUY,
                    positionSide='SHORT',
                    type=ORDER_TYPE_MARKET,
                    quantity=short_profit_close_qty_3)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Short Profit Close"
                short_remaining_qty = short_remaining_qty - short_profit_close_qty_3

            elif market_price < short_price and (short_price - market_price)/short_price >= avg_thcp*short_profit2 and short_profit_close_qty_2 == 0:
                
                if short_profit_close_qty_1 == 0:
                    short_profit_close_qty_2 = round(short_quantity/2,0)
                
                elif short_profit_close_qty_1 != 0:
                    short_profit_close_qty_2 = round(short_quantity/4,0)

                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_BUY,
                    positionSide='SHORT',
                    type=ORDER_TYPE_MARKET,
                    quantity=short_profit_close_qty_2)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Short Profit Close"
                short_remaining_qty = short_remaining_qty - short_profit_close_qty_2
                
            elif market_price < short_price and (short_price - market_price)/short_price >= avg_thcp*short_profit1 and short_profit_close_qty_1 == 0:
                
                short_profit_close_qty_1 = round(short_quantity/4,0)
                
                client.futures_create_order(
                    symbol = usdt_symbol,
                    side=SIDE_BUY,
                    positionSide='SHORT',
                    type=ORDER_TYPE_MARKET,
                    quantity=short_profit_close_qty_1)
                
                new_balance = float(client.futures_account_balance()[1]['balance'])
                if new_balance > begin_balance:
                    begin_balance = new_balance
                    
                last_trade_type = "Short Profit Close"
                short_remaining_qty = short_remaining_qty - short_profit_close_qty_1

            ### this part is the loss reduction
            ### it calculates and compares the price drop % to average amplitude % of pass 20 candles 
            ### if the price dropping too low, it will trigger the condition and sell immediately
            if last_trade_type != "Close Short":
                if (lowest_market_price < market_price and np.abs((lowest_market_price - market_price)/lowest_market_price) > avg_thcp*short_stop_loss_pct and \
                   last_trade_type == "Short Profit Close") or (candles_hd.iloc[0,10] <= candles_hd.iloc[0,2] and sar_above == 1) or (last_trade_type == "Short" and \
                   short_price < market_price and np.abs((short_price - market_price)/short_price) > avg_thcp*short_force_stop_loss_pct):
                    
                    final_short_quantity = short_remaining_qty

                    client.futures_create_order(
                        symbol = usdt_symbol,
                        side=SIDE_BUY,
                        positionSide='SHORT',
                        type=ORDER_TYPE_MARKET,
                        quantity=final_short_quantity)
                
                    short_profit_close_qty_4 = 0
                    short_profit_close_qty_3 = 0
                    short_profit_close_qty_2 = 0
                    short_profit_close_qty_1 = 0
                    lowest_market_price = 0
                    short_quantity = 0
                    sar_above = 0
                    last_trade_type = "Close Short"
                    new_balance = float(client.futures_account_balance()[1]['balance'])
                    balance_diff_pct = (begin_balance - new_balance)/begin_balance
                
                    if balance_diff_pct > final_stop_loss:
                        running = False
                        print("STOP LOSS TRIGGERED!")
                        print("THE % OF LOSS HAS REACHED",final_stop_loss*100,"% of the Total Futures Balance!")
                        print("THE TRADE BOT HAS TERMINATED!")
        
        elif last_trade_type == 'Close Long':
            if candles_hd.iloc[0,0] > candles_hd.iloc[0,3] and ((candles_hd.iloc[0,4] < candles_hd.iloc[0,5] and candles_hd.iloc[0,3] <= candles_hd.iloc[0,9] and \
                candles_hd.iloc[0,10] <= candles_hd.iloc[0,2] and minutes_left < 3) or (candles_hd.iloc[0,10] >= candles_hd.iloc[0,1] and candles_hd.iloc[0,4] < candles_hd.iloc[0,5])):
                
                short_quantity = round((begin_balance*short_qty_pct)/candles_hd.iloc[0][3],0)
                
                short = client.futures_create_order(
                            symbol=usdt_symbol,
                            side=SIDE_SELL,
                            positionSide='SHORT',
                            type=ORDER_TYPE_MARKET,
                            quantity=short_quantity)
                
                short_remaining_qty = short_quantity
                short_ID = short['orderId']
                last_trade_type = 'Short'
                
                lowest_market_price = market_price
        
        elif last_trade_type == 'Close Short':
            if candles_hd.iloc[0,0] < candles_hd.iloc[0,3] and ((candles_hd.iloc[0,4] > candles_hd.iloc[0,5] and candles_hd.iloc[0,3] >= candles_hd.iloc[0,9] and \
                candles_hd.iloc[0,10] >= candles_hd.iloc[0,1] and minutes_left < 3) or (candles_hd.iloc[0,10] <= candles_hd.iloc[0,2] and candles_hd.iloc[0,4] > candles_hd.iloc[0,5])):
                
                long_quantity = round((begin_balance*long_qty_pct)/candles_hd.iloc[0][3],0)
                
                long = client.futures_create_order(
                            symbol=usdt_symbol,
                            side=SIDE_BUY,
                            positionSide='LONG',
                            type=ORDER_TYPE_MARKET,
                            quantity=long_quantity)
                
                long_remaining_qty = long_quantity
                long_ID = long['orderId']
                last_trade_type = 'Long'
                
                highest_market_price = market_price
                
        time.sleep(1)  

trade_bot(kdj_length = 3, k = 9, d = 3, boll_length = 20, boll_multipler = 2, acceleration = 0.02, maximum = 0.2,
              usdt_symbol = "SKLUSDT",long_qty_pct = 0.9,short_qty_pct = 0.9, 
              long_profit1=2.0, long_profit2=2.5, long_profit3=3.0, long_profit4=4.0, long_stop_loss_pct=1.5, long_force_stop_loss_pct=1.0,
              short_profit1=2.0, short_profit2=2.5, short_profit3=3.0, short_profit4=4.0, short_stop_loss_pct=1.5, short_force_stop_loss_pct=1.0,
              final_stop_loss=0.10,leverage_level=1)



