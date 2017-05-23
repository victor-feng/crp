# -*- coding: utf-8 -*-
resource_set_errors = {
    'ResourceSetAlreadyExistsError': {
        'message': "A resource set with that ID already exists.",
        'status': 409,
    },
    'ResourceSetDoesNotExist': {
        'message': "A resource set with that ID no longer exists.",
        'status': 410,
        'extra': "Any extra information you want.",
    },
}
