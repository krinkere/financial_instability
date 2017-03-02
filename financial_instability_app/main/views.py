from datetime import datetime
from flask import render_template, session, redirect, url_for, flash
from . import main
from .forms import TickerForm
from .. import db
from ..models import Ticker, Sector, Portfolio
from ..utils import retrieve_stock_info
from ..utils import visualization

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


@main.route('/corr', methods=['GET', 'POST'])
def corr():
    return render_template("corr.html", ticker=session.get("ticker_symbol"))


@main.route('/candle_plot', methods=['GET', 'POST'])
def candle_plot():
    import datetime

    start = datetime.datetime(2015, 1, 1)
    end = datetime.date.today()

    ticker = session.get("ticker_symbol")
    df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_candlestick_plot(df, ticker)

    return render_template("candle_stick.html", ticker=session.get("ticker_symbol"), generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/adj_close_plot', methods=['GET', 'POST'])
def adj_close_plot():
    import datetime

    start = datetime.datetime(2015, 1, 1)
    end = datetime.date.today()

    ticker = session.get("ticker_symbol")
    df = retrieve_stock_info.get_stock_from_yahoo(ticker, start, end)

    generated_script, div_tag, cdn_js, cdn_css = visualization.generate_single_line_plot(df, ticker)

    return render_template("adj_close_plot.html", ticker=session.get("ticker_symbol"),
                           generated_script=generated_script, div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)


@main.route('/available_stocks', methods=['GET', 'POST'])
def available_stocks():
    return render_template("available_stocks.html")
