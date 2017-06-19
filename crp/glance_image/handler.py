# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource

from crp.taskmgr import *
from crp.models import User
from crp.glance_image import glance_image_blueprint
from crp.glance_image.errors import user_errors
from crp.openstack import OpenStack
from crp.log import Log

glance_image_api = Api(glance_image_blueprint, errors=user_errors)


class ImageListAPI(Resource):

    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('image_format', type=str, location='args')
        parser.add_argument('image_name', type=str, location='args')

        args = parser.parse_args()
        filters = {}
        if args.image_format:
            filters['disk_format'] = args.image_format
        # if args.image_name:
        #     filters['name'] = args.image_name

        res_images = []
        try:
            glance_cli = OpenStack.glance_client()
            kwargs = {'filters': filters}
            images = glance_cli.images.list(**kwargs)
            for item in images:
                if (not args.image_name) or (
                            args.image_name and args.image_name in item.name):
                    res_images.append({
                        "id": item.id,
                        "image_name": item.name,
                        "image_size": item.size,
                        "image_format": item.disk_format,
                        "created_time": item.created_at,
                    })
        except Exception as e:
            err_msg = e.message
            Log.logger.error('list glance image err: %s' % err_msg)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": res_images
                }
            }
            return res, 200


glance_image_api.add_resource(ImageListAPI, '/images')
