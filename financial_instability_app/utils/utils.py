import time
import functools
import logging
import datetime
import pickle


def log_time(function_name):
    def log_it(func):
        @functools.wraps(func)
        def measure_and_log_time(*args, **kwargs):
            start_time = time.time()
            returned_view = func(*args, **kwargs)
            # logging
            logger = logging.getLogger("utils")
            logger.setLevel(logging.INFO)
            fh = logging.FileHandler('logs/retrieve_stock_info.log')
            formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                                          "%Y-%m-%d %H:%M:%S")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logger.info("--- Function %s ran in %s seconds ---" % (function_name, time.time() - start_time))
            return returned_view
        return measure_and_log_time
    return log_it


# Date time
def get_ticker_start_date_end_date(session):
    ticker = get_ticker(session)
    start, end = get_start_date_end_date(session)

    return ticker, start, end


def get_ticker(session):
    ticker = session.get("ticker_symbol")

    return ticker


def get_start_date_end_date(session):
    start = datetime.datetime(2016, 1, 1)
    end = datetime.date.today()

    if session.get("start_date"):
        start = session.get("start_date")
        start = datetime.datetime.strptime(start, '%a, %d %b %Y %X GMT')
    if session.get("end_date"):
        end = session.get("end_date")
        end = datetime.datetime.strptime(end, '%a, %d %b %Y %X GMT')

    return start, end


# Pickle
def save_to_pickle(df, file_location):
    pickle_out = open(file_location, 'wb')
    pickle.dump(df, pickle_out)
    pickle_out.close()


