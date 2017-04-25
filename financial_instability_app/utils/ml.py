from collections import Counter
import numpy as np
import pandas as pd
from sklearn import svm, cross_validation, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
import stock_utils


# ## Trading strategy 1:
# ## If the price rises more than 2% in the next 7 days, we're going to say that's a buy. If it drops more than 2% in
# ## the next 7 days, that's a sell. If it doesn't do either of those, then it's not moving enough, and we're going to
# ## just hold whatever our position is. If we have shares in that company, we do nothing, we keep our position. If we
# ## don't have shares in that company, we do nothing, we just wait.

# -1 is a sell, 0 is hold, and 1 is a buy
def buy_sell_hold(*args):
    cols = [c for c in args]
    requirement = 0.02
    for col in cols:
        if col > requirement:
            return 1
        if col < -requirement:
            return -1
    return 0


def extract_feature_sets(df, ticker):
    tickers, df = process_data_for_labels(df, ticker)

    df['{}_target'.format(ticker)] = list(map( buy_sell_hold,
                                               df['{}_1d'.format(ticker)],
                                               df['{}_2d'.format(ticker)],
                                               df['{}_3d'.format(ticker)],
                                               df['{}_4d'.format(ticker)],
                                               df['{}_5d'.format(ticker)],
                                               df['{}_6d'.format(ticker)],
                                               df['{}_7d'.format(ticker)] ))


    vals = df['{}_target'.format(ticker)].values.tolist()
    str_vals = [str(i) for i in vals]
    # print('Data spread:', Counter(str_vals))

    df.fillna(0, inplace=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    df.dropna(inplace=True)

    df_vals = df[[tkr for tkr in tickers]].pct_change()
    df_vals = df_vals.replace([np.inf, -np.inf], 0)
    df_vals.fillna(0, inplace=True)

    X = df_vals.values
    y = df['{}_target'.format(ticker)].values

    return X, y, df, Counter(str_vals)


def process_data_for_labels(df, ticker):
    hm_days = 7

    df.fillna(0, inplace=True)

    for i in range(1, hm_days + 1):
        df['{}_{}d'.format(ticker, i)] = (df[ticker].shift(-i) - df[ticker]) / df[ticker]

    df.fillna(0, inplace=True)

    tickers = df.columns.values.tolist()

    return tickers, df


def run_trading_strategy_1(df, ticker):
    X, y, df, data_spread = extract_feature_sets(df, ticker)

    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.25)

    # clf = neighbors.KNeighborsClassifier()

    clf = VotingClassifier([('lsvc', svm.LinearSVC()),
                            ('knn', neighbors.KNeighborsClassifier()),
                            ('rfor', RandomForestClassifier())])

    clf.fit(X_train, y_train)
    confidence = clf.score(X_test, y_test)
    # print('accuracy:', confidence)
    predictions = clf.predict(X_test)
    # print('predicted class counts:', Counter(predictions))

    return confidence, Counter(predictions), data_spread


def run_trading_strategy_2(df, ticker):
    column_name = "AdjClose_" + ticker
    # calculate fast moving average
    df = stock_utils.calculate_rolling_mean(df, window=20, column_name=column_name, result_column_name='20d')
    # calculate slow moving average
    df = stock_utils.calculate_rolling_mean(df, window=50, column_name=column_name, result_column_name='50d')
    # identify when fast moving average is below slow moving average and vise versa
    df['20d-50d'] = df['20d'] - df['50d']

    print df.tail(10)

    # determine the regime
    # Bull Regime - if the fast moving average is above the slow moving average. Value: 1
    # Bear Regime - if the fast moving average is below the slow moving average. Value: -1

    df["Regime"] = np.where(df['20d-50d'] > 0, 1, 0)  # np.where() is a vectorized if-else function, where a condition
                                                      # is checked for each component of a vector, and the first
                                                      # argument passed is used when the condition holds, and the other
                                                      # passed if it does not
    df["Regime"] = np.where(df['20d-50d'] < 0, -1, df["Regime"])

    print df["Regime"].value_counts()

    # Trading signals appear at regime changes. When a bullish regime begins, a buy signal is triggered, and when it
    # ends, a sell signal is triggered. Likewise, when a bearish regime begins, a sell signal is triggered, and when
    # the regime ends, a buy signal is triggered (this is of interest only if you ever will short the stock, or use
    # some derivative like a stock option to bet against the market).

    # To ensure that all trades close out, temporarily change the regime of the last row to 0
    regime_orig = df.ix[-1, "Regime"]
    df.ix[-1, "Regime"] = 0
    df["Signal"] = np.sign(df["Regime"] - df["Regime"].shift(1))
    # Restore original regime data
    df.ix[-1, "Regime"] = regime_orig

    print df.tail()
    print df["Signal"].value_counts()

    # You may notice that the system as it currently stands isn’t very robust, since even a fleeting moment when the
    # fast moving average is above the slow moving average triggers a trade, resulting in trades that end immediately
    # (which is bad if not simply because realistically every trade is accompanied by a fee that can quickly erode
    # earnings). Additionally, every bullish regime immediately transitions into a bearish regime, and if you were
    # constructing trading systems that allow both bullish and bearish bets, this would lead to the end of one trade
    # immediately triggering a new trade that bets on the market in the opposite direction, which again seems finnicky.
    # A better system would require more evidence that the market is moving in some particular direction. But we will
    # not concern ourselves with these details for now.

    # Let’s now try to identify what the prices of the stock is at every buy and every sell.
    print df.loc[df["Signal"] == 1, column_name]
    print df.loc[df["Signal"] == -1, column_name]

    # Create a DataFrame with trades, including the price at the trade and the regime under which the trade is made.
    signals = pd.concat([
        pd.DataFrame({"Price": df.loc[df["Signal"] == 1, column_name],
                      "Regime": df.loc[df["Signal"] == 1, "Regime"],
                      "Signal": "Buy"}),
        pd.DataFrame({"Price": df.loc[df["Signal"] == -1, column_name],
                      "Regime": df.loc[df["Signal"] == -1, "Regime"],
                      "Signal": "Sell"}),
    ])
    signals.sort_index(inplace=True)

    print signals

    # Let's see the profitability of long trades
    long_profits = pd.DataFrame({
        "Price":
            signals.loc[(signals["Signal"] == "Buy") & signals["Regime"] == 1, "Price"],
        "Profit":
            pd.Series(signals["Price"] - signals["Price"].shift(1)).loc[signals.loc[(signals["Signal"].shift(1) == "Buy") & (signals["Regime"].shift(1) == 1)].index].tolist(),
        "End Date":
            signals["Price"].loc[signals.loc[(signals["Signal"].shift(1) == "Buy") & (signals["Regime"].shift(1) == 1)].index].index
    })

    print long_profits