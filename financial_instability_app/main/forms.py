from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class TickerForm(Form):
    ticker_symbol = StringField('Submit new stock symbol', validators=[DataRequired()])
    submit = SubmitField('Submit')