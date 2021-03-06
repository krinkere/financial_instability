import numpy as np
import pandas as pd


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


def calculate_adj_rate(adj_close, close):
    return adj_close / close


def calculate_adj_numbers(df, ticker):
    adj_rate = calculate_adj_rate(df['AdjClose_' + ticker], df['Close_' + ticker])
    df['AdjOpen_' + ticker] = adj_rate * df['Open']
    df['AdjHigh_' + ticker] = adj_rate * df['High']
    df['AdjLow_' + ticker] = adj_rate * df['Low']

    return df


def generate_swing_index_timeserie(df):
    current_values = df[1:].values
    prior_values = df[:-1].values

    dates = []
    swing_indexes = []

    for counter, values in enumerate(current_values):
        date = df.index[counter + 1]
        dates.append(date)

        open_prior = prior_values[counter][0]
        open_current = values[0]
        high_current = values[1]
        low_current = values[2]
        close_prior = prior_values[counter][3]
        close_current = values[3]

        swing_index = calculate_swing_index(open_prior, open_current, high_current, low_current, close_prior,
                                            close_current, 75)

        swing_indexes.append(swing_index)

    swing_index_df = pd.DataFrame(swing_indexes, index=dates, columns=['Swing Index'])

    swing_index_df['Accumulated Swing Index'] = swing_index_df['Swing Index'].cumsum()

    return swing_index_df


def calculate_swing_index(open_prior, open_current, high_current, low_current, close_prior, close_current, limit_move):
    """
    The Swing Index is a technical indicator that attempts to predict future short-term price action:

    When the Swing Index crosses over zero, then a trader might expect short-term price movement upward.
    When the Swing Index crosses below zero, then a trader might expect short-term price movement downward.

    50 * ((CY - C + 0.5 * (CY - OY) + 0.25 * (C- O)) / R) * (K / T)

    """

    def calc_R(H2, C1, L2, O1):
        x = H2 - C1
        y = L2 - C1
        z = H2 - L2

        # print x
        # print y
        # print z

        if z < x > y:
            R = (H2 - C1) - (.5 * (L2 - C1)) + (.25 * (C1 - O1))
        elif x < y > z:
            R = (L2 - C1) - (.5 * (H2 - C1)) + (.25 * (C1 - O1))
        else:
            R = (H2 - L2) + (.25 * (C1 - O1))

        return R

    def calc_K(H2, L2, C1):
        x = H2 - C1
        y = L2 - C1

        if x > y:
            return x
        else:
            return y
    # $75 for gold, c50 for silver
    L = limit_move
    R = calc_R(high_current, close_prior, low_current, open_prior)
    K = calc_K(high_current, low_current, close_prior)

    swing_index = 50 * ((close_current - close_prior + (.5 * (close_current - open_current)) +
                         (.25 * (close_prior - open_prior))) / R) * (K / L)

    return swing_index


def calculate_direction_move(df):
    df['MoveUp'] = df['High'] - df['High'].shift()
    df['MoveDown'] = df['Low'].shift() - df['Low']

    df['PDM'] = 0
    df['PDM'][(df['MoveUp'] > 0) & (df['MoveUp'] > df['MoveDown'])] = df['MoveUp']

    df['NDM'] = 0
    df['NDM'][(df['MoveDown'] > 0) & (df['MoveDown'] > df['MoveUp'])] = df['MoveDown']

    return df


def calculate_direction_index(df):
    df['PDI'] = (pd.ewma(df['PDM'], span=14) / df['AvgTrueRange']) * 100
    df['NDI'] = (pd.ewma(df['NDM'], span=14) / df['AvgTrueRange']) * 100

    return df


def calculate_average_directional_index(df):
    df['ADX'] = (pd.ewma(abs(df['PDI']-df['NDI']), span=14) / (df['PDI']+df['NDI'])) * 100

    return df


def calculate_chaikin_money_flow(df):
    # The calculation for Chaikin Money Flow (CMF) has three distinct steps for this example we will use a 21 Period CMF
    # 1. Find the Money Flow Multiplier
    #    [(Close  -  Low) - (High - Close)] /(High - Low) = Money Flow Multiplier
    #
    money_flow_multiplier = (2 * df['Close'] - df['High'] - df['Low']) / (df['High'] - df['Low'])
    # 2. Calculate Money Flow Volume
    #    Money Flow Multiplier x Volume for the Period = Money Flow Volume
    money_flow_volume = money_flow_multiplier * df['Volume']
    # 3. Calculate The CMF
    #    21 Period Sum of Money Flow Volume / 21 Period Sum of Volume = 21 Period CMF
    df['Chaikin'] = money_flow_volume.rolling(window=21).sum() / df['Volume'].rolling(window=21).sum()

    return df


def calculate_average_true_range(df):
    df['ATR1'] = abs(df['High'] - df['Low'])
    df['ATR2'] = abs(df['High'] - df['Close'].shift())
    df['ATR3'] = abs(df['Low'] - df['Close'].shift())
    df['TrueRange'] = df[['ATR1', 'ATR2', 'ATR3']].max(axis=1)
    df['AvgTrueRange'] = pd.ewma(df['TrueRange'], span=14)
    return df

# How not to calculate it :)
# def calculate_average_true_range(df):
#     current_values = df[1:].values
#     prior_values = df[:-1].values
#
#     dates = []
#     true_ranges = []
#
#     for counter, values in enumerate(current_values):
#         date = df.index[counter + 1]
#         dates.append(date)
#
#         high_current = values[1]
#         low_current = values[2]
#         close_prior = prior_values[counter][3]
#
#         true_range = calculate_true_range(high_current, low_current, close_prior)
#
#         true_ranges.append(true_range)
#
#     true_range_df = pd.DataFrame(true_ranges, index=dates, columns=['True Range'])
#
#     true_range_df['Average True Range'] = pd.ewma(true_range_df['True Range'], span=14)
#
#     return true_range_df


