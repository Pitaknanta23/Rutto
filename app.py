import json
from flask import Flask, request
from binance.client import Client
from binance.enums import *
import os
import requests

app = Flask(__name__)

API_KEY = str(os.environ['API_KEY'])
API_SECRET = str(os.environ['API_SECRET'])
TEST_NET = bool(str(os.environ['TEST_NET']))
LINE_TOKEN=str(os.environ['LINE_TOKEN'])
BOT_NAME=str(os.environ['BOT_NAME'])

client = Client(API_KEY,API_SECRET,testnet=TEST_NET)

#STATIC API for testnet
#API_KEY = '3ebbe4c386be6fd911894b3b0b72c6f2026959e47e74ed9aa0ff8f676a04a9c3'
#API_SECRET = '4b060561fddd153b5367614e8427bb5fd2a5b312f1dc2fff830278ddf36ed18a'
#client = Client(API_KEY,API_SECRET,testnet=True)


url = 'https://notify-api.line.me/api/notify'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+LINE_TOKEN}
#msg = 'Hello LINE Notify'
#r = requests.post(url, headers=headers, data = {'message':msg})
#print (r.text)

print(API_KEY)
print(API_SECRET)

@app.route("/")
def hello_world():
    return "Hello Welcome!"

@app.route("/webhook", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    print("arrr data")

    action = data['action']
    symbol = data['ticker']
    usdt = data['quantity(USDT)']
    lev = data['leverage']
    COIN = symbol[0:len(symbol)-4] 

    bid = 0
    ask = 0
    usdt = float(usdt)
    lev = int(lev)
    

    bid = float(client.futures_orderbook_ticker(symbol =symbol)['bidPrice'])
    ask = float(client.futures_orderbook_ticker(symbol =symbol)['askPrice'])

    posiAmt = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
    #OpenLong
    if action == "BUY":
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        Qty_buy = usdt/bid
        Qty_buy = round(Qty_buy,qty_precision)
        print('qty buy : ',Qty_buy)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)
        order_BUY = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=Qty_buy)
        print(symbol," : BUY")
        #success openlong, push line notification        
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[LONG]" + "\nAmount  :" + str(Qty_buy) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) + "\nPaid        :" + str(round(usdt/lev,3)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})
        
    #OpenShort
    if action == "SELL":
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        Qty_sell = usdt/ask
        Qty_sell = round(Qty_sell,qty_precision)
        print('qty sell : ',Qty_sell)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)
        order_SELL = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=Qty_sell)
        print(symbol,": SELL")
        #success openshort, push line notification        
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SHORT]" + "\nAmount  :" + str(Qty_sell) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) + "\nPaid        :" + str(round(usdt/lev,3)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})
        
    #StopLoss
    if action == "SL":
        if posiAmt > 0.0 :
            qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
            close_BUY = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty_close)
            #success close sell, push line notification        
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SELL]" + "\nAmount  :" + str(qty_close) + " "+  COIN +"/"+str(round((qty_close*bid),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*bid/lev),3)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": StopLoss")

        if posiAmt < 0.0 :
            qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
            close_SELL = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty_close*-1)
            print(symbol,": StopLoss")
            #success close buy, push line notification        
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(qty_close*-1) + " "+  COIN +"/"+str(round((qty_close*ask*-1),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*ask*-1/lev),3)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": StopLoss")
    #TakeProfit
    if action == "TP":
        if posiAmt > 0.0 :
            qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
            close_BUY = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty_close)
            #success close sell, push line notification                    
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SELL]" + "\nAmount  :" + str(qty_close) + " "+  COIN +"/"+str(round(qty_close*bid,3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round(qty_close*bid/lev,3)) + " USDT"            
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": TakeProfit")

        if posiAmt < 0.0 :
            qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
            close_SELL = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty_close*-1)
            #success close buy, push line notification        
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(qty_close*-1) + " "+  COIN +"/"+str(round(qty_close*ask*-1,3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round(qty_close*ask*-1/lev,3)) + " USDT"            
            r = requests.post(url, headers=headers, data = {'message':msg})            
            print(symbol,": TakeProfit")
    #CloseLong
    if action == "CloseBuy":
        qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
        close_BUY = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty_close)
        #success close sell, push line notification                
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SELL]" + "\nAmount  :" + str(qty_close) + " "+  COIN +"/"+str(round((qty_close*bid),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*bid/lev),3)) + " USDT"        
        r = requests.post(url, headers=headers, data = {'message':msg})        
        print(symbol,": Close Buy")
    #CloseShort
    if action == "CloseSell":
        qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
        close_SELL = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty_close*-1)
        #success close buy, push line notification        
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(qty_close*-1) + " "+  COIN +"/"+str(round((qty_close*ask*-1),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*ask*-1/lev),3)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})        
        print(symbol,": Close Sell")

    if action == "test":
        print("TEST!")
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nTest.."
        r = requests.post(url, headers=headers, data = {'message':msg})        
    
    print("---------------------------------")

    return {
        "code" : "success",
        "message" : data
    }

if __name__ == '__main__':
    app.run(debug=True)
