# -*- coding: utf-8 -*-
import logging

from flask_restful import reqparse, Api, Resource

# TODO: import * is bad!!!
from crp.taskmgr import *
from crp.glance_image import glance_image_blueprint
from crp.glance_image.errors import user_errors
from crp.openstack2 import OpenStack as OpenStack2
from crp.openstack import OpenStack as OpenStack1
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
        res_images = []
        try:
            kwargs = {'filters': filters}

            glance_cli_1 = OpenStack1.glance_client()
            images_1 = glance_cli_1.images.list(**kwargs)
            Log.logger.info("The cloud1 image_1 is {}".format(images_1))
            for item_1 in images_1:
                if (not args.image_name) or (args.image_name and args.image_name in item_1.name):
                    res_images.append({
                        "id": item_1.id,
                        "image_name": item_1.name,
                        "image_size": item_1.size,
                        "image_format": item_1.disk_format,
                        "created_time": item_1.created_at,
                        "cloud": "1"
                    })
            Log.logger.info("The cloud1 image list is {}".format(res_images))
            glance_cli = OpenStack2.glance_client()
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
                        "cloud": "2"
                    })
            Log.logger.info("The cloud2 image list is {}".format(res_images))
        except Exception as e:
            err_msg ='CRP list glance image err: %s' % str(e)
            Log.logger.error(err_msg)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": err_msg
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "Get image list success ",
                    "res": res_images
                }
            }
            return res, 200


glance_image_api.add_resource(ImageListAPI, '/images')
