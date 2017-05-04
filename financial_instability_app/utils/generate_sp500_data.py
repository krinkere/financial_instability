from ..utils import retrieve_stock_info
import datetime

tickers = retrieve_stock_info.retrieve_sp500_tickers()
start = datetime.datetime(2015, 1, 1)
end = datetime.date.today()

retrieve_stock_info.get_sp500_data(tickers=tickers, start=start, end=end)