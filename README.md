# Binance-Trading-Bot
Simple Trading bot that uses RSI and Bollinger Bands as a buy/sell indicator. The values in the script work quite well. Still need to implement a stop loss. The code is from about an year ago, so the code might be broken.

# Instalation
```bash
pip install websocket-client pprint talib numpy binance-python
```
Make sure you fill the api key and secret key in `config.py`.
You can also use a discord webhook if you want.

# Warning
This bot uses ALL of your USDT balance by default. Modify in the code in order to use another currency or less money to place trades. You can test the bot by using the [testnet](https://testnet.binance.vision/).

