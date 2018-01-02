# -*- coding: utf-8 -*-

import logging
import os
import uuid
import hashlib

from flask import current_app
import commands
import docker

from crp.log import Log
# from glanceclient import Client as GlanceClient
# from keystoneclient.auth.identity import v2 as v2_auth
# from keystoneclient import session
from config import APP_ENV, configs

DK_SOCK_URL = configs[APP_ENV].DK_SOCK_URL
DK_CLI_VERSION = configs[APP_ENV].DK_CLI_VERSION
DK_TAR_PATH = configs[APP_ENV].DK_TAR_PATH
GLANCE_RESERVATION_QUANTITY = configs[APP_ENV].GLANCE_RESERVATION_QUANTITY


DK_CREATED_FROM = 'created_from'
DK_UOP_CRP = 'uop-crp'



def _dk_py_cli():

    #DK_SOCK_URL = current_app.config['DK_SOCK_URL']
    #DK_CLI_VERSION = current_app.config['DK_CLI_VERSION']

    client = docker.DockerClient(
        base_url=DK_SOCK_URL,
        version=DK_CLI_VERSION,
        timeout=120)
    return client


def _dk_img_pull(dk_cli, _image_url, repository_hash, tag):
    try:
        #dk_cli.images.pull(_image_url)
        image = dk_cli.images.get(_image_url)
        image.tag(repository_hash, tag=tag)
    except docker.errors.ImageNotFound as img_err:
        Log.logger.error(img_err.args)
        return -1
    except docker.errors.APIError as api_err:
        if api_err.status_code==409:
            pass
        else:
            Log.logger.error(api_err)
            return api_err
    except Exception as e:
        Log.logger.error(e.args)
        return e.args
    else:
        return None


def _dk_img_save(dk_cli, _image_url):
    # image = dk_cli.images.get(_image_url)
    # resp = image.save()
    # tar_name = str(uuid.uuid1()) + '.tar'
    # tar_file = DK_TAR_PATH + tar_name
    # try:
    #     with open(tar_file, 'w') as f:
    #         for chunk in resp.stream():
    #             f.write(chunk)
    # except Exception as e:
    #     Log.logger.error(e.args)
    #     return e.args, None
    # else:
    #     return None, tar_file


    #DK_TAR_PATH = current_app.config['DK_TAR_PATH']
    tar_name = str(uuid.uuid1()) + '.tar'
    tar_file = DK_TAR_PATH + tar_name
    cmd = 'docker save --output '+tar_file+' '+_image_url
    try:
        code, msg = commands.getstatusoutput(cmd)
        if code == 0:
            return None, tar_file
        else:
            return msg, None
    except Exception as e:
        Log.logger.error(e.args)
        return e.args, None


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
    return OpenStack.glance_client()


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
        # "is_public": True,
        "container_format": 'docker',
        "disk_format": 'raw',
        "properties": {DK_CREATED_FROM: DK_UOP_CRP, "log_volume":"/home/logs/"},
        #"properties": {DK_CREATED_FROM: DK_UOP_CRP},

    }
    try:
        fields['data'] = open(tar_file, 'rb')
        Log.logger.debug(tar_file+" is opened now.")
        image = glance_cli.images.create(**fields)
        return None, image
    except Exception as e:
        err_msg="create image error ,msg is:%s" % str(e.args)
        Log.logger.error(err_msg)
        return err_msg, None
    finally:
        fields['data'].close()
        Log.logger.debug(tar_file+" is closed now.")
        #Log.logger.debug(fields['data'].closed)
        if fields['data'].closed:
            os.remove(tar_file)
            Log.logger.debug(tar_file+" was removed.")


def _cmp_img_info_time(img_item1, img_item2):
    """
    custom compare function like this:
    cmp(x, y) -> -1, 0, 1
    :param img_item1
    :param img_item2
    """
    import time

    time1 = img_item1.get('created_at')
    time2 = img_item2.get('created_at')
    t1 = time.strptime(time1, "%Y-%m-%dT%H:%M:%S")
    t2 = time.strptime(time2, "%Y-%m-%dT%H:%M:%S")
    if t1 < t2:
        return -1
    if t1 == t2:
        return 0
    if t1 > t2:
        return 1


def _glance_img_reservation(glance_cli, current_image_id, reservation_quantity):
    img_current = 0
    sort_img_reserv_info_list = []
    img_list = glance_cli.images.list()
    for img in img_list:
        if img.id == current_image_id:
            img_current += 1
            continue
        if img.properties.get(DK_CREATED_FROM) == DK_UOP_CRP:
            img_info = {
                "id": img.id,
                "created_at": img.created_at
            }
            sort_img_reserv_info_list.append(img_info)
    if sort_img_reserv_info_list.__len__() >= 1:
        Log.logger.debug("Original sort_img_reserv_info_list:")
        Log.logger.debug(sort_img_reserv_info_list)
        sort_img_reserv_info_list.sort(_cmp_img_info_time, key=None, reverse=True)
        Log.logger.debug("Sorted sort_img_reserv_info_list:")
        Log.logger.debug(sort_img_reserv_info_list)

    quantity = 0
    img_sum = sort_img_reserv_info_list.__len__() + img_current
    if img_sum >= reservation_quantity:
        quantity = img_sum - reservation_quantity

    if quantity > 0:
        img_info_to_be_delete = sort_img_reserv_info_list[reservation_quantity-1:]
        Log.logger.debug("image quantity is " + img_sum.__str__() +
                         " big than " + reservation_quantity.__str__() + ", img_info_to_be_delete:")
        Log.logger.debug(img_info_to_be_delete)
        for img in img_info_to_be_delete:
            img_id = img.get('id')
            #glance_cli.images.delete(img_id)
            Log.logger.debug(" glance Image ID " + img_id + " is deleting.")

#def image_update(image_id):
#    glance_cli = _glance_cli()
#    fields = {
#        "properties": {"log_volume":"/home/logs/"},
#    }
#    image = glance_cli.images.update(image.id, **fields)
#    return image.id

def delete_glance(glance_cli,image_id):
    """
    去glance 删除镜像方法，获取返回信息
    :param glance_cli:
    :param image_id:
    :return:
    """
    try:
        glance_cli.images.delete(image_id)
        return "success"
    except Exception as e:
        return "failed"

def delete_query_glance(glance_cli,image_id,properties):
    """
    删除镜像并查询镜像状态，删除五次后不能删除退出
    :param glance_cli:
    :param image_id:
    :param _image_url_hash:
    :return:
    """
    for i in range(5):
        Log.logger.debug("Begin delete image, %s times" % i)
        res=delete_glance(glance_cli, image_id)
        if res == "success":break
        else:
            Log.logger.debug("Begin query image, %s times" % i)
            images = glance_cli.images.list(filters=properties)
            image_list=[image for image in images]
            if len(image_list) == 0:break
    else:
        return "failed"
    return "success"




def image_transit(_image_url):
    try:
        img_tag = _image_url.split(':', 2)
        Log.logger.debug("Docker image url split list is:")
        Log.logger.debug(img_tag)
        glance_cli = _glance_cli()
        docker_cli = _dk_py_cli()
        try:
            cur_img = docker_cli.images.get(_image_url)
            docker_cli.images.remove(cur_img.id, force=True)
        except docker.errors.ImageNotFound, e:
            cur_img=None
        try:
            docker_cli.images.pull(_image_url)
            cur_img = docker_cli.images.get(_image_url)
        except Exception as e:
            err_msg="docker pull images from harbor to crp node,err_msg is %s" % str(e)
            return err_msg, None
        if cur_img:
            img_id = cur_img.attrs.get('ContainerConfig').get('Image')
            _image_url_hash = img_id.replace(':', '') + ':' + img_tag[1]
            repository_hash = img_id.replace(':', '')
        err_msg = ''
        Log.logger.info(_image_url_hash)
        Log.logger.info(repository_hash)
        try:
            cur_img.tag(repository_hash, tag=img_tag[1])
        except docker.errors.ImageNotFound as img_err:
            Log.logger.error(img_err.args)
        except docker.errors.APIError as api_err:
            if api_err.status_code==409:
                pass
        except Exception as e:
            Log.logger.error(e.args)
            err_msg = e.args
        properties = {"name": _image_url_hash}
        images = glance_cli.images.list(filters=properties)
        Log.logger.debug("FILTER IMAGE IS %s" ,images)
        for image in images:
            res=delete_query_glance(glance_cli,image.id,properties)
            if res == "success":
                Log.logger.debug("GLANCE IMAGE id is " +image.id + " IS DELETED " + " image_url " + _image_url)
            else:
                err_msg="delete glance images five time error"
                return err_msg,None
    except Exception as e:
        err_msg= "delete or pull images error ,error msg is : %s" % str(e.args)
        return err_msg, None
    dk_cli = _dk_py_cli()
    Log.logger.debug("Docker image pull from harbor url \'" + _image_url + "\' is started.")
    Log.logger.debug("Docker image pull from harbor url \'" + _image_url + "\' is done.")
    if err_msg:
        return err_msg, None
    else:
        Log.logger.debug("Docker image save as a tar package from harbor url \'" + _image_url +
                         " witch name with tag transit to sha224 " + _image_url_hash + "\' is started.")
        err_msg, tar_file = _dk_img_save(dk_cli, _image_url_hash)
        Log.logger.debug("Docker image save as a tar package from harbor url \'" + _image_url +
                         " witch name with tag transit to sha224 " + _image_url_hash + "\' is done.")
        if err_msg:
            return err_msg, None
        else:
            Log.logger.debug("Docker image tar package create glance image from harbor url \'" + _image_url +
                             " witch name with tag transit to sha224 " + _image_url_hash + "\' is started.")
            err_msg, image = _glance_img_create(glance_cli, _image_url_hash, tar_file)
            Log.logger.debug("Docker image tar package create glance image from harbor url \'" + _image_url +
                             " witch name with tag transit to sha224 " + _image_url_hash + "\' is done.")
            if err_msg:
                return err_msg, None
            else:
                #GLANCE_RESERVATION_QUANTITY = current_app.config['GLANCE_RESERVATION_QUANTITY']
                _glance_img_reservation(glance_cli, image.id, GLANCE_RESERVATION_QUANTITY)
                Log.logger.debug("SUCCESS IMAGE ID IS" + image.id + "URL is"+ _image_url)
                return None, image.id


if __name__ == '__main__':
    image_url = 'arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170517101336'
    err_msg, image_id = image_transit(image_url)
    print err_msg, image_id
    # image_url = 'wzbtest:xxx'
    # tar_file = '/home/dk/03224b48-4069-11e7-b211-000c29bca56a.tar'
    # glance_cli = _glance_cli()
    # print _glance_img_create(glance_cli, image_url, tar_file)
