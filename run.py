# -*- coding: utf-8 -*-
from crp import create_app
from config import APP_ENV

if __name__ == '__main__':
    app = create_app(APP_ENV)
    # app.run(host='0.0.0.0', port=8000)
    app.run(host='0.0.0.0', port=8001)
