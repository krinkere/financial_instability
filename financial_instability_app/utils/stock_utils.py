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