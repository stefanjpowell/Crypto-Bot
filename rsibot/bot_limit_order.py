import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/iotausdt@kline_1m"

RSI_PERIOD = 8
VARIANCE_PERIOD = 180
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 25
TRADE_SYMBOL = 'IOTAUSDT'
TRADE_QUANTITY = 300
GAIN_TARGET = 1.015 #1.01 = 1% gain target. Used as the sell target after a buy has been made 
DROP_QUANTITY1 = 0.985
DROP_QUANTITY2 = 0.98 # 0.9 = 2% drop in price after buy1 

closes = []
orders =[]

in_position = False
in_position2 = False

buy1_placed = False
buy2_placed = False
sell1_placed = False
sell2_placed = False

buy_price_history = [1] #needs a value for "last value" to function
buy_price_history2 = [1]

client = Client(config.API_KEY, config.API_SECRET)

def order(side, quantity, symbol,order_type=ORDER_TYPE_LIMIT):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC, price= closes[-1])
        print(order)
        orderId = order['orderId']
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return [True, orderId]
  

    
def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, in_position, in_position2, buy1_placed, buy2_placed, sell1_placed, sell2_placed, order, buy1_orderid, buy2_orderid, sell1_orderid, sell2_orderid
    
    #print('received message')
    json_message = json.loads(message)
    #pprint.pprint(json_message)


    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        
        print("closes")
        print(closes)
        last_buy_price = buy_price_history[-1]
        last_buy_price2 = buy_price_history2[-1]
        print("buy price history")
        print(buy_price_history)  
        print("buy price history2") 
        print(buy_price_history2)



                
        print('buy1 placed')
        print(buy1_placed)
        print('buy2 placed')
        print(buy2_placed)
        print('sell1 placed')
        print(sell1_placed)
        print('sell2 placed')
        print(sell2_placed)
        

        print("Buy position 1")
        print(in_position) 
        print("Buy position 2")
        print(in_position2) 
    

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all rsis calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))

            #sell round 1 logic
            if float(close) > last_buy_price * GAIN_TARGET and in_position and sell1_placed == False: 
                print("Price has increased 1percent since we bought! Sell! Sell! Sell!")
                # put binance sell logic here
                order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                if order_succeeded[0]:
                    sell1_placed = True
                    sell1_orderid = order_succeeded[1]
 
             #sell round 2 logic
            if float(close) > last_buy_price2 * GAIN_TARGET and in_position2 and sell2_placed == False: 
                print("Price has increased 1percent since we bought our second buy")
                # put binance sell logic here
                order_succeeded = order(SIDE_SELL, TRADE_QUANTITY*2, TRADE_SYMBOL)
                if order_succeeded:
                    sell2_placed = True
                    sell2_orderid = order_succeeded[1]
      
            #buy round 1 logic           
            if last_rsi < RSI_OVERSOLD and float(close)/max(closes[-VARIANCE_PERIOD:]) < DROP_QUANTITY1:
                ###test place buy1 order
                if in_position or buy1_placed:
                    print("It is oversold, but you already own it or have an order placed..... nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded[0]:
                        buy1_placed = True
                        buy_price_history.append(float(close))
                        buy1_orderid = order_succeeded[1]
                        print(buy1_orderid)

            
            # Buy round 2 logic
            if float(close) < last_buy_price * DROP_QUANTITY2 and in_position:
                if in_position2 or buy2_placed == True or last_buy_price == 1 :   
                    print("The price has dropped since we bought but we already have a position or order")
                else:
                    print("The price has dropped since we bought, so lets buy more!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY*2, TRADE_SYMBOL)
                    if order_succeeded[0]:
                        buy2_placed = True
                        buy_price_history2.append(float(close))
                        buy2_orderid = order_succeeded[1]

        # If xxxx_orderplaced = true, check if it has been activated and change position status accordingly 
        if buy1_placed:
            orderstatus = client.get_order(symbol=TRADE_SYMBOL,orderId=buy1_orderid)
            if orderstatus['status'] == "FILLED":
                in_position = True
                buy1_placed = False
            elif orderstatus['status'] == "CANCELED":
                buy1_placed = False

        if buy2_placed:
            orderstatus = client.get_order(symbol=TRADE_SYMBOL,orderId=buy2_orderid)
            if orderstatus['status'] == "FILLED":
                in_position2 = True
                buy2_placed = False
            elif orderstatus['status'] == "CANCELED":
                buy2_placed = False

        if sell1_placed:
            orderstatus = client.get_order(symbol=TRADE_SYMBOL,orderId=sell1_orderid)
            if orderstatus['status'] == "FILLED":
                in_position = False
                sell1_placed = False
            elif orderstatus['status'] == "CANCELED":
                sell1_placed = False

        if sell2_placed:
            orderstatus = client.get_order(symbol=TRADE_SYMBOL,orderId=sell2_orderid)
            if orderstatus['status'] == "FILLED":
                in_position2 = False
                sell2_placed = False
            elif orderstatus['status'] == "CANCELED":
                sell2_placed = False    

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()