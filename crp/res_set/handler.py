# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource

from crp.taskmgr import *
from crp.res_set import resource_set_blueprint
from crp.res_set.errors import resource_set_errors
from crp.openstack import OpenStack

resource_set_api = Api(resource_set_blueprint, errors=resource_set_errors)


TIMEOUT = 500
SLEEP_TIME = 3


images_dict = {
    'mysql': {
        'uuid': '9d9c2029-cd1e-41d3-ab2e-9b1ab6eca7df',
        'name': 'mysqlsas-50G-20170428',
    },
    'redis': {
        'uuid': '3da55e5b-814c-4935-abf0-1469ae606286',
        'name': 'redis-50G-20170428',
    },
    'mongo': {
        'uuid': '95863650-6816-4588-846a-c0423b5baae0',
        'name': 'mongosas-50G-20170428',
    },
}


# cirros-0.3.3
IMAGE_MINI = 'c63884fb-399b-400c-a5fd-810cefb50dc0'
# mini
FLAVOR_MINI = 'aadb6488-a64f-4868-82dd-7b832cd047ac'
# scm2-dev--1C2G80G
FLAVOR_1C2G = 'scm2-dev--1C2G80G'
AVAILABILITY_ZONE = 'AZ_GENERAL'
DEV_NETWORK_ID = 'c12740e6-33c8-49e9-b17d-6255bb10cd0c'


# 向OpenStack申请资源
def _create_instance(name, image, flavor, availability_zone, network_id):
    nova_client = OpenStack.nova_client
    # ints = nova_client.servers.list()
    # Log.logger.debug(ints)
    # def create(self, name, image, flavor, meta=None, files=None,
    #            reservation_id=None, min_count=None,
    #            max_count=None, security_groups=None, userdata=None,
    #            key_name=None, availability_zone=None,
    #            block_device_mapping=None, block_device_mapping_v2=None,
    #            nics=None, scheduler_hints=None,
    #            config_drive=None, disk_config=None, **kwargs):

    nics_list = []
    nic_info = {'net-id': network_id}
    nics_list.append(nic_info)
    int = nova_client.servers.create(name, image, flavor,
                                     availability_zone=availability_zone,
                                     nics=nics_list)
    Log.logger.debug(int)
    Log.logger.debug(int.id)

    return int.id


# 依据资源类型创建资源
def create_instance_by_type(ins_type, name):
    image = images_dict.get(ins_type)
    image_uuid = image.get('uuid')
    Log.logger.debug("Select Image UUID: "+image_uuid+" by Instance Type "+ins_type)
    return _create_instance(name, image_uuid, FLAVOR_1C2G, AVAILABILITY_ZONE, DEV_NETWORK_ID)


# 申请资源定时任务
def _create_resource_set(task_id=None, resource_list=None, compute_list=None):
    ins_id_list = []
    for resource in resource_list:
        ins_name = resource.get('res_name')
        ins_id = resource.get('res_id')
        # ins_id = str(uuid.uuid1())
        ins_type = resource.get('res_type')
        cpu = resource.get('cpu')
        mem = resource.get('mem')
        disk = resource.get('disk')
        quantity = resource.get('quantity')
        version = resource.get('version')

        osint_id = create_instance_by_type(ins_type, ins_name)
        ins_id_list.append(osint_id)

    for compute in compute_list:
        ins_name = compute.get('ins_name')
        ins_id = compute.get('ins_id')
        # ins_id = str(uuid.uuid1())
        cpu = compute.get('cpu')
        mem = compute.get('mem')
        url = compute.get('url')

        # osint_id = _create_instance()
        # ins_id_list.append(osint_id)

    return ins_id_list


# 向OpenStack查询已申请资源的定时任务
def _query_resource_set_status(task_id=None, result_list=None, osins_id_list=None):
    rollback_flag = False
    osint_id_wait_query = list(set(osins_id_list) - set(result_list))
    Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
                     ", Content is " + result_list[:].__str__())
    nova_client = OpenStack.nova_client
    for int_id in osint_id_wait_query:
        int = nova_client.servers.get(int_id)
        Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id+" Status is "+int.status)
        if int.status == 'ACTIVE':
            result_list.append(int_id)
        if int.status == 'ERROR':
            # TODO: 删除全部
            rollback_flag = True

    if result_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        Log.logger.debug("Task ID "+task_id.__str__()+" all instance create success." +
                         " instance id set is "+result_list[:].__str__())
        TaskManager.task_exit(task_id)

    if rollback_flag:
        fail_list = list(set(osins_id_list) - set(result_list))
        Log.logger.debug("Task ID "+task_id.__str__()+" have one or more instance create failed." +
                         " Successful instance id set is "+result_list[:].__str__() +
                         " Failed instance id set is "+fail_list[:].__str__())
        # 删除全部，完成rollback
        for int_id in osins_id_list:
            nova_client.servers.delete(int_id)

        # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程

        # 停止定时任务并退出
        TaskManager.task_exit(task_id)


class ResourceSet(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('resource_name', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('department', type=str)
        # parser.add_argument('department_id', type=str)
        parser.add_argument('res_id', type=str)
        parser.add_argument('user_name', type=str)
        parser.add_argument('user_id', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('application_status', type=str)
        # parser.add_argument('approval_status', type=str)
        parser.add_argument('resource_list', type=list, location='json')
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()

        resource_name = args.resource_name
        project = args.project
        department = args.department
        department_id = '1'
        res_id = args.res_id
        # res_id = str(uuid.uuid1())
        user_name = args.user_name
        user_id = args.user_id
        domain = args.domain
        env = args.env
        application_status = args.application_status
        # approval_status = args.approval_status
        resource_list = args.resource_list
        compute_list = args.compute_list

        # try:
        #     if ResourceModel.objects.filter(resource_name=resource_name).count():
        #         res = {
        #             'code': 200,
        #             'result': {
        #                 'res': 'success',
        #                 'msg': 'Resource already exist.',
        #                 'res_name': resource_name
        #             }
        #         }
        #         return res, 404
        # except Exception as e:
        #     print e
        #     return
        # resource_application = ResourceModel(resource_name=resource_name, project=project, department=department,
        #                                      department_id=department_id, res_id=res_id,
        #                                      user_name=user_name, user_id=user_id, domain=domain, env=env,
        #                                      application_status=application_status)
        for resource in resource_list:
            ins_name = resource.get('res_name')
            ins_id = resource.get('res_id')
            # ins_id = str(uuid.uuid1())
            ins_type = resource.get('res_type')
            cpu = resource.get('cpu')
            mem = resource.get('mem')
            disk = resource.get('disk')
            quantity = resource.get('quantity')
            version = resource.get('version')
            # db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
            #                quantity=quantity, version=version)
            # resource_application.resource_list.append(db_ins)

        for compute in compute_list:
            ins_name = compute.get('ins_name')
            ins_id = compute.get('ins_id')
            # ins_id = str(uuid.uuid1())
            cpu = compute.get('cpu')
            mem = compute.get('mem')
            url = compute.get('url')
            # compute_ins = ComputeIns(ins_name=ins_name, ins_id=ins_id, cpu=cpu, mem=mem, url=url)
            # resource_application.compute_list.append(compute_ins)

        Log.logger.debug(resource_list)
        Log.logger.debug(compute_list)

        osins_id_list = _create_resource_set(res_id, resource_list, compute_list)
        # TODO(TaskManager.task_start()): 定时任务示例代码
        result_list = []
        Log.logger.debug("Test API handler result_list object id is " + id(result_list).__str__() +
                         ", Content is " + result_list[:].__str__())
        TaskManager.task_start(SLEEP_TIME, TIMEOUT, result_list, _query_resource_set_status, osins_id_list)
        # try:
        #     resource_application.save()
        # except Exception as e:
        #     code = 500
        #     res = {"code": code,
        #            "result": {
        #                'res': 'fail',
        #                'msg': 'Create resource application fail.'
        #            }
        #     }
        #     return res, code

        # return http code 202 (Accepted)
        res_id = 'testid'
        res = {
            'code': 202,
            'result': {
                'res': 'success',
                'msg': 'Create Resource Set Accepted.',
                'res_id': res_id,
                'res_name': resource_name
            }
        }

        return res, 202


resource_set_api.add_resource(ResourceSet, '/sets')
