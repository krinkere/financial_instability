from flask import Flask
import argparse
from tornado.options import options
from tornado.wsgi import WSGIContainer
import signal
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import FallbackHandler, Application

is_closing = False


def signal_handler(signum, frame):
    global is_closing
    print('exiting...')
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        IOLoop.instance().stop()
        print('exit success')

financial_instability_app = Flask(__name__)


@financial_instability_app.route('/')
def index():
    return '<h1>Welcome to Instability</h1>'

arg_parser = argparse.ArgumentParser(description='Financial Instability Application')
arg_parser.add_argument("-p", "--port", help="Port to run application on",
                        type=int, action="store", dest="tcp_port")
options = arg_parser.parse_args()

if options.tcp_port is None:
    print "You must specify a port to host on, e.g. python financial_instability.py -p 5000"
    exit()

financial_instability_container = WSGIContainer(financial_instability_app)
signal.signal(signal.SIGINT, signal_handler)
PeriodicCallback(try_exit, 100).start()

application = Application([
    (r"/.*", FallbackHandler, dict(fallback=financial_instability_container)),
    ])

print "Routes"
print list(financial_instability_app.url_map.iter_rules())

if __name__ == '__main__':
    application.listen(options.tcp_port)
    IOLoop.instance().start()