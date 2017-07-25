# -*- coding: utf-8 -*-

import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options

define('port', type=int, default=8001)
#define('port', type=int, default=5000)

# deploy or debug
define('mode', default='debug')

from crp import create_app
from config import APP_ENV

def main():
    options.parse_command_line()

    if options.mode.lower() == "debug":
        from tornado import autoreload
        autoreload.start()

    app = create_app(APP_ENV)
    # app.run(host='0.0.0.0', debug=True)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(options.port)
    logging.warn("[CRP] CRP is running on: localhost:%d", options.port)
    IOLoop.instance().start()

if __name__ == '__main__':
    main()

