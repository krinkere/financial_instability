import financial_instability

db = financial_instability.db
db.drop_all()
db.create_all()

# https://biz.yahoo.com/p/s_conameu.html
basic_materials = financial_instability.Sector(name="Basic Materials")
conglomerates = financial_instability.Sector(name="Conglomerates")
consumer_goods = financial_instability.Sector(name="Consumer Goods")
financial = financial_instability.Sector(name="Financial")
healthcare = financial_instability.Sector(name="Healthcare")
industrial_goods = financial_instability.Sector(name="Industrial Goods")
services = financial_instability.Sector(name="Services")
technology = financial_instability.Sector(name="Technology")
utilities = financial_instability.Sector(name="Utilities")

db.session.add_all([basic_materials, conglomerates, consumer_goods,
                    financial, healthcare, industrial_goods,
                    services, technology, utilities])

aapl = financial_instability.Ticker(ticker_symbol="AAPL2", sector=technology)
db.session.add(aapl)
msft = financial_instability.Ticker(ticker_symbol="MSFT", sector=technology)
db.session.add(msft)
afl = financial_instability.Ticker(ticker_symbol="AFL", sector=financial)
db.session.add(afl)

db.session.commit()

# Modify
aapl.ticker_symbol = "AAPL"
db.session.add(aapl)
db.session.commit()

# Delete
db.session.delete(conglomerates)
db.session.commit()

# Query
print "Print all sectors"
print financial_instability.Sector.query.all()
print "Ticker all sectors"
print financial_instability.Ticker.query.all()
print "Print all sectors in technology sectors"
print financial_instability.Ticker.query.filter_by(sector=technology).all()
print "Debug previous query"
print str(financial_instability.Ticker.query.filter_by(sector=technology))
print "Tickers in Technology sector"
print technology.tickers.count()