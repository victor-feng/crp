# -*- coding: utf-8 -*-
from flask import Blueprint

resource_set_blueprint = Blueprint('resource_set_blueprint', __name__)

from . import handler, forms, errors
