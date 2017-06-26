# -*- coding: utf-8 -*-
from flask import Blueprint

flavor_blueprint = Blueprint('flavor_blueprint', __name__)

from . import handler, forms, errors
