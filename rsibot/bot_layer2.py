import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/iotausdt@kline_1m"

RSI_PERIOD = 3
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 60
TRADE_SYMBOL = 'IOTAUSDT'
TRADE_QUANTITY = 50
GAIN_TARGET = 1.01 #1.01 = 1% gain target. Used as the sell target after a buy has been made 
DROP_QUANTITY2 = 0.98 # 0.9 = 2% drop in price after buy1 

closes = []

in_position = False
in_position2 = False

buy_price_history = [1] #needs a value for "last value" to function
buy_price_history2 = [1]

client = Client(config.API_KEY, config.API_SECRET)

def order(side, quantity, symbol,order_type=ORDER_TYPE_LIMIT):
    try:
        print("sending order")
        order = client.create_margin_order(symbol=symbol, side=side, type=order_type, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC, price=closes[-1])
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

    
def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, in_position, in_position2
    
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
            if float(close) > last_buy_price * GAIN_TARGET and in_position: 
            
                print("Price has increased 1percent since we bought! Sell! Sell! Sell!")
                # put binance sell logic here
                order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                if order_succeeded:
                    in_position = False

            
             #sell round 2 logic
            if float(close) > last_buy_price2 * GAIN_TARGET and in_position2: 
                
            
                print("Price has increased 1percent since we bought our second buy")
                # put binance sell logic here
                order_succeeded = order(SIDE_SELL, TRADE_QUANTITY*2, TRADE_SYMBOL)
                if order_succeeded:
                    in_position2 = False

                       
            #buy round 1 logic           
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
                        buy_price_history.append(float(close))
            
            # Buy round 2 logic
            if float(close) < last_buy_price * DROP_QUANTITY2 and in_position:
                if in_position2 or last_buy_price == 1:   
                    print("The price has dropped since we bought but we already ahve a second buy")
                else:
                    print("The price has dropped since we bought, so lets buy more!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY*2, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position2 = True
                        buy_price_history2.append(float(close))

                        

                
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()