from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask.ext.script import Manager
from flask.ext.moment import Moment
from datetime import datetime

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

financial_instability_app = Flask(__name__)
manager = Manager(financial_instability_app)
bootstrap = Bootstrap(financial_instability_app)
moment = Moment(financial_instability_app)

# Cross-Site Request Forgery (CSRF) Protection
financial_instability_app.config['SECRET_KEY'] = 'hard to guess string'


# Define routes
@financial_instability_app.route('/', methods=['GET', 'POST'])
def index():
    form = TickerForm()
    if form.validate_on_submit():
        session["ticker"] = form.ticker.data
        return redirect(url_for('index'))
    return render_template("index.html", form=form, ticker=session.get("ticker"), current_time=datetime.utcnow())


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
    ticker = StringField('Stock symbol?', validators=[Required()])
    submit = SubmitField('Submit')

# Start the application
if __name__ == '__main__':
    manager.run()