from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask.ext.script import Manager
from flask.ext.moment import Moment
from datetime import datetime

financial_instability_app = Flask(__name__)
manager = Manager(financial_instability_app)
bootstrap = Bootstrap(financial_instability_app)
moment = Moment(financial_instability_app)


# Define routes
@financial_instability_app.route('/')
def index():
    return render_template("index.html", current_time=datetime.utcnow())


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

# Start the application
if __name__ == '__main__':
    manager.run()