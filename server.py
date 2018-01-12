# -*- coding: utf-8 -*-

import logging

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
import os
import tornado.log


define('port', type=int, default=8001)
#define('port', type=int, default=5000)

# deploy or debug
define('mode', default='debug')
# dev, test, prod
define('deploy', default='dev')
# True, False
define('mpc_sync', type=bool, default=False)
options.parse_command_line()
os.system('rm -rf config.py')
os.system('rm -rf config.pyc')
os.system('rm -rf conf')
os.system('ln -s conf.d/%s  conf '%(options.deploy))
os.system('ln -s conf/config.py  config.py')
os.system('> /etc/ansible/hosts')

from crp import create_app
from config import APP_ENV
from crp.log import logger_setting

def main():

    if options.mode.lower() == "debug":
        from tornado import autoreload
        autoreload.start()

    app = create_app(APP_ENV)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(options.port)
    logging.warn("[CRP] CRP is running on: localhost:%d", options.port)

    from crp.openstack import openstack_client_setting
    from crp.openstack2 import openstack2_client_setting
    from crp.mpc_resource import instance_status_sync

    OPENRC_PATH = app.config['OPENRC_PATH']
    OPENRC2_PATH = app.config['OPENRC2_PATH']
    openstack_client_setting()
    openstack2_client_setting()
    logging.warn("[CRP] Openstack client is inited")
    MPC_URL = app.config['MPC_URL']

    instance_status_sync(mpc_sync=options.mpc_sync)
    #set app log
    logger = logger_setting(app)
    fm = tornado.log.LogFormatter(
    fmt='[%(asctime)s]%(color)s[%(levelname)s]%(end_color)s[%(pathname)s %(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    tornado.log.enable_pretty_logging(logger=logger)
    logger.handlers[0].setFormatter(fm)

    IOLoop.instance().start()


if __name__ == '__main__':
    main()

