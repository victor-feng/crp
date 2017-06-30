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
from crp.glance_image import glance_image_blueprint
from crp.availability_zone import az_blueprint
from crp.mpc_resource import mpc_resource_blueprint
from crp.mpc_resource import instance_status_sync
from crp.flavor import flavor_blueprint
from crp.vm_operation import vm_operation_blueprint

def create_app(config_name):
    app = Flask(__name__)

    app.config.from_object(configs[config_name])
    db.init_app(app)

    logger_setting(app)
    openstack_client_setting()
    instance_status_sync()

    # swagger docs
    @app.route('/docs')
    def docs():
        return redirect('/static/docs/index.html')

    # blueprint
    app.register_blueprint(user_blueprint, url_prefix='/api/user')
    app.register_blueprint(resource_set_blueprint, url_prefix='/api/resource')
    app.register_blueprint(app_deploy_blueprint, url_prefix='/api/deploy')
    app.register_blueprint(glance_image_blueprint, url_prefix='/api/image')
    app.register_blueprint(az_blueprint, url_prefix='/api/az')
    app.register_blueprint(mpc_resource_blueprint, url_prefix='/api/mpc')
    app.register_blueprint(flavor_blueprint, url_prefix='/api/flavor')
    app.register_blueprint(vm_operation_blueprint, url_prefix='/api/vm_operation')
    return app
