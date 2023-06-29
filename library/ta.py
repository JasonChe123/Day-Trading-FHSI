import pandas as pd
import numpy as np
import time


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function '{func.__name__}' took {end_time - start_time:.5f} seconds to run")
        return result
    return wrapper


def bollingerbands(price_original: pd.Series, period: int = 20, num_std: float = 2.0):
    """
    :param price_original: Price Series (normally 'close')
    :param period: calculated period
    :param num_std: required standard deviation
    :return: Series: sma, upper_band, lower_band
    """
    price = price_original.copy()

    rolling_mean = price.rolling(window=period).mean()
    rolling_std = price.rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)

    return np.round(rolling_mean, 2), np.round(upper_band, 2), np.round(lower_band, 2)


def adx(df_original: pd.DataFrame, period: int = 14):
    """
    :param df_original: DataFrame contains columns: 'high' 'low' 'close'
    :param period: calculated peruod
    :return: Series ['ADX']
    """
    alpha = 1.015 / period  # smoothing factor: as same as possible to multicharts
    df = df_original.copy()

    # TR
    df['H-L'] = df['high'] - df['low']
    df['H-C'] = np.abs(df['high'] - df['close'].shift(1))
    df['L-C'] = np.abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
    del df['H-L'], df['H-C'], df['L-C']

    # ATR
    df['ATR'] = df['TR'].ewm(alpha=alpha, adjust=False).mean()

    # +-DX
    df['H-pH'] = df['high'] - df['high'].shift(1)
    df['pL-L'] = df['low'].shift(1) - df['low']
    df['+DX'] = np.where(
        (df['H-pH'] > df['pL-L']) & (df['H-pH'] > 0),
        df['H-pH'],
        0.0
    )
    df['-DX'] = np.where(
        (df['H-pH'] < df['pL-L']) & (df['pL-L'] > 0),
        df['pL-L'],
        0.0
    )
    del df['H-pH'], df['pL-L']

    # +- DMI
    df['S+DM'] = df['+DX'].ewm(alpha=alpha, adjust=False).mean()
    df['S-DM'] = df['-DX'].ewm(alpha=alpha, adjust=False).mean()
    df['+DMI'] = (df['S+DM'] / df['ATR']) * 100
    df['-DMI'] = (df['S-DM'] / df['ATR']) * 100
    del df['S+DM'], df['S-DM']

    # ADX
    df['DX'] = (np.abs(df['+DMI'] - df['-DMI']) / (df['+DMI'] + df['-DMI'])) * 100
    df['ADX'] = df['DX'].ewm(alpha=alpha, adjust=False).mean()

    return df['ADX']


def ema(df_original: pd.DataFrame, period: int, ohlc='close'):
    """
    :param df_original: DataFrame contains columns: 'open' 'high' 'low' 'close'
    :param period:
    :param ohlc:
    :return: Series
    """
    df = df_original.copy()
    df['ema'] = df[ohlc].ewm(span=period, adjust=False).mean()
    return df['ema']


def stoch(df_original: pd.DataFrame, period: int = 14, smooth_1: int = 3, smooth_2: int = 3, smoothing_type: int = 1):
    df = df_original.copy()

    high_n = df['high'].rolling(window=period).max()
    low_n = df['low'].rolling(window=period).min()
    k = ((df['close'] - low_n) / (high_n - low_n)) * 100

    d = k.rolling(window=smooth_1).mean()
    slow_k = d
    slow_d = slow_k.rolling(window=smooth_2).mean()

    return slow_k, slow_d
