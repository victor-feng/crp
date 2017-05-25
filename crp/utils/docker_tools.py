# -*- coding: utf-8 -*-

import docker
import uuid

# from crp.log import Log
from glanceclient.v1 import client as glance_client
from keystoneclient.v2_0 import client as keystone_client

DK_URL = 'unix://var/run/docker.sock'
CLI_VERSION = '1.22'


def _dk_py_cli():
    client = docker.DockerClient(
        base_url=DK_URL,
        version=CLI_VERSION)
    return client


def _dk_img_pull(dk_cli, _image_url):
    try:
        dk_cli.images.pull(_image_url)
    except docker.errors.ImageNotFound as img_err:
        err_msg = img_err.message
        # Log.logger.error(msg)
        return err_msg
    except Exception as e:
        err_msg = e.message
        # Log.logger.error(msg)
        return err_msg
    else:
        return None


TAR_PATH = '/home/dk/'


def _dk_img_save(dk_cli, _image_url):
    image = dk_cli.images.get(_image_url)
    resp = image.save()
    tar_name = str(uuid.uuid1()) + '.tar'
    tar_file = TAR_PATH + tar_name
    try:
        with open(tar_file, 'w') as f:
            for chunk in resp.stream():
                f.write(chunk)
    except Exception as e:
        # Log.logger.error(e.message)
        return e.message, None
    else:
        return None, tar_file


def _glance_cli():
    user_name = 'admin'
    user_password = 'sySwin@sy'
    keystone_token = 'sySwin@sy'
    tenant_name = 'admin'
    auth_url = 'http://172.28.11.254:35357/v2.0/'

    # just for glance now.
    def get_endpoint():
        _keystone_cli = keystone_client.Client(
            token=keystone_token,
            endpoint=auth_url,
            tenant_name=tenant_name)
        service_list = _keystone_cli.services.list()
        glance_id = None
        for i in range(len(service_list)):
            if service_list[i].type == "image":
                glance_id = service_list[i].id
        if glance_id == None:
            return
        endpoint_list = _keystone_cli.endpoints.list()
        for j in range(len(endpoint_list)):
            if endpoint_list[j].service_id == glance_id:
                return endpoint_list[j].publicurl

    glance_endpoint = get_endpoint()
    _glance_cli = glance_client.Client(endpoint=glance_endpoint, username=user_name,
                                       password=user_password, tenant_name=tenant_name,
                                       auth_url=auth_url)
    return _glance_cli


def _glance_img_create(glance_cli, image_name, tar_file):
    '''
    glance image-create --is-public=True --container-format=docker --disk-format=raw --name xxx --file xxx.tar
    :param glance_cli:
    :param image_name:
    :param tar_file:
    :return:
    '''
    fields = {
        "is-public": True,
        "container-format": 'docker',
        "disk-format": 'raw',
        "name": image_name,
        "file": tar_file
    }
    if 'location' not in fields and 'copy_from' not in fields:
        open(fields['file'], 'rb')
    # image = glance_cli.images.create(**fields)
    # return image
    images = glance_cli.images.list()
    return images
    # image = glance_cli.images.get('3027f868-8f87-45cd-b85b-8b0da3ecaa84')
    # return image



def image_transit(_image_url):
    # dk_cli = _dk_py_cli()
    # err_msg = _dk_img_pull(dk_cli, _image_url)
    # if err_msg:
    #     return err_msg, None
    # else:
    #     err_msg, tar_file = _dk_img_save(dk_cli, _image_url)
    #     if err_msg:
    #         return err_msg, None
    #     else:
    #         glance_cli = _glance_cli()
    #         image = _glance_img_create(glance_cli, _image_url, tar_file)
    #         return image
    return None, '3027f868-8f87-45cd-b85b-8b0da3ecaa84'


if __name__ == '__main__':
    image_url = 'arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170517101336'
    # err_msg, tar_file = image_transit(image_url)
    # print err_msg, tar_file
    tar_file = '/home/dk/03224b48-4069-11e7-b211-000c29bca56a.tar'
    glance_cli = _glance_cli()
    print dir(_glance_img_create(glance_cli, image_url, tar_file))
