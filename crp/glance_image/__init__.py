# -*- coding: utf-8 -*-
from flask import Blueprint

glance_image_blueprint = Blueprint('glance_image_blueprint', __name__)

from . import handler,views, forms, errors
