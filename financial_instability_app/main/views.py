import os.path
from flask import render_template, session, redirect, url_for, flash, make_response
from . import main
from .forms import TickerForm
from .. import db
from ..models import Ticker, Sector, Portfolio
from ..utils import retrieve_stock_info
from ..utils import visualization
from ..utils import df_utils
from ..utils import stock_utils
from ..utils import utils
import pandas as pd
import datetime


# Define routes
@main.route('/', methods=['GET', 'POST'])
def index():
    from urllib import urlopen
    from lxml.html import parse

    def get_sector(ticker):
        tree = parse(urlopen('http://www.google.com/finance?&q=NASDAQ%3A' + ticker))
        return tree.xpath("//a[@id='sector']")[0].text, tree.xpath("//a[@id='sector']")[0].getnext().text

    form = TickerForm()
    if form.validate_on_submit():
        ticker_symbol = Ticker.query.filter_by(ticker_symbol=form.ticker_symbol.data).first()
        if ticker_symbol is None:
            sector_name, industry_name = get_sector(form.ticker_symbol.data)
            sector = Sector.query.filter_by(sector=sector_name, industry=industry_name).first()
            if sector is None:
                sector = Sector(sector=sector_name, industry=industry_name)
                db.session.add(sector)
            ticker = Ticker(ticker_symbol=form.ticker_symbol.data, sector=sector)

            db.session.add(ticker)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session["ticker_symbol"] = form.ticker_symbol.data
        session["start_date"] = form.start.data
        session["end_date"] = form.end.data
        flash("Data is being retrieved for %s" % form.ticker_symbol.data)
        return redirect(url_for('main.index'))
    return render_template("index.html", form=form, ticker=session.get("ticker_symbol"),
                           current_time=datetime.datetime.utcnow(), known=session.get('known', False))


@main.route('/corr', methods=['GET'])
@utils.log_time("corr")
def corr():
    df, tickers, ticker = us_get_comparison_data()
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css, pearson_corr, comp_ticket \
        = visualization.generate_corr_plot(daily_returns, tickers)

    return render_template("corr.html", ticker=session.get("ticker_symbol"), generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css, pearson_corr=pearson_corr,
                           comp_ticket=comp_ticket)


@main.route('/candle_plot', methods=['GET'])
@utils.log_time("candle_plot")
def candle_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_candlestick_plot(df, ticker)

    return render_template("candle_stick.html", ticker=session.get("ticker_symbol"), generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/bollinger_bands_plot', methods=['GET'])
@utils.log_time("bollinger_bands_plot")
def bollinger_bands_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    df = stock_utils.calculate_rolling_mean(df, column_name="AdjClose_"+ticker)
    df = stock_utils.calculate_bollinger_bands(df, column_name="AdjClose_"+ticker)

    # df = df_utils.join_dataframes(df, roll_mean)
    # df = df_utils.join_dataframes(df, upper_band)
    # df = df_utils.join_dataframes(df, lower_band)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_bollinger_plot(df, ticker)

    return render_template("bollinger_bands_plot.html", ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/trade_volume_plot')
@utils.log_time("trade_volume_plot")
def trade_volume_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_volume_data(ticker, start, end)
    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_volume_bar_plot(df, ticker)

    return render_template("volume_histo_plot.html", ticker=ticker, generated_script=generated_script, div_tag=div_tag,
                           cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/adj_close_histo_plot')
@utils.log_time("adj_close_histo_plot")
def adj_close_histo_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css, mean, std = \
        visualization.generate_adj_close_histo_plot(daily_returns, ticker)

    return render_template("adj_close_histo_plot.html", ticker=ticker, generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css, mean=mean, std=std)


@main.route('/mov_av_20day_plot')
@utils.log_time("mov_av_20day_plot")
def mov_av_20day_plot():
    return mov_av_plot(20)


@main.route('/mov_av_50day_plot')
@utils.log_time("mov_av_50day_plot")
def mov_av_50day_plot():
    return mov_av_plot(50)


@main.route('/mov_av_200day_plot')
@utils.log_time("mov_av_200day_plot")
def mov_av_200day_plot():
    return mov_av_plot(200)


def mov_av_plot(num_days):
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    df = retrieve_stock_info.get_stock_data(ticker, start, end)
    column_name = "AdjClose_" + ticker
    df = stock_utils.calculate_rolling_mean(df, window=num_days, column_name=column_name)

    tickers = ["rolling_mean", column_name]
    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(df, tickers=tickers,
                                                                                        labels=[str(num_days) +
                                                                                                " day rolling mean",
                                                                                                ticker])

    return render_template("mov_av_plot.html", num_days=num_days, ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/adj_close_plot', methods=['GET'])
@utils.log_time("adj_close_plot")
def adj_close_plot():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    file_location = "pickle_jar/" + ticker + "_" + start.strftime("%Y-%m-%d") + "_" + end.strftime(
        "%Y-%m-%d") + "_yahoo.pickle"
    if os.path.exists(file_location):
        # retrieve from pickle file
        print ("retrieving information from pickle file %s" % file_location)
        df = pd.read_pickle(file_location)
    else:
        print ("retrieving information for %s for time range %s - %s" % (ticker, start, end))
        df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)
        utils.save_to_pickle(df, file_location)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_single_line_plot(df,
                                                                                         column='AdjClose_' + ticker,
                                                                                         ticker=ticker)
    return render_template("adj_close_plot.html", ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/us_comparison_plot_adjclose', methods=['GET'])
@utils.log_time("us_comparison_plot_adjclose")
def us_comparison_plot_adjclose():
    df, tickers, ticker = us_get_comparison_data()
    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(df, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="close prices", economy_type="U.S.",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/us_comparison_plot_norm', methods=['GET'])
@utils.log_time("us_comparison_plot_norm")
def us_comparison_plot_norm():
    df, tickers, ticker = us_get_comparison_data()
    normalized_data = stock_utils.normalize_data(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(normalized_data, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="normalized prices", economy_type="U.S.",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/us_comparison_plot_daily', methods=['GET'])
@utils.log_time("us_comparison_plot_daily")
def us_comparison_plot_daily():
    df, tickers, ticker = us_get_comparison_data()
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(daily_returns, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="daily changes", economy_type="U.S.",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/us_comparison_plot_cum', methods=['GET'])
@utils.log_time("us_comparison_plot_cum")
def us_comparison_plot_cum():
    df, tickers, ticker = us_get_comparison_data()
    cum_returns = stock_utils.calculate_cumulative_returns(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(cum_returns, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="cumulative changes", economy_type="U.S.",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


def us_get_comparison_data():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)
    tickers = [session.get("ticker_symbol"), 'SPY']

    file_location = "pickle_jar/" + ticker + "_" + start.strftime("%Y-%m-%d") + "_" + end.strftime(
        "%Y-%m-%d") + "_us_corr.pickle"
    if os.path.exists(file_location):
        # retrieve from pickle file
        df = pd.read_pickle(file_location)
    else:
        df = retrieve_stock_info.get_us_stock_data_from_web(ticker, start, end)
        df = df_utils.slice_dataframe_by_columns(df, ['AdjClose_' + ticker, 'AdjClose_SPY'])
        df.columns = tickers
        utils.save_to_pickle(df, file_location)

    return df, tickers, ticker





@main.route('/global_comparison_plot_adjclose', methods=['GET'])
@utils.log_time("global_comparison_plot_adjclose")
def global_comparison_plot_adjclose():
    df, tickers, ticker = get_global_comparison_data()

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(df, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="close prices", economy_type="Global",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/global_comparison_plot_norm', methods=['GET'])
@utils.log_time("global_comparison_plot_norm")
def global_comparison_plot_norm():
    df, tickers, ticker = get_global_comparison_data()
    normalized_data = stock_utils.normalize_data(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(normalized_data, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="normalized prices", economy_type="Global",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/global_comparison_plot_daily', methods=['GET'])
@utils.log_time("global_comparison_plot_daily")
def global_comparison_plot_daily():
    df, tickers, ticker = get_global_comparison_data()
    daily_returns = stock_utils.calculate_daily_returns(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(daily_returns, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="daily changes", economy_type="Global",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/global_comparison_plot_cum', methods=['GET'])
@utils.log_time("global_comparison_plot_cum")
def global_comparison_plot_cum():
    df, tickers, ticker = get_global_comparison_data()
    cum_returns = stock_utils.calculate_cumulative_returns(df)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(cum_returns, tickers=tickers,
                                                                                        labels=tickers)

    return render_template("comparison_plot.html", ticker=ticker, comparator_type="cumulative changes", economy_type="Global",
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


def get_global_comparison_data():
    ticker, start, end = utils.get_ticker_start_date_end_date(session)

    tickers = [session.get("ticker_symbol"), 'Frankfurt', 'Paris', 'Hong Kong', 'Japan', 'Australia']
    file_location = "pickle_jar/" + ticker + "_" + start.strftime("%Y-%m-%d") + "_" + end.strftime(
        "%Y-%m-%d") + "_global.pickle"
    if os.path.exists(file_location):
        # retrieve from pickle file
        df = pd.read_pickle(file_location)
    else:
        df = retrieve_stock_info.get_global_stock_data_from_web(ticker, start, end)
        df = df_utils.slice_dataframe_by_columns(df,
                                                 ['AdjClose_' + ticker, 'AdjClose_^GDAXI',
                                                  'AdjClose_^FCHI', 'AdjClose_^HSI',
                                                  'AdjClose_^N225', 'AdjClose_^AXJO'])
        df.columns = tickers
        utils.save_to_pickle(df, file_location)

    return df, tickers, ticker


@main.route('/available_stocks', methods=['GET'])
@utils.log_time("available_stocks")
def available_stocks():
    return render_template("available_stocks.html")


# @main.route('/stock_analysis', methods=['GET'])
# @utils.log_time("stock_analysis")
# def stock_analysis():
#     start, end = utils.get_start_end_dates(session)
#     aapl = retrieve_stock_info.get_stock_from_yahoo("AAPL", start, end)
#     goog = retrieve_stock_info.get_stock_from_yahoo("GOOG", start, end)
#     stocks = df_utils.join_dataframes(aapl, goog)
#
#     adj_close_data = df_utils.slice_dataframe_by_columns(stocks, ['AdjClose_AAPL', 'AdjClose_GOOG'])
#     adj_close_data.columns = ['AAPL', 'GOOG']
#
#     figdata_png = visualization.plot_stock_analysis(adj_close_data)
#     return render_template("stock_analysis.html", figdata_png=figdata_png)


# Example of displaying a mathplotlib image
@main.route('/test.png', methods=['GET'])
@utils.log_time("simple")
def simple():
    import datetime
    import StringIO
    import random

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    fig = Figure()
    ax = fig.add_subplot(111)
    x = []
    y = []
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now += delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response