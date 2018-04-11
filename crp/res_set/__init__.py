# -*- coding: utf-8 -*-
from flask import Blueprint
import json
import requests
from crp.log import Log
from config import APP_ENV, configs


resource_set_blueprint = Blueprint('resource_set_blueprint', __name__)




UOP_URL = configs[APP_ENV].UOP_URL
RES_DELETE_CALL_BACK = configs[APP_ENV].RES_DELETE_CALL_BACK

def delete_request_callback(task_id, result):
    """
    把删除信息和状态回调给uop
    :param task_id:
    :param result:
    :return:
    """
    data = {
            'resource_id': result.get('resource_id', ''),
            'os_inst_id': result.get('os_inst_id', ''),
            'msg': result.get('msg', ''),
            'code': result.get('code', ''),
            'unique_flag': result.get('unique_flag',''),
            'del_os_ins_ip_list': result.get('del_os_ins_ip_list', []),
            "set_flag":result.get('set_flag','res'),
            "status" : result.get("status",'fail')
        }
    headers = {'Content-Type': 'application/json'}
    syswin_project=result.get('syswin_project', '')
    DELETE_CALL_BACK=RES_DELETE_CALL_BACK[syswin_project]
    try:
        data_str=json.dumps(data)
        res=requests.post(DELETE_CALL_BACK,data=data_str,headers=headers)
        res=json.dumps(res.json())
        Log.logger.debug(res)
    except BaseException as e:
        err_msg = str(e)
        Log.logger.error(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'delete_request_callback err_msg ' + str(err_msg))

from . import handler, views, forms, errors
