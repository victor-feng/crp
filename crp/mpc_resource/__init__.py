# -*- coding: utf-8 -*-
from flask import Blueprint

mpc_resource_blueprint = Blueprint('mpc_resource_blueprint', __name__)

from . import handler, forms, errors
