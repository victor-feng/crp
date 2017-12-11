# -*- coding: utf-8 -*-
from flask import Blueprint

dns_set_blueprint = Blueprint('dns_set_blueprint', __name__)

from . import handler, views, forms, errors
