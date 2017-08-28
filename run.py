# -*- coding: utf-8 -*-
from crp import create_app
from config import APP_ENV
from crp.openstack import openstack_client_setting

if __name__ == '__main__':
    app = create_app(APP_ENV)
    openstack_client_setting()
    app.run(host='0.0.0.0', port=8001)
