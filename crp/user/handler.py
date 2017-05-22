# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource

from crp.taskmgr import *
from crp.models import User
from crp.user import user_blueprint
from crp.user.errors import user_errors

user_api = Api(user_blueprint, errors=user_errors)


class UserRegister(Resource):
    @classmethod
    def post(cls):
        code = 200
        msg = "success"
        user_set = {}

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('email', type=str)
            parser.add_argument('first_name', type=str)
            parser.add_argument('last_name', type=str)
            args = parser.parse_args()

            email = args.email
            first_name = args.first_name
            last_name = args.last_name

            User(email=email, first_name=first_name, last_name=last_name).save()

            user_set['email'] = email
            user_set['first_name'] = first_name
            user_set['last_name'] = last_name

            # TODO(TaskManager.task_start()): 定时任务示例代码
            TaskManager.task_start(SLEEP_TIME, TIMEOUT, query_modify_db, "testargs1", "testargs2")
        except Exception as e:
            code = 500
            msg = "internal server error"

        res = {
            "code": code,
            "result": {
                "res": user_set,
                "msg": msg
            }
        }

        return res, code

    @classmethod
    def get(cls):
        code = 200
        msg = "success"
        user_list = []
        user_set = {}

        try:
            data = User.objects.all()
            for i in data:
                if i.first_name:
                    user_set['email'] = i.email
                    user_set['first_name'] = i.first_name
                    user_set['last_name'] = i.last_name
                    user_list.append(user_set)
                    user_set = {}

        except Exception as e:
            code = 500
            msg = "internal server error"

        res = {
            'code': code,
            'result': {
                'res': user_list,
                'msg': msg
            }
        }

        return res, code


user_api.add_resource(UserRegister, '/users')
