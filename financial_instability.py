from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask.ext.script import Manager
from flask.ext.moment import Moment
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
import os
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required


basedir = os.path.abspath(os.path.dirname(__file__))
financial_instability_app = Flask(__name__)
manager = Manager(financial_instability_app)
bootstrap = Bootstrap(financial_instability_app)
moment = Moment(financial_instability_app)
financial_instability_app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
# financial_instability_app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(financial_instability_app)

# Cross-Site Request Forgery (CSRF) Protection
financial_instability_app.config['SECRET_KEY'] = 'hard to guess string'


# Define routes
@financial_instability_app.route('/', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))
    return render_template("index.html", form=form, ticker=session.get("ticker_symbol"),
                           current_time=datetime.utcnow(), known=session.get('known', False))


@financial_instability_app.route('/user/<name>')
def user(name):
    return render_template("user.html", name=name)


@financial_instability_app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@financial_instability_app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

print "Available Routes:"
print list(financial_instability_app.url_map.iter_rules())


class TickerForm(Form):
    ticker_symbol = StringField('Stock symbol?', validators=[Required()])
    submit = SubmitField('Submit')


class Ticker (db.Model):
    __tablename__ = 'tickers'
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(64), unique=True, index=True)

    sector_id = db.Column(db.Integer, db.ForeignKey('stock_sector.id'))

    def __repr__(self):
        return '<Stock: %r>' % self.ticker_symbol


class Sector (db.Model):
    __tablename__ = 'stock_sector'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)

    # has to define lazy as dynamic, otherwise all() will be executed by default
    tickers = db.relationship('Ticker', backref='sector', lazy='dynamic')

    def __repr__(self):
        return '<Stock Sector: %r>' % self.name


class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # tickers = db.relationship('Ticker', backref='portfolio')

    def __repr__(self):
        return '<Portfolio: %r>' % self.name


# Start the application
if __name__ == '__main__':
    manager.run()