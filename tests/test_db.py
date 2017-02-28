import unittest
from financial_instability_app import create_app, db
from financial_instability_app.models import Sector, Ticker


class InfrastructureTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_sector_population(self):
        # https://biz.yahoo.com/p/s_conameu.html
        basic_materials = Sector(name="Basic Materials")
        conglomerates = Sector(name="Conglomerates")
        consumer_goods = Sector(name="Consumer Goods")
        financial = Sector(name="Financial")
        healthcare = Sector(name="Healthcare")
        industrial_goods = Sector(name="Industrial Goods")
        services = Sector(name="Services")
        technology = Sector(name="Technology")
        utilities = Sector(name="Utilities")

        db.session.add_all([basic_materials, conglomerates, consumer_goods,
                            financial, healthcare, industrial_goods,
                            services, technology, utilities])
        db.session.commit()

        print "\nPrint all sectors"
        print Sector.query.all()

        self.assertTrue(Sector.query.count() == 9)

    def test_sector_delete(self):
        # https://biz.yahoo.com/p/s_conameu.html
        basic_materials = Sector(name="Basic Materials")
        conglomerates = Sector(name="Conglomerates")
        consumer_goods = Sector(name="Consumer Goods")
        financial = Sector(name="Financial")
        healthcare = Sector(name="Healthcare")
        industrial_goods = Sector(name="Industrial Goods")
        services = Sector(name="Services")
        technology = Sector(name="Technology")
        utilities = Sector(name="Utilities")

        db.session.add_all([basic_materials, conglomerates, consumer_goods,
                            financial, healthcare, industrial_goods,
                            services, technology, utilities])
        db.session.commit()

        print "\nPrint all sectors"
        print Sector.query.all()

        self.assertTrue(Sector.query.count() == 9)

        # Delete
        db.session.delete(conglomerates)
        db.session.commit()

        self.assertTrue(Sector.query.count() == 8)

    def test_stock_population(self):
        technology = Sector(name="Technology")
        financial = Sector(name="Financial")
        db.session.add_all([financial, technology])

        aapl = Ticker(ticker_symbol="AAPL2", sector=technology)
        db.session.add(aapl)
        msft = Ticker(ticker_symbol="MSFT", sector=technology)
        db.session.add(msft)
        afl = Ticker(ticker_symbol="AFL", sector=financial)
        db.session.add(afl)

        db.session.commit()

        print "\nTicker all sectors"
        print Ticker.query.all()
        print "Print all sectors in technology sectors"
        print Ticker.query.filter_by(sector=technology).all()
        print "Debug previous query"
        print str(Ticker.query.filter_by(sector=technology))

        self.assertTrue(Ticker.query.count() == 3)

    def test_stock_rename(self):
        technology = Sector(name="Technology")
        financial = Sector(name="Financial")
        db.session.add_all([financial, technology])

        aapl = Ticker(ticker_symbol="AAPL2", sector=technology)
        db.session.add(aapl)
        msft = Ticker(ticker_symbol="MSFT", sector=technology)
        db.session.add(msft)
        afl = Ticker(ticker_symbol="AFL", sector=financial)
        db.session.add(afl)

        db.session.commit()

        self.assertTrue(Ticker.query.filter_by(ticker_symbol="AAPL2").count() == 1)

        # Modify
        aapl.ticker_symbol = "AAPL"
        db.session.add(aapl)
        db.session.commit()

        self.assertTrue(Ticker.query.filter_by(ticker_symbol="AAPL").count() == 1)
