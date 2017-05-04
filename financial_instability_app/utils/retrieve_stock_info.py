from datetime import datetime
import time
import df_utils
import pandas_datareader.data as web
import logging
import utils
import os.path
import pandas as pd
import requests
import bs4 as bs
from pandas_datareader._utils import RemoteDataError

# Uncomment to decrease default level of logging to debug, ie. get the most data
# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("retrieve_stock_info")
logger.setLevel(logging.INFO)
fh = logging.FileHandler('logs/retrieve_stock_info.log')
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                              "%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh)


def retrieve_data(ticker, start, end, file_name, file_prefix,  df_generator):
    file_location = "pickle_jar/" + file_prefix + "_" + start.strftime("%Y-%m-%d") + "_" + end.strftime("%Y-%m-%d") + "_" + \
                    file_name + ".pickle"
    if os.path.exists(file_location):
        # retrieve from pickle file
        logger.info("-- Retrieving from %s" % file_location)
        df = pd.read_pickle(file_location)
    else:
        logger.info("-- Web pull for %s [%s : %s]" % (ticker, start.strftime("%Y-%m-%d"),
                                                                   end.strftime("%Y-%m-%d")))
        df = df_generator(ticker, start, end)
        utils.save_to_pickle(df, file_location)
    return df


def retrieve_sp500_tickers():
    file_location = "pickle_jar/sp500list_" + time.strftime("%d%m%Y")

    if os.path.exists(file_location):
        # retrieve from pickle file
        logger.info("-- Retrieving from %s" % file_location)
        tickers = pd.read_pickle(file_location)
    else:
        resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        soup = bs.BeautifulSoup(resp.text, 'lxml')

        table = soup.find('table', {'class': 'wikitable sortable'})
        tickers = []
        for row in table.findAll('tr')[1:]:
            ticker = row.findAll('td')[0].text
            tickers.append(ticker)

        tickers = sorted(tickers)
        utils.save_to_pickle(tickers, file_location)

    return tickers


def get_stock_volume_data(ticker, start, end):
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="stock_volume_data", file_prefix=ticker,
                       df_generator=get_stock_volume_data_df_generator)
    return df


def get_stock_volume_data_df_generator(ticker, start, end):
    df = get_stock_from_yahoo(ticker, start, end)
    df = df_utils.slice_dataframe_by_columns(df, ['Volume_' + ticker])
    return df


def get_stock_data(ticker, start, end):
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="stock_data", file_prefix=ticker,
                       df_generator=get_stock_data_df_generator)
    return df


def get_stock_data_df_generator(ticker, start, end):
    df = get_us_stock_data_from_web(ticker, start, end)
    df = df_utils.slice_dataframe_by_columns(df, ['AdjClose_' + ticker])
    return df


def adj_close_data(ticker, start, end):
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="close_data", file_prefix=ticker,
                       df_generator=adj_close_plot_df_generator)
    return df


def adj_close_plot_df_generator(ticker, start, end):
    df = get_stock_from_yahoo(ticker, start, end)
    return df


def get_adj_close_data(ticker, start, end):
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="comparison_data",
                       file_prefix='-'.join(ticker), df_generator=get_adj_close_data_df_generator)
    return df


def get_adj_close_data_df_generator(ticker, start, end):
    df = get_adj_close_data_from_web(ticker, start, end)
    return df


def get_sp500_data(tickers, start, end):
    file_location = "pickle_jar/SP500crawl_" + start.strftime("%Y-%m-%d") + "_" + end.strftime("%Y-%m-%d") + "_"
    sp500pickle = file_location+"sp500pickle.pickle"
    validtickerspickle = file_location + "validtickerspickle.pickle"

    if os.path.exists(sp500pickle):
        # retrieve from pickle file
        logger.info("-- Retrieving from %s" % sp500pickle)
        df = pd.read_pickle(sp500pickle)
        valid_tickers = pd.read_pickle(validtickerspickle)
    else:
        logger.info("-- Web pull for %s [%s : %s]" % ("S&P500", start.strftime("%Y-%m-%d"),
                                                      end.strftime("%Y-%m-%d")))
        df, valid_tickers = get_sp500_data_df_generator(tickers, start, end)
        utils.save_to_pickle(df, sp500pickle)
        utils.save_to_pickle(valid_tickers, validtickerspickle)

    return df, valid_tickers


def get_sp500_data_df_generator(tickers, start, end):
    df, valid_tickers = get_stock_data_from_web(tickers, start, end)
    columns = []
    for ticker in valid_tickers:
        columns.append('AdjClose_' + ticker)
    df = df_utils.slice_dataframe_by_columns(df, columns)
    df.columns = valid_tickers
    return df, valid_tickers


def get_us_comparison_data(ticker, start, end):
    tickers = [ticker, 'SPY']
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="us_comparison_data", file_prefix=ticker,
                       df_generator=get_us_comparison_data_df_generator)
    return df, tickers


def get_us_comparison_data_df_generator(ticker, start, end):
    tickers = [ticker, 'SPY']
    df = get_us_stock_data_from_web(ticker, start, end)
    df = df_utils.slice_dataframe_by_columns(df, ['AdjClose_' + ticker, 'AdjClose_SPY'])
    df.columns = tickers
    return df


def get_global_comparison_data(ticker, start, end):
    tickers = [ticker, 'Frankfurt', 'Paris', 'Hong Kong', 'Japan', 'Australia']
    df = retrieve_data(ticker=ticker, start=start, end=end, file_name="global_comparison_data", file_prefix=ticker,
                       df_generator=get_global_comparison_data_df_generator)
    return df, tickers


def get_global_comparison_data_df_generator(ticker, start, end):
    tickers = [ticker, 'Frankfurt', 'Paris', 'Hong Kong', 'Japan', 'Australia']
    df = get_global_stock_data_from_web(ticker, start, end)
    df = df_utils.slice_dataframe_by_columns(df,
                                             ['AdjClose_' + ticker, 'AdjClose_^GDAXI',
                                              'AdjClose_^FCHI', 'AdjClose_^HSI',
                                              'AdjClose_^N225', 'AdjClose_^AXJO'])
    df.columns = tickers
    return df


def get_stock_from_yahoo(symbol, start, end):
    """
    Downloads Stock from Yahoo Finance.
    Returns pandas dataframe.
    """
    try:
        df = web.DataReader(symbol, data_source='yahoo', start=start, end=end)
    except RemoteDataError:
        return None

    def inc_dec(c, o):
        if c > o:
            value = "Increase"
        elif c < o:
            value = "Decrease"
        else:
            value = "Equal"
        return value

    df['Status'] = [inc_dec(c, o) for c, o in zip(df.Close, df.Open)]
    df['Middle'] = (df.Open + df.Close) / 2
    df['Height'] = abs(df.Close - df.Open)

    return append_symbol_to_columns(df, symbol)


def append_symbol_to_columns(df, symbol_name):
    """
    Utility method that takes data frame (df) and appends symbol_name at the end of its column names
    """
    df.columns.values[-4] = 'AdjClose'
    df.columns = df.columns + '_' + symbol_name
    df['DailyReturn_%s' % symbol_name] = df['AdjClose_%s' % symbol_name].pct_change()

    return df


def get_stock_data_from_web(tickers, start, end):
    """
    Collects predictors data from Yahoo Finance.
    Returns a list of dataframes.
    """
    logger.info("Received %r tickers" % len(tickers))
    bad_tickers = []
    for i, ticker in enumerate(tickers):
        logger.info("Processing ticker '%s'" % ticker)
        curr_df = get_stock_from_yahoo(ticker, start, end)
        if i == 0:
            df = get_stock_from_yahoo(ticker, start, end)
        else:
            if curr_df is not None:
                df = df_utils.join_dataframes(curr_df, df)
            else:
                logger.warn("Ticker %s could not be retrieved from Yahoo Finance" % ticker)
                bad_tickers.append(ticker)
    logger.info("Could not process %r tickers. \n %r" % (len(bad_tickers), bad_tickers))

    good_tickers = [ticker for ticker in tickers if ticker not in bad_tickers]
    return df, good_tickers


def get_adj_close_data_from_web(ticker, start, end):
    logger.info("Processing ticker '%s'" % ticker)
    df = get_stock_from_yahoo(ticker, start, end)
    df = df.ix[:, 'AdjClose_' + ticker]
    return df


def get_us_stock_data_from_web(ticker, start, end):
    """
    Collects predictors data from Yahoo Finance and quandl.
    Returns a list of dataframes.
    """
    # start = parser.parse(start_string)
    # end = parser.parse(end_string)

    # Get US market data
    sp500 = get_stock_from_yahoo('SPY', start, end)

    # Get ticker data
    stock = get_stock_from_yahoo(ticker, start, end)
    df = df_utils.join_dataframes(stock, sp500)

    return df


def get_global_stock_data_from_web(ticker, start, end):
    """
    Collects predictors data from Yahoo Finance and quandl.
    Returns a list of dataframes.
    """
    # start = parser.parse(start_string)
    # end = parser.parse(end_string)

    # Get major markets data
    nasdaq = get_stock_from_yahoo('^IXIC', start, end)
    frankfurt = get_stock_from_yahoo('^GDAXI', start, end)
    # london = getStock('^FTSE', start, end)
    paris = get_stock_from_yahoo('^FCHI', start, end)
    hong_kong = get_stock_from_yahoo('^HSI', start, end)
    japan = get_stock_from_yahoo('^N225', start, end)
    australia = get_stock_from_yahoo('^AXJO', start, end)
    sp500 = get_stock_from_yahoo('SPY', start, end)

    # Get ticker data
    stock = get_stock_from_yahoo(ticker, start, end)
    df = df_utils.join_dataframes(stock, nasdaq)
    df = df_utils.join_dataframes(df, frankfurt)
    df = df_utils.join_dataframes(df, paris)
    df = df_utils.join_dataframes(df, hong_kong)
    df = df_utils.join_dataframes(df, japan)
    df = df_utils.join_dataframes(df, australia)
    df = df_utils.join_dataframes(df, sp500)

    # return [stock, nasdaq, frankfurt, paris, hong_kong, japan, australia, sp500]
    return df


def construct_yahoo_finance_url(ticker, start_date, end_date, freq):
    """
    In some rare case that we can't download data by using pandas, we can download it manually.

    Sample of URL to download Apple Inc stock info:
    http://chart.finance.yahoo.com/table.csv?s=AAPL&a=9&b=17&c=2016&d=10&e=17&f=2016&g=d&ignore=.csv

    s - ticker symbol
    a/b/c - start date
    d/e/f - end data
    g - frequency
    """
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    s = ticker.replace("^", "%5E")

    if start_date.month-1 < 10:
        a = "0"+str(start_date.month-1)
    else:
        a = str(start_date.month-1)
    b = str(start_date.day)
    c = str(start_date.year)

    if end_date.month - 1 < 10:
        d = "0" + str(end_date.month - 1)
    else:
        d = str(end_date.month - 1)
    e = str(end_date.day)
    f = str(end_date.year)

    g = freq

    url = "http://chart.finance.yahoo.com/table.csv?s=" + s + "&a=" + a + "&b=" + b + "&c=" + c + "&d=" + d + "&e=" + e \
          + "&f=" + f + "&g=" + g + "&ignore=.csv"
    return url


def download_cvs(file_path, url):
    import urllib2

    # In order to fool websites into thinking that it is a human that makes the request we need to add header attribute
    # use http://www.whoishostingthis.com/tools/user-agent/ to find "What's my User Agent"
    hdr={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
         'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
         'Accept-Language':'en-US,en;q=0.8',
         'Accept-Encoding':'none',
         'Connection':'keep-alive'}
    web_request = urllib2.Request(url, headers=hdr)
    try:
        page = urllib2.urlopen(web_request)
        # save the contents of the web request in a variable called 'content'
        # These are literally the file from the URL (i.e. what you'd get if you downloaded the URL manually)
        content = page.read()

        # we are simply reading the bytes in content and writing them to local file. this way we are agnostic to what
        # kind of file we are trying to download ie zip files, cvs, excel, etc
        with open(file_path, 'wb') as output:
            output.write(bytearray(content))

    except urllib2.HTTPError, e:
        print e.fp.read()


def get_stock_from_yahoo_manually(symbol, start, end):
    import pandas as pd

    url = construct_yahoo_finance_url(symbol, start, end, "d")
    output_cvs_file = "output/" + symbol + ".csv"
    download_cvs(output_cvs_file, url)
    df = pd.read_csv(output_cvs_file, index_col=0)
    return df


# print get_stock_data_from_web("AAPL", "2016-10-01", "2016-10-25")
# print get_stock_from_yahoo_manually("AAPL", "2015-01-01", "2016-01-01").tail()

