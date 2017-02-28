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