# -*- coding: utf-8 -*-
from flask import Flask, redirect
from flask_restful import Resource, Api
from config import configs
from models import db
from crp.user import user_blueprint
from crp.log import logger_setting, Log
from crp.openstack import openstack_client_setting
from crp.res_set import resource_set_blueprint
from crp.app_deployment import app_deploy_blueprint

def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(configs[config_name])
    db.init_app(app)

    logger_setting(app)
    openstack_client_setting()

    # swagger docs
    @app.route('/docs')
    def docs():
        return redirect('/static/docs/index.html')

    # blueprint
    app.register_blueprint(user_blueprint, url_prefix='/api/user')
    app.register_blueprint(resource_set_blueprint, url_prefix='/api/resource')
    app.register_blueprint(app_deploy_blueprint, url_prefix='/api/deploy')
    return app
