from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import datetime
from wtforms.fields.html5 import DateField


class CheckMediaForm(Form):
    ticker_symbol = StringField('Submit new stock symbol')
    start = StringField('Start Date')
    end = StringField('End Date')


class TickerForm(Form):
    ticker_symbol = StringField('Submit new stock symbol', validators=[DataRequired()])
    start = DateField('Start Date', default=datetime.datetime(2016, 1, 1))
    end = DateField('End Date', default=datetime.date.today())
    submit = SubmitField('Submit')

    def validate(self):
        if not Form.validate(self):
            return False

        result = True
        if self.start.data > self.end.data:
            result = False
            self.start.errors.append('Start date can\'t be after end date')

        if self.start.data > datetime.date.today():
            result = False
            self.start.errors.append('Start date can\'t be in the future')

        if self.end.data > datetime.date.today():
            result = False
            self.end.errors.append('End date can\'t be in the future')

        return result