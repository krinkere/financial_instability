import retrieve_stock_info
import datetime

tickers = retrieve_stock_info.retrieve_sp500_tickers(logit=False, pickle_jar_location="/data/unixhome/xkrinkere/PythonProjects/financial_instability/pickle_jar/")
start = datetime.datetime(2016, 1, 1)
end = datetime.date.today()

retrieve_stock_info.get_sp500_data(tickers=tickers, start=start, end=end, logit=False, pickle_jar_location="/data/unixhome/xkrinkere/PythonProjects/financial_instability/pickle_jar/")