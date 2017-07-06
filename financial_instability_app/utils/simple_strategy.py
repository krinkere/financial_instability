import pandas as pd
import numpy as np
import datetime
import pandas_datareader.data as web


# MACD, MACD Signal and MACD histogram
def MACD(df, fastperiod=12, slowperiod=26, signalperiod=9):
    """
    Moving Average Convergence/Divergence(MACD)
    The MACD indicator (or "oscillator") is a collection of three time series calculated
    from historical price data: the MACD series proper, the "signal" or "average" series,
    and the "divergence" series which is the difference between the two.

    The most commonly used values are 12, 26, and 9 days, that is, MACD(12,26,9):
        MACD Line = (12-period EMA  26-period EMA)
        Signal Line = 9 Day Exponential Moving Average of MACD
        Histogram = MACD Line - Signal Line
    Return: list of [MACD Line, Signal Line, Histogram], all in pandas Series format.
    """
    EMAfast = pd.Series(pd.ewma(df['Close'], span = fastperiod))
    EMAslow = pd.Series(pd.ewma(df['Close'], span = slowperiod))
    MACD = pd.Series(EMAfast - EMAslow, name = 'MACD_' + str(fastperiod) + '_' + str(slowperiod))
    MACDsignal = pd.Series(pd.ewma(MACD, span = signalperiod), name = 'MACDsignal_' + str(fastperiod) + '_' + str(slowperiod))
    MACDhist = pd.Series(MACD - MACDsignal, name = 'MACDhist_' + str(fastperiod) + '_' + str(slowperiod))
    df = df.join(MACD)
    df = df.join(MACDsignal)
    df = df.join(MACDhist)
    return df


# Bollinger Bands
def BBANDS(df, movingaverage=12):
    MA = pd.Series(pd.rolling_mean(df['Close'], movingaverage), name = 'BB_middle')
    MSD = pd.Series(pd.rolling_std(df['Close'], movingaverage))

    BBupper = pd.Series(MA + 2 * MSD, name = 'BB_upper')
    BBlower = pd.Series(MA - 2 * MSD, name = 'BB_lower')

    df = df.join(MA)
    df = df.join(BBupper)
    df = df.join(BBlower)
    return df


def RSI(prices, n=14):
    """
    The Relative Strength Index (RSI) is a momentum oscillator.
    It oscillates between 0 and 100.
    It is considered overbought/oversold when it's over 70/below 30.
    Some traders use 80/20 to be on the safe side.
    RSI becomes more accurate as the calculation period (min_periods)
    increases.
    This can be lowered to increase sensitivity or raised to decrease
    sensitivity.
    10-day RSI is more likely to reach overbought or oversold levels than
    20-day RSI. The look-back parameters also depend on a security's
    volatility.
    RSI can also be used to identify the general trend.
    The RSI was developed by J. Welles Wilder and was first introduced in his
    article in the June, 1978 issue of Commodities magazine, now known as
    Futures magazine. It is detailed in his book New Concepts In Technical
    Trading Systems.
    http://www.csidata.com/?page_id=797
    http://stockcharts.com/help/doku.php?id=chart_school:technical_indicators:relative_strength_in
    """
    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1.+rs)

    for i in range(n, len(prices)):
        delta = deltas[i-1]
        if delta>0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(n-1) + upval)/n
        down = (down*(n-1) + downval)/n

        rs = up/down
        rsi[i] = 100. - 100./(1.+rs)

    return rsi


pd.set_option('display.width', 1000)
start = datetime.datetime(2016, 1, 1)
end = datetime.date.today()
df = web.DataReader('TDOC', data_source='google', start=start, end=end)
df = MACD(df)
df = BBANDS(df)
close_prices = df['Close']
df['RSI'] = RSI(close_prices)

# df1 = df[['RSI',  'RSI_rw']]
# print df1

print df