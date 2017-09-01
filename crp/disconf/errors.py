# -*- coding: utf-8 -*-
disconf_errors = {
    'UserAlreadyExistsError': {
        'message': "A user with that username already exists.",
        'status': 409,
    },
    'ResourceDoesNotExist': {
        'message': "A resource with that ID no longer exists.",
        'status': 410,
        'extra': "Any extra information you want.",
    },
    'DeploymentNotFound': {
        'message': "Deployment Not Found",
        'status': 404,
    }
}
