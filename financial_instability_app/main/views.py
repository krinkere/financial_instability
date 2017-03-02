from datetime import datetime
from flask import render_template, session, redirect, url_for, flash
from . import main
from .forms import TickerForm
from .. import db
from ..models import Ticker, Sector, Portfolio


# Define routes
@main.route('/', methods=['GET', 'POST'])
def index():
    form = TickerForm()
    if form.validate_on_submit():
        ticker_symbol = Ticker.query.filter_by(ticker_symbol=form.ticker_symbol.data).first()
        if ticker_symbol is None:
            ticker = Ticker(ticker_symbol=form.ticker_symbol.data)
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
    from pandas_datareader import data
    import datetime
    from bokeh.plotting import figure, show, output_file
    from bokeh.embed import components
    from bokeh.resources import CDN

    start = datetime.datetime(2015, 1, 1)
    end = datetime.datetime(2017, 3, 2)

    ticker = session.get("ticker_symbol")
    df = data.DataReader(name=ticker, data_source="yahoo", start=start, end=end)

    def inc_dec(c, o):
        if c > o:
            value = "Increase"
        elif c < o:
            value = "Decrease"
        else:
            value = "Equal"
        return value

    df['Status'] = [inc_dec(c, o) for c, o in zip(df.Close, df.Open)]
    df['Middle'] = (df.Open+df.Close)/2
    df['Height'] = abs(df.Close-df.Open)

    p = figure(x_axis_type='datetime', width=1200, height=600, responsive=True)
    p.grid.grid_line_alpha=0.3

    hours_12 = 12*60*60*1000
    p.rect(df.index[df.Status == 'Increase'], df.Middle[df.Status == 'Increase'], hours_12,
           df.Height[df.Status == 'Increase'], fill_color='green', line_color='black')
    p.rect(df.index[df.Status == 'Decrease'], df.Middle[df.Status == 'Decrease'], hours_12,
           df.Height[df.Status == 'Decrease'], fill_color='red', line_color='black')
    p.segment(df.index, df.High, df.index, df.Low, color='Black')


    generated_script, div_tag = components(p)
    cdn_js = CDN.js_files[0]
    cdn_css = CDN.css_files[0]

    return render_template("candle_stick.html", ticker=session.get("ticker_symbol"), generated_script=generated_script,
                           div_tag=div_tag, cdn_js=cdn_js, cdn_css=cdn_css)