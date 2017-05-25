# -*- coding: utf-8 -*-
from flask import Blueprint

docker_deploy_blueprint = Blueprint('docker_deploy_blueprint', __name__)

from . import handler, errors
