# -*- coding: utf-8 -*-
from flask import Blueprint

az_blueprint = Blueprint('openstack_blueprint', __name__)

from . import handler, forms, errors
