# -*- coding: utf-8 -*-
import json
import requests
from crp.log import Log
from config import configs, APP_ENV
RES_STATUS_CALLBACK = configs[APP_ENV].RES_STATUS_CALLBACK
ADD_LOG = configs[APP_ENV].ADD_LOG
WAR_DICT = ADD_LOG.get("WAR_DICT")
BUILD_IMAGE = ADD_LOG.get("BUILD_IMAGE")
PUSH_IMAGE = ADD_LOG.get("PUSH_IMAGE")

def res_instance_push_callback(task_id,req_dict,quantity,instance_info,db_push_info, add_log, set_flag):
    """
    crp 将预留资源时的状态和信息回调给uop
    :param task_id:
    :param req_dict:
    :param quantity:
    :param instance_info:
    :param db_push_info:
    :param set_flag:
    :return:
    """
    try:
        resource_id = req_dict["resource_id"]
        if instance_info:
            ip=instance_info.get('ip')
            instance_type=instance_info.get('instance_type')
            instance_name=instance_info.get('instance_name')
            os_inst_id=instance_info.get('os_inst_id')
            physical_server=instance_info.get('physical_server')
            instance={
                "resource_id":resource_id,
                "ip": ip,
                "instance_name": instance_name,
                "instance_type": instance_type,
                "os_inst_id": os_inst_id,
                "physical_server": physical_server,
                "quantity":quantity,
                "status":"active",
                "from":'resource',
                }
        else:
            instance=None
        if db_push_info:
            cluster_name=db_push_info.get('cluster_name')
            cluster_type=db_push_info.get('cluster_type')
            db_push={
                "resource_id":resource_id,
                "cluster_name":cluster_name,
                "cluster_type":"push_%s" %cluster_type,
                "status":"ok",
                "from":'resource',
                }
        else:
            db_push=None

        if add_log in WAR_DICT:
            var_dict = {
                "war_to_image_status": add_log,
                "resource_id": resource_id
            }
        else:
            var_dict = {}

        if add_log in BUILD_IMAGE:
            build_image = {
                "resource_id": resource_id,
                "build_image_status": add_log,
            }
        else:
            build_image = {}

        if add_log in PUSH_IMAGE:
            push_image = {
                "resource_id": resource_id,
                "push_image_status": add_log
            }
        else:
            push_image = {}

        data={
            "instance":instance,
            "db_push":db_push,
            "set_flag":set_flag,
            "var_dict": var_dict,
            "build_image": build_image,
            "push_image": push_image
        }
        data_str=json.dumps(data)
        headers = {
        'Content-Type': 'application/json'
        }
        res = requests.post(RES_STATUS_CALLBACK,data=data_str,headers=headers)
        Log.logger.debug(res)
    except Exception as e:
        err_msg=e.args
        Log.logger.error("res_instance_push_callback error %s" % err_msg)
