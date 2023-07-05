import websocket, json, pprint, talib, numpy,math
import config
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
from discord_webhook import DiscordWebhook, DiscordEmbed
import pandas as pd

RSI_PERIOD = 5  # set RSI period
RSI_OVERBOUGHT = 75  # set RSI threshold
RSI_OVERSOLD = 20  # set RSI threshold
BB_LENGTH = 21  # set bollinger bands length
BB_STD = 2.6  # set bollinger bands standard deviation
TRADE_SYMBOL = 'BTCUSDT'  # set coin type
TIMEFRAME = "5m"  # set timeframe
TRADE_QUANTITY = 0
BALANCE = 0
t = TRADE_SYMBOL.lower()
closes = [] 
ticker = "BTC-USD"
in_position = False  # checking if in position
buying_price = 0

def truncate(num,n):
    temp = str(num)
    for x in range(len(temp)):
        if temp[x] == '.':
            try:
                return float(temp[:x+n+1])
            except:
                return float(temp)      
    return float(temp)

webhook = DiscordWebhook(url='https://discord.com/api/webhooks/*******************************')
SOCKET = f'wss://stream.binance.com:9443/ws/{t}@kline_{TIMEFRAME}'
client = Client(config.API_KEY, config.API_SECRET, testnet=False)
data = pd.DataFrame(client.get_historical_klines_generator(TRADE_SYMBOL, Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC"))
data.columns = [
  'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav',
  'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
]
data = data.astype(float)
for i in data["close"]:
  i = truncate(float(i), 4)
  closes.append(float(i))

def order(side, quantity, symbol, close, last_upper, last_lower, last_rsi, order_type=ORDER_TYPE_MARKET):
  try:
    print("sending order")
    order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
    print(order)
    BALANCE=truncate(float(client.get_asset_balance(asset='USDT')['free']),4)
    embed = DiscordEmbed(title='Order Sent', description='', color='GRAY')
    embed.set_thumbnail(url='https://cdn.discordapp.com/icons/**************.png')
    embed.set_footer(text='Live buy/sell signals')
    embed.set_timestamp()
    embed.add_embed_field(name='Ticker', value=format(TRADE_SYMBOL))
    embed.add_embed_field(name='Signal Type', value=format(side))
    embed.add_embed_field(name='Closing Price', value=f'${format(close)}')
    embed.add_embed_field(name='Upperband', value=format(last_upper))
    embed.add_embed_field(name='Lowerband', value=format(last_lower))
    embed.add_embed_field(name='RSI', value=format(last_rsi))
    embed.add_embed_field(name='Balance', value=format(BALANCE) )
    webhook.add_embed(embed)
    print(webhook.execute(remove_embeds=True, remove_files=True))
  except Exception as e:
    print("An exception occured - {}".format(e))
    return False
  return True

def on_open(ws):
  print('*** opened connection ***')
  print('The bot will now attempt to find good buy/sell signals')

def on_close(ws):
  print('*** closed connection ***')

def rsi_bb(ws, message):
  global closes, in_position, BALANCE, buying_price, TRADE_QUANTITY

  json_message = json.loads(message)
  candle = json_message['k']
  is_candle_closed = candle['x']
  close = candle['c']

  if is_candle_closed:  # taking only the closing candle stick for the period
    close = truncate(float(close), 4)
    closes.append(close)

    if len(closes) > BB_LENGTH: 
      np_closes = numpy.array(closes)
      rsi = talib.RSI(np_closes, RSI_PERIOD)  # setting rsi and bollingerbands
      upperband, middleband, lowerband = talib.BBANDS(np_closes, timeperiod=BB_LENGTH, nbdevup=BB_STD, nbdevdn=BB_STD, matype=0)
      last_rsi = truncate(rsi[-1],2)
      last_lowerband = truncate(lowerband[-1],2)
      last_upperband = truncate(upperband[-1],2)
      t_bal = client.get_asset_balance(asset='USDT')
      BALANCE=truncate(float(t_bal['free']),4)
      print(f'Closing: {close} | RSI: {last_rsi} | Upperband: {last_upperband} | Lowerband: {last_lowerband} | Balance: {BALANCE}')

      if last_rsi > RSI_OVERBOUGHT and close > last_upperband:  # SELL CONDITION
        if in_position:
          TRADE_QUANTITY = truncate(float(client.get_asset_balance(asset='BTC')['free']), 4)
          print(f'Seling {TRADE_QUANTITY} worth {close*TRADE_QUANTITY} of {TRADE_SYMBOL}')
          order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL, close, last_upperband, last_lowerband, last_rsi)
          if order_succeeded:
            in_position = False
      if last_rsi < RSI_OVERSOLD and close < last_lowerband:  # BUY CONDITION
        if not in_position:
          BALANCE=truncate(float(client.get_asset_balance(asset='USDT')['free']),4)
          TRADE_QUANTITY = truncate(BALANCE / close, 4)
          print(f'Buying {TRADE_QUANTITY} worth {TRADE_QUANTITY * close} of {TRADE_SYMBOL}')
          order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL, close, last_upperband, last_lowerband, last_rsi)
          if order_succeeded:
            in_position = True

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=rsi_bb)
ws.run_forever()
