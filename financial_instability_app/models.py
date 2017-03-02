from . import db


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
    sector = db.Column(db.String(64), index=True)
    industry = db.Column(db.String(64), index=True)

    # has to define lazy as dynamic, otherwise all() will be executed by default
    tickers = db.relationship('Ticker', backref='sector', lazy='dynamic')

    def __repr__(self):
        return '<Stock Sector: %r Industry: %r>' % (self.sector, self.industry)


class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # tickers = db.relationship('Ticker', backref='portfolio')

    def __repr__(self):
        return '<Portfolio: %r>' % self.name