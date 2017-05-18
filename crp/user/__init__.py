# -*- coding: utf-8 -*-
from flask import Blueprint

user_blueprint = Blueprint('user_blueprint', __name__)

from . import handler, forms, errors
