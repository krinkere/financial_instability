from collections import Counter
import numpy as np
import pandas as pd
from sklearn import svm, cross_validation, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
import stock_utils
import visualization


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

    # You may notice that the system as it currently stands isn't very robust, since even a fleeting moment when the
    # fast moving average is above the slow moving average triggers a trade, resulting in trades that end immediately
    # (which is bad if not simply because realistically every trade is accompanied by a fee that can quickly erode
    # earnings). Additionally, every bullish regime immediately transitions into a bearish regime, and if you were
    # constructing trading systems that allow both bullish and bearish bets, this would lead to the end of one trade
    # immediately triggering a new trade that bets on the market in the opposite direction, which again seems finnicky.
    # A better system would require more evidence that the market is moving in some particular direction. But we will
    # not concern ourselves with these details for now.

    # Let's now try to identify what the prices of the stock is at every buy and every sell.
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

    # Create a simulated portfolio of $1,000,000.
    # Rules:
    #   Investing only 10% of the portfolio in any trade
    #   Exiting the position if losses exceed 20% of the value of the trade.
    # We need to get the low of the price during each trade.
    tradeperiods = pd.DataFrame({"Start": long_profits.index,
                                 "End": long_profits["End Date"]})
    long_profits["Low"] = tradeperiods.apply(lambda x: min(df.loc[x["Start"]:x["End"], "Low_" + ticker]), axis=1)

    print long_profits

    # Now we have all the information needed to simulate this strategy in long_profits
    cash = 1000000

    backtest = pd.DataFrame({"Start Port. Value": [],
                             "End Port. Value": [],
                             "End Date": [],
                             "Shares": [],
                             "Share Price": [],
                             "Trade Value": [],
                             "Profit per Share": [],
                             "Total Profit": [],
                             "Stop-Loss Triggered": []})

    port_value = .1  # Max proportion of portfolio bet on any trade
    batch = 100  # Number of shares bought per batch
    stop_loss = .2  # % of trade loss that would trigger a stop_loss

    for index, row in long_profits.iterrows():
        # Maximum number of batches of stocks invested in
        batches = np.floor(cash * port_value) // np.ceil(batch * row["Price"])
        # How much money is put on the line with each trade
        trade_val = batches * batch * row["Price"]
        # Account for the stop-loss
        if row["Low"] < (1 - stop_loss) * row["Price"]:
            share_profit = np.round((1 - stop_loss) * row["Price"], 2)
            stop_trig = True
        else:
            share_profit = row["Profit"]
            stop_trig = False
        # Compute profits
        profit = share_profit * batches * batch
        # Add a row to the backtest data frame containing the results of the trade
        backtest = backtest.append(pd.DataFrame({
            "Start Port. Value": cash,
            "End Port. Value": cash + profit,
            "End Date": row["End Date"],
            "Shares": batch * batches,
            "Share Price": row["Price"],
            "Trade Value": trade_val,
            "Profit per Share": share_profit,
            "Total Profit": profit,
            "Stop-Loss Triggered": stop_trig
        }, index=[index]))
        cash = max(0, cash + profit)

    print backtest

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_single_line_plot(backtest, "End Port. Value")

    return generated_script, div_tag, cdn_js, cdn_css


def ma_crossover_orders(stocks, fast, slow):
    """
    :param stocks: A list of tuples, the first argument in each tuple being a string containing the ticker symbol of
    each stock (or however you want the stock represented, so long as it's unique), and the second being a pandas
    DataFrame containing the stocks, with a "AdjClose" column and indexing by date (like the data frames returned by
    the Yahoo! Finance API)

    :param fast: Integer for the number of days used in the fast moving average
    :param slow: Integer for the number of days used in the slow moving average

    :return: pandas DataFrame containing stock orders

    This function takes a list of stocks and determines when each stock would be bought or sold depending on a moving
    average crossover strategy, returning a data frame with information about when the stocks in the portfolio are
    bought or sold according to the strategy
    """
    fast_str = str(fast) + 'd'
    slow_str = str(slow) + 'd'
    ma_diff_str = fast_str + '-' + slow_str

    trades = pd.DataFrame({"Price": [], "Regime": [], "Signal": []})
    for s in stocks:
        # Get the moving averages, both fast and slow, along with the difference in the moving averages
        column_name = "AdjClose_" + s[0]
        s[1][fast_str] = np.round(s[1][column_name].rolling(window=fast, center=False).mean(), 2)
        s[1][slow_str] = np.round(s[1][column_name].rolling(window=slow, center=False).mean(), 2)
        s[1][ma_diff_str] = s[1][fast_str] - s[1][slow_str]

        # np.where() is a vectorized if-else function, where a condition is checked for each component of a vector, and
        # the first argument passed is used when the condition holds, and the other passed if it does not
        s[1]["Regime"] = np.where(s[1][ma_diff_str] > 0, 1, 0)
        # We have 1's for bullish regimes and 0's for everything else. Below I replace bearish regimes's values with -1,
        # and to maintain the rest of the vector, the second argument is apple["Regime"]
        s[1]["Regime"] = np.where(s[1][ma_diff_str] < 0, -1, s[1]["Regime"])
        # To ensure that all trades close out, I temporarily change the regime of the last row to 0
        regime_orig = s[1].ix[-1, "Regime"]
        s[1].ix[-1, "Regime"] = 0
        s[1]["Signal"] = np.sign(s[1]["Regime"] - s[1]["Regime"].shift(1))
        # Restore original regime data
        s[1].ix[-1, "Regime"] = regime_orig

        # Get signals
        signals = pd.concat([
            pd.DataFrame({"Price": s[1].loc[s[1]["Signal"] == 1, column_name],
                         "Regime": s[1].loc[s[1]["Signal"] == 1, "Regime"],
                         "Signal": "Buy"}),
            pd.DataFrame({"Price": s[1].loc[s[1]["Signal"] == -1, column_name],
                         "Regime": s[1].loc[s[1]["Signal"] == -1, "Regime"],
                         "Signal": "Sell"}),
        ])
        signals.index = pd.MultiIndex.from_product([signals.index, [s[0]]], names=["Date", "Symbol"])
        trades = trades.append(signals)

    trades.sort_index(inplace=True)
    trades.index = pd.MultiIndex.from_tuples(trades.index, names=["Date", "Symbol"])

    return trades


def backtest(signals, cash, port_value=.1, batch=100):
    """
    :param signals: pandas DataFrame containing buy and sell signals with stock prices and symbols, like that returned
    by ma_crossover_orders

    :param cash: integer for starting cash value
    :param port_value: maximum proportion of portfolio to risk on any single trade
    :param batch: Trading batch sizes

    :return: pandas DataFrame with backtesting results

    This function backtests strategies, with the signals generated by the strategies being passed in the signals
    DataFrame. A fictitious portfolio is simulated and the returns generated by this portfolio are reported.
    """

    # Constant for which element in index represents symbol
    SYMBOL = 1
    # Will contain how many stocks are in the portfolio for a given symbol
    portfolio = dict()
    # Tracks old trade prices for determining profits
    port_prices = dict()
    # Dataframe that will contain backtesting report
    results = pd.DataFrame({"Start Cash": [],
                            "End Cash": [],
                            "Portfolio Value": [],
                            "Type": [],
                            "Shares": [],
                            "Share Price": [],
                            "Trade Value": [],
                            "Profit per Share": [],
                            "Total Profit": []})

    for index, row in signals.iterrows():
        # These first few lines are done for any trade
        shares = portfolio.setdefault(index[SYMBOL], 0)
        trade_val = 0
        batches = 0
        # Shares could potentially be a positive or negative number (cash_change will be added in the end; negative
        # shares indicate a short)
        cash_change = row["Price"] * shares
        # For a given symbol, a position is effectively cleared
        portfolio[index[SYMBOL]] = 0

        old_price = port_prices.setdefault(index[SYMBOL], row["Price"])
        portfolio_val = 0
        for key, val in portfolio.items():
            portfolio_val += val * port_prices[key]

        if row["Signal"] == "Buy" and row["Regime"] == 1:
            # Entering a long position
            # Maximum number of batches of stocks invested in
            batches = np.floor((portfolio_val + cash) * port_value) // np.ceil(batch * row["Price"])
            # How much money is put on the line with each trade
            trade_val = batches * batch * row["Price"]
            # We are buying shares so cash will go down
            cash_change -= trade_val
            # Recording how many shares are currently invested in the stock
            portfolio[index[SYMBOL]] = batches * batch
            # Record price
            port_prices[index[SYMBOL]] = row["Price"]
            old_price = row["Price"]
        elif row["Signal"] == "Sell" and row["Regime"] == -1:
            # Entering a short
            # Do nothing; can we provide a method for shorting the market?
            pass
        #else:
            #raise ValueError("I don't know what to do with signal " + row["Signal"])

        # Compute profit per share; old_price is set in such a way that entering a position results in a profit of zero
        pprofit = row["Price"] - old_price

        # Update report
        results = results.append(pd.DataFrame({
            "Start Cash": cash,
            "End Cash": cash + cash_change,
            "Portfolio Value": cash + cash_change + portfolio_val + trade_val,
            "Type": row["Signal"],
            "Shares": batch * batches,
            "Share Price": row["Price"],
            "Trade Value": abs(cash_change),
            "Profit per Share": pprofit,
            "Total Profit": batches * batch * pprofit
        }, index=[index]))
        # Final change to cash balance
        cash += cash_change

    results.sort_index(inplace=True)
    results.index = pd.MultiIndex.from_tuples(results.index, names=["Date", "Symbol"])

    return results


def run_trading_strategy_3(stocks, df_market, fast=20, slow=50):
    signals = ma_crossover_orders(stocks, fast, slow)

    print signals

    bk = backtest(signals, 1000000)

    print bk

    # Backtesting is only part of evaluating the efficacy of a trading strategy. We would like to benchmark the
    # strategy, or compare it to other available (usually well-known) strategies in order to determine how well we have
    # done.

    # The efficient market hypothesis claims that it is all but impossible for anyone to beat the market. Thus, one
    # should always buy an index fund that merely reflects the composition of the market. SPY is an exchange-traded
    # fund (a mutual fund that is traded on the market like a stock) whose value effectively represents the value of
    # the stocks in the S&P 500 stock index. By buying and holding SPY, we are effectively trying to match our returns
    # with the market rather than beat it.

    return visualization.generate_aggregated_plot_line_plot(bk, "Portfolio Value", df_market)
