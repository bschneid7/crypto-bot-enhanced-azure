import pandas as pd
import numpy as np

def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def atr(high, low, close, length=14):
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    return pd.Series(tr).rolling(length).mean()

def compute_indicators(df, macd_fast=12, macd_slow=26, macd_signal=9, ema_len=200, atr_len=14):
    macd_line = ema(df['close'], macd_fast) - ema(df['close'], macd_slow)
    macd_sig  = ema(macd_line, macd_signal)
    ema200    = ema(df['close'], ema_len)
    atrv      = atr(df['high'], df['low'], df['close'], atr_len)
    volz      = (df['volume'] - df['volume'].rolling(20).mean()) / (df['volume'].rolling(20).std() + 1e-9)
    return macd_line, macd_sig, ema200, atrv, volz

def generate_signal(df, whale_flag, params):
    macd_fast = params['macd']['fast']; macd_slow = params['macd']['slow']; macd_signal = params['macd']['signal']
    ema_len = params['ema']['len']; atr_len = params['atr_len']
    macd_line, macd_sig, ema200, atrv, volz = compute_indicators(df, macd_fast, macd_slow, macd_signal, ema_len, atr_len)

    c = df['close'].iloc[-1]
    cond_trend = (macd_line.iloc[-1] > macd_sig.iloc[-1]) and (c > ema200.iloc[-1])
    cond_vol   = (volz.iloc[-1] >= 2.0) or whale_flag

    if cond_trend and cond_vol:
        a = float(atrv.iloc[-1])
        entry = float(c)
        stop  = float(entry - params['exits']['atr_stop'] * a)
        tp    = float(entry + params['exits']['atr_tp'] * a)
        return {
            "symbol_side": "BUY",
            "entry": entry,
            "stop": stop,
            "tp": tp,
            "atr": a,
            "reasons": {"trend":"macd_up_above_ema200", "volume": "z>=2_or_whale"}
        }
    return None

