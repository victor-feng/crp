# -*- coding: utf-8 -*-
from flask import Blueprint

disconf_blueprint = Blueprint('disconf_blueprint', __name__)

from . import handler, forms, errors
