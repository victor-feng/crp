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
# dev, test, prod
define('deploy', default='dev')
# True, False
define('mpc_sync', type=bool, default=False)

from crp import create_app
from config import APP_ENV

def main():
    options.parse_command_line()

    if options.mode.lower() == "debug":
        from tornado import autoreload
        autoreload.start()

    app = create_app(APP_ENV)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(options.port)
    logging.warn("[CRP] CRP is running on: localhost:%d", options.port)

    from crp.openstack import openstack_client_setting
    from crp.mpc_resource import instance_status_sync

    OPENRC_PATH = app.config['OPENRC_PATH']
    openstack_client_setting()
    logging.warn("[CRP] Openstack client is inited")
    MPC_URL = app.config['MPC_URL']

    instance_status_sync(mpc_sync=options.mpc_sync)

    IOLoop.instance().start()


if __name__ == '__main__':
    main()

