from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, make_response
from . import main
from .forms import TickerForm
from .. import db
from ..models import Ticker, Sector, Portfolio
from ..utils import retrieve_stock_info
from ..utils import visualization
from ..utils import df_utils

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
        flash("Data is being retrieved for %s" % form.ticker_symbol.data)
        return redirect(url_for('main.index'))
    return render_template("index.html", form=form, ticker=session.get("ticker_symbol"),
                           current_time=datetime.utcnow(), known=session.get('known', False))


@main.route('/corr', methods=['GET'])
def corr():
    return render_template("corr.html", ticker=session.get("ticker_symbol"))


@main.route('/candle_plot', methods=['GET'])
def candle_plot():
    import datetime

    start = datetime.datetime(2015, 1, 1)
    end = datetime.date.today()

    ticker = session.get("ticker_symbol")
    df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_candlestick_plot(df, ticker)

    return render_template("candle_stick.html", ticker=session.get("ticker_symbol"), generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/adj_close_plot', methods=['GET'])
def adj_close_plot():
    import datetime

    start = datetime.datetime(2015, 1, 1)
    end = datetime.date.today()

    ticker = session.get("ticker_symbol")
    df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_single_line_plot(df, ticker)

    return render_template("adj_close_plot.html", ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/global_comparison_plot', methods=['GET'])
def global_comparison_plot():
    import datetime

    start = datetime.datetime(2016, 1, 1)
    end = datetime.date.today()

    tickers = ['AAPL', 'SPY', 'Nasdaq', 'Frankfurt', 'Paris', 'Hong Kong', 'Japan', 'Australia', 'S&P 500']
    df = retrieve_stock_info.get_stock_data_from_web("AAPL", start, end)
    df = df_utils.slice_dataframe_by_columns(df, ['AdjClose_AAPL', 'AdjClose_SPY', 'AdjClose_^IXIC', 'AdjClose_^GDAXI',
                                                  'AdjClose_^FCHI', 'AdjClose_^HSI',
                                                  'AdjClose_^N225', 'AdjClose_^AXJO', 'AdjClose_SPY'])
    df.columns = tickers

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_multi_line_plot(df, tickers)

    return render_template("global_comparison_plot.html", ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)

@main.route('/available_stocks', methods=['GET'])
def available_stocks():
    return render_template("available_stocks.html")


@main.route('/stock_analysis', methods=['GET'])
def stock_analysis():
    import datetime

    start = datetime.datetime(2016, 1, 1)
    end = datetime.date.today()
    aapl = retrieve_stock_info.get_stock_from_yahoo("AAPL", start, end)
    goog = retrieve_stock_info.get_stock_from_yahoo("GOOG", start, end)
    stocks = df_utils.join_dataframes(aapl, goog)

    adj_close_data = df_utils.slice_dataframe_by_columns(stocks, ['AdjClose_AAPL', 'AdjClose_GOOG'])
    adj_close_data.columns = ['AAPL', 'GOOG']

    figdata_png = visualization.plot_stock_analysis(adj_close_data)
    return render_template("stock_analysis.html", figdata_png=figdata_png)


# Example of displaying a mathplotlib image
@main.route('/test.png', methods=['GET'])
def simple():
    import datetime
    import StringIO
    import random

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response
