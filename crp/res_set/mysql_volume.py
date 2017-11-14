# -*- coding:utf8 -*-

import json
import requests
import logging
from crp.openstack import OpenStack
# 创建volume
# 挂载volume到虚机


def create_volume(vm,volume_size):
    data_dict = {
        "volume": {
            'size': volume_size,
            "display_name": "%s-vol" % vm.get('vm_name', ''),
            "lvm_instance_id": vm.get('os_inst_id', ''),
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
        cv_result = requests.post(url=url, headers=headers, data=data_str)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
        logging.debug('error msg: %s' % err_msg)
    except BaseException as e:
        err_msg = e.msg
        logging.debug('error msg: %s' % err_msg)
    finally:
        if err_msg:
            logging.debug("CreateVolume Task ID " + str(vm.get('vm_name', '')) + '\r\n' + 'create_volume err_msg ' + str(err_msg))
        else:
            cv_result_dict = cv_result.json()
            volume = cv_result_dict.get('volume', {})
            res = {
                'id': volume.get('id', ''),
                'display_name': volume.get('display_name', ''),
            }
            logging.debug("CreateVolume success %s" % res)
            return volume

def instance_attach_volume(os_inst_id, os_vol_id,device=None):
    nova_client = OpenStack.nova_client
    vol_attach_result = nova_client.volumes.create_server_volume(
        os_inst_id, os_vol_id, device)
    logging.debug(
        "AttachVolume Task ID " +
        "\r\nvolume ID " + os_vol_id +
        "\r\ninstance ID " + os_inst_id +
        "\r\nresult: " + str(vol_attach_result.to_dict())
    )