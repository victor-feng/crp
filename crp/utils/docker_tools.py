# -*- coding: utf-8 -*-

import docker
import uuid

from crp.log import Log
# from glanceclient import Client as GlanceClient
# from keystoneclient.auth.identity import v2 as v2_auth
# from keystoneclient import session
from config import APP_ENV, configs

DK_SOCK_URL = configs[APP_ENV].DK_SOCK_URL
DK_CLI_VERSION = configs[APP_ENV].DK_CLI_VERSION
DK_TAR_PATH = configs[APP_ENV].DK_TAR_PATH


def _dk_py_cli():
    client = docker.DockerClient(
        base_url=DK_SOCK_URL,
        version=DK_CLI_VERSION)
    return client


def _dk_img_pull(dk_cli, _image_url):
    try:
        dk_cli.images.pull(_image_url)
    except docker.errors.ImageNotFound as img_err:
        Log.logger.error(img_err.message)
        return img_err.message
    except Exception as e:
        Log.logger.error(e.message)
        return e.message
    else:
        return None


def _dk_img_save(dk_cli, _image_url):
    image = dk_cli.images.get(_image_url)
    resp = image.save()
    tar_name = str(uuid.uuid1()) + '.tar'
    tar_file = DK_TAR_PATH + tar_name
    try:
        with open(tar_file, 'w') as f:
            for chunk in resp.stream():
                f.write(chunk)
    except Exception as e:
        Log.logger.error(e.message)
        return e.message, None
    else:
        return None, tar_file


# def _get_endpoint_and_token(auth_url, username, password, tenant_name):
#     kwargs = {
#         'auth_url': auth_url,
#         'username': username,
#         'password': password,
#         'tenant_name': tenant_name,
#     }
#     ks_session = session.Session.construct(kwargs)
#     auth = v2_auth.Password(
#         auth_url=auth_url, username=username,
#         password=password, tenant_name=tenant_name)
#     ks_session.auth = auth
#     token = ks_session.get_token()
#     endpoint = ks_session.get_endpoint(
#         service_type='image', endpoint_type='public')
#     return endpoint, token


def _glance_cli():
    # user_name = 'admin'
    # user_password = 'sySwin@sy'
    # tenant_name = 'admin'
    # auth_url = 'http://172.28.11.254:35357/v2.0/'
    #
    # endpoint, token = _get_endpoint_and_token(auth_url, user_name, user_password, tenant_name)
    # _glance_cli = GlanceClient('1', endpoint=endpoint, token=token)
    from crp.openstack import OpenStack
    return OpenStack.glance_client


def _glance_img_create(glance_cli, image_name, tar_file):
    '''
    glance image-create --is-public=True --container-format=docker --disk-format=raw --name xxx --file xxx.tar
    :param glance_cli:
    :param image_name:
    :param tar_file:
    :return:
    '''
    fields = {
        "name": image_name,
        "is_public": True,
        "container_format": 'docker',
        "disk_format": 'raw',
    }
    try:
        fields['data'] = open(tar_file, 'rb')
        image = glance_cli.images.create(**fields)
        return None, image
    except Exception as e:
        Log.logger.error(e.message)
        return e.message, None


def image_transit(_image_url):
    dk_cli = _dk_py_cli()
    err_msg = _dk_img_pull(dk_cli, _image_url)
    if err_msg:
        return err_msg, None
    else:
        err_msg, tar_file = _dk_img_save(dk_cli, _image_url)
        if err_msg:
            return err_msg, None
        else:
            glance_cli = _glance_cli()
            err_msg, image = _glance_img_create(glance_cli, _image_url, tar_file)
            if err_msg:
                return err_msg, None
            else:
                return None, image.id
    # return None, '3027f868-8f87-45cd-b85b-8b0da3ecaa84'


if __name__ == '__main__':
    image_url = 'arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170517101336'
    err_msg, image_id = image_transit(image_url)
    print err_msg, image_id
    # image_url = 'wzbtest:xxx'
    # tar_file = '/home/dk/03224b48-4069-11e7-b211-000c29bca56a.tar'
    # glance_cli = _glance_cli()
    # print _glance_img_create(glance_cli, image_url, tar_file)
