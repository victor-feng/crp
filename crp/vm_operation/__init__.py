# -*- coding: utf-8 -*-
from flask import Blueprint

vm_operation_blueprint = Blueprint('vm_operation_blueprint', __name__)

from . import handler,views, forms, errors
