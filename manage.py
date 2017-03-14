import os
from financial_instability_app import create_app, db
from financial_instability_app.models import Ticker, Sector, Portfolio
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


financial_instability_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(financial_instability_app)
migrate = Migrate(financial_instability_app, db)


def make_shell_context():
    return dict(financial_instability_app=financial_instability_app, db=db, Ticker=Ticker, Sector=Sector,
                Portfolio=Portfolio)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """ Run the unit test """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def create_db():
    """ Create initial database """
    db.create_all()


@manager.command
def destroy_db():
    """ Destroy database """
    db.drop_all()


# Start the application
if __name__ == '__main__':
    print "Available Routes:"
    print list(financial_instability_app.url_map.iter_rules())
    manager.run()