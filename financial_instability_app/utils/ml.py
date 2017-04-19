from collections import Counter
import numpy as np
from sklearn import svm, cross_validation, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier


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