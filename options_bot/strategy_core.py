import talib
import pandas as pd


def tech_signal(df, ma_short=50, ma_long=200, rsi_len=14,
                rsi_ob=60, rsi_os=40):
    df['ma_s'] = talib.SMA(df['close'], timeperiod=ma_short)
    df['ma_l'] = talib.SMA(df['close'], timeperiod=ma_long)
    df['rsi'] = talib.RSI(df['close'], timeperiod=rsi_len)
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    long_ok = (df.close > df.ma_l) & (df.close.shift(1) < df.ma_s)
    short_ok = (df.close < df.ma_l) & (df.close.shift(1) > df.ma_s)

    long = long_ok.iloc[-1] and df.rsi.iloc[-1] < rsi_ob
    short = short_ok.iloc[-1] and df.rsi.iloc[-1] > rsi_os
    return long, short, df.atr.iloc[-1]
