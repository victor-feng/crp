# -*- coding: utf-8 -*-
from flask import Blueprint

app_deploy_blueprint = Blueprint('app_deploy_blueprint', __name__)

from . import handler, forms, errors
