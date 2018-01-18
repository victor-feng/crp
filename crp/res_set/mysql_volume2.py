# -*- coding:utf8 -*-

import json
import requests
import logging
from crp.log import Log
from crp.openstack2 import OpenStack
from del_handler import CrpException
# 创建volume
# 挂载volume到虚机


def create_volume(vm,volume_size):
    """
    创建卷
    :param vm:
    :param volume_size:
    :return:
    """
    data_dict = {
        "volume": {
            "status": "creating",
            "availability_zone": "nova",
            "source_volid": None,
            "display_description": None,
            "snapshot_id": None,
            "user_id": None,
            "size": volume_size,
            "display_name": "%s-vol" % vm.get('vm_name', ''),
            "imageRef": None,
            "attach_status": "detached",
            "volume_type": None,
            "project_id": None,
            "metadata": {},
            "lvm_instance_id": vm.get('os_inst_id', '')
        }
    }
    cv_result = None
    err_msg = None
    try:
        cinder_endpoint, token = OpenStack.get_cinder_endpoint_and_token()
        url = cinder_endpoint + '/volumes'
        headers = {
            'User-Agent': 'python-cinderclient',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': token,
        }

        data_str = json.dumps(data_dict)
        Log.logger.debug(data_str)
        cv_result = requests.post(url=url, headers=headers, data=data_str)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.args
        Log.logger.error('error msg: %s' % err_msg)
    except BaseException as e:
        err_msg = e.args
        Log.logger.error('error msg: %s' % err_msg)
    finally:
        if err_msg:
            Log.logger.debug("CreateVolume Task ID " + str(vm.get('vm_name', '')) + '\r\n' + 'create_volume err_msg ' + str(err_msg))
            raise CrpException(err_msg)
        else:
            cv_result_dict = cv_result.json()
            volume = cv_result_dict.get('volume', {})
            res = {
                'id': volume.get('id', ''),
                'display_name': volume.get('display_name', ''),
            }
            Log.logger.debug("CreateVolume success %s" % res)
            return volume

def instance_attach_volume(os_inst_id, os_vol_id,device=None):
    """
    挂载卷
    :param os_inst_id:
    :param os_vol_id:
    :param device:
    :return:
    """
    try:
        nova_client = OpenStack.nova_client
        vol_attach_result = nova_client.volumes.create_server_volume(os_inst_id, os_vol_id, device)
        Log.logger.debug(
            "AttachVolume Task ID " +
            "\r\nvolume ID " + os_vol_id +
            "\r\ninstance ID " + os_inst_id +
            "\r\nresult: " + str(vol_attach_result.to_dict()))
        return "AttachVolumeSuccess"
    except BaseException as e:
        err_msg=str(e.args)
        Log.logger.error('attach volume os_inst_id is %s os_vol_id is  error msg: %s' % (os_inst_id,os_vol_id,err_msg))
        return "AttachVolumeError"

