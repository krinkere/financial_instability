import numpy as np


def normalize_data(df):
    """Normalize stock prices using the first row of the dataframe"""
    return df/df.ix[0, :]


def calculate_daily_returns(df):
    """Compute and return the daily return values."""
    daily_returns = df.copy()  # copy given DataFrame to match size and column names
    # compute daily returns for row 1 onwards
    # we need to use 'values' so that we won't try to do the operation on two DataFrames, in which case their index
    # would be matched instead hence ignoring the shift
    # manually:
    # daily_returns[1:] = (df[1:] / df[:-1].values) - 1
    # or with panda's help (note that pandas leaves the 0th row full of NaNs)
    daily_returns = (df / df.shift(1)) - 1
    daily_returns.ix[0, :] = 0  # set daily returns for row 0 to zeros
    return daily_returns


def calculate_cumulative_returns(df):
    df = calculate_daily_returns(df)
    return df.cumsum()


def calculate_cumulative_returns_from_daily(df):
    return df.cumsum()


def calculate_rolling_mean(df, window=20, column_name='', result_column_name='rolling_mean'):
    """
    Rolling mean is a way to compute the mean over window of period. If you were to plot the rolling mean stats, you
    would be able to come up with a graph that generally follows the stock prices with certain lag.

    With rolling mean you need to watch for cross overs, i.e. the time that stock crosses the rolling mean line and goes
    down (or vise versa) it would could signify that it would come up toward the mean at some point, hence might be a good
    time to buy. The challenge here is to guess where to buy the stock since it might still go down or up.
    """
    if column_name:
        df[result_column_name] = df[column_name].rolling(window=window, center=False).mean()
        return df
    return df.rolling(window=window, center=False).mean()


def calculate_bollinger_bands(df, window=20, column_name=''):
    """
    Bollinger Bands - Like it was mentioned above once stock prices cross rolling mean it might be an indication to buy or
    sell, but when? Bollinger Bands measire rolling standard deviation and plot 2 sigma plots above and below rolling mean
    It is expected that once stock price reaches Bollinger Bands it would most likely to change direction.

    Hence to compute Bollinger Bands you need:
    1. Compute rolling mean
    2. Compute rolling standard deviation
    3. Compute upper and lower bands
    """
    # roll_mean = calculate_rolling_mean(df, window, column_name)
    roll_std = calculate_rolling_std(df, window, column_name)
    df = roll_std
    df['upper_band'] = df['rolling_mean'] + 2 * df['rolling_std']
    df['lower_band'] = df['rolling_mean'] - 2 * df['rolling_std']
    # lower_band = roll_mean - 2 * roll_std
    return df


def calculate_rolling_std(df, window, column_name=''):
    if column_name:
        df['rolling_std'] = df[column_name].rolling(window=window, center=False).std()
        return df
    return df.rolling(window=window, center=False).std()


def find_beta_alpha(df, col_name1, col_name2):
    beta, alpha = np.polyfit(df[col_name1], df[col_name2], 1)
    return beta, alpha


def generate_correlation_dataframe(df):
    df_corr = df.corr()
    return df_corr


def calculate_correlation(df, stock1, stock2):
    corr_matrix = calculate_correlation_matrix(df)
    return corr_matrix[stock1][stock2]


def calculate_correlation_matrix(df):
    return df.corr(method='pearson')