# -*- coding: utf-8 -*-



from crp.log import Log
from crp.openstack2 import OpenStack
from crp.k8s_api import K8sDeploymentApi,K8sServiceApi,K8sIngressApi
from crp.taskmgr import *
from config import APP_ENV, configs
from crp.res_set import  delete_request_callback
NAMESPACE = configs[APP_ENV].NAMESPACE
RES_DELETE_CALL_BACK = configs[APP_ENV].RES_DELETE_CALL_BACK

QUERY_VOLUME = 0
DETACH_VOLUME = 1
DETACH_VOLUME_SUCCESSFUL = 2
QUERY_INGRESS = 3
DELETE_INGRESS = 4
QUERY_SERVICE = 5
DELETE_SERVICE = 6
QUERY_VM = 7
DELETE_VM = 8


UOP_URL = configs[APP_ENV].UOP_URL


class CrpException(Exception):
    pass


def query_ingress(task_id, result):
    resource_name = result.get('resource_name', '')
    resource_type = result.get('resource_type', '')
    ingress_name = resource_name + "-" + "ingress"
    try:
        if resource_type == "app":
            namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
            K8sIngress = K8sIngressApi()
            ingress_ret, ingress_code = K8sIngress.get_ingress(ingress_name,namespace)
            if ingress_code == 200:
                result['msg'] = 'Ingress is exist  begin delete Ingress'
                result['current_status'] = DELETE_INGRESS
                result['ingress_state'] = 1
            elif ingress_code == 404:
                result['current_status'] = QUERY_SERVICE
                ingress_state = result.get('ingress_state', 0)
                if ingress_state == 1:
                    result['msg'] = 'Ingress  delete success, begin query Service'
                else:
                    result['msg'] = 'Ingress is not exist, begin query Service'
        else:
            result['current_status'] = QUERY_VM
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Query ingress error {e}".format(e=str(e))
        result['msg'] = err_msg
        Log.logger.error(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
        raise CrpException(err_msg)

def delete_ingress(task_id, result):
    resource_name = result.get('resource_name', '')
    ingress_name = resource_name + "-" + "ingress"
    try:
        namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
        K8sIngress = K8sIngressApi()
        K8sIngress.delete_ingress(ingress_name, namespace)
        result['current_status'] = QUERY_INGRESS
        result['msg'] = 'delete ingress begin query ingress status'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Delete ingress error {e}".format(e=str(e))
        result['msg'] = err_msg
        Log.logger.error(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
        raise CrpException(err_msg)




def query_service(task_id, result):
    resource_name = result.get('resource_name', '')
    resource_type = result.get('resource_type', '')
    service_name = resource_name
    try:
        if resource_type == "app":
            namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
            K8sService = K8sServiceApi()
            service_ret, service_code = K8sService.get_service(service_name,namespace)
            if service_code == 200:
                result['msg'] = 'Service is exist  begin delete service'
                result['current_status'] = DELETE_SERVICE
                result['service_state'] = 1
            elif service_code == 404:
                result['current_status'] = QUERY_VM
                service_state = result.get('service_state', 0)
                if service_state == 1:
                    result['msg'] = 'Service  delete success, begin query Deployment'
                else:
                    result['msg'] = 'Service is not exist, begin query Deployment'
        else:
            result['current_status'] = QUERY_VM
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Query service error {e}".format(e=str(e))
        result['msg'] = err_msg
        Log.logger.error(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
        raise CrpException(err_msg)

def delete_service(task_id, result):
    resource_name = result.get('resource_name', '')
    service_name = resource_name
    try:
        namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
        K8sService = K8sServiceApi()
        K8sService.delete_service(service_name,namespace)
        result['current_status'] = QUERY_SERVICE
        result['msg'] = 'delete service begin query service status'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Delete service error {e}".format(e=str(e))
        result['msg'] = err_msg
        Log.logger.error(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
        raise CrpException(err_msg)


def query_instance(task_id, result, resource):
    """
    向openstack查询虚机状态
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_inst_id =resource.get('os_inst_id', '')
    resource_id =resource.get('resource_id', '')
    result['os_inst_id'] = os_inst_id
    if resource_id:
        result['resource_id'] = resource_id
    resource_type=result.get('resource_type','')
    resource_name = result.get('resource_name','')
    nova_client = OpenStack.nova_client
    try:
        if resource_type == "app":
            namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
            K8sDeployment = K8sDeploymentApi()
            deployment_ret,deployment_code=K8sDeployment.get_deployment(namespace,resource_name)
            if deployment_code == 200:
                result['deployment_state'] = 1
                result['current_status'] = DELETE_VM
                result['msg'] = 'deployment is exist  begin delete Deployment'
                Log.logger.error(
                    "Query Task ID " + str(task_id) +
                    " result " + result.__str__())
            elif deployment_code == 404:
                deployment_state = result.get("deployment_state",0)
                if deployment_state == 1:
                    result['msg'] = 'delete deployment success'
                    result['status'] = "success"
                    Log.logger.debug(
                        "Query Task ID " + str(task_id) +
                        " query Instance ID " + os_inst_id +
                        " result " + result.__str__())
                    delete_request_callback(task_id, result)
                    TaskManager.task_exit(task_id)
                elif deployment_state == 0:
                    result['msg'] = 'deployment is not exist'
                    result['code'] = 404
                    result['inst_state'] = 0
                    result['status'] = "success"
                    Log.logger.debug(
                        "Query Task ID " + str(task_id) +
                        " query Instance ID " + os_inst_id +
                        " result " + result.__str__())
                    delete_request_callback(task_id, result)
                    TaskManager.task_exit(task_id)
        else:
            inst = nova_client.servers.get(os_inst_id)
            task_state=getattr(inst,'OS-EXT-STS:task_state')
            result['inst_state'] = 1
            Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + os_inst_id +
            " Status is " + inst.status + " Instance task state is " + str(task_state))
            if  task_state != 'deleting' and inst.status != 'DELETED':
                result['current_status'] = DELETE_VM
                result['msg']='instance is exist  begin delete Instance'
    except Exception as e:
        err_msg = "Query deployment or instance error {e}".format(e=str(e))
        if resource_type == "app":
            raise CrpException(err_msg)
        else:
            inst_state=result.get('inst_state',0)
            if inst_state == 1:
                result['msg']='delete instance success'
                result['status'] = "success"
                Log.logger.debug(
                    "Query Task ID " + str(task_id) +
                    " query Instance ID " + os_inst_id +
                    " result " + result.__str__())
                delete_request_callback(task_id, result)
            elif inst_state == 0:
                result['msg'] = 'instance is not exist'
                result['code'] = 404
                result['status'] = "success"
                Log.logger.debug(
                    "Query Task ID " + str(task_id) +
                    " query Instance ID " + os_inst_id +
                    " result " + result.__str__())
                delete_request_callback(task_id, result)
            else:
                raise CrpException(err_msg)
        TaskManager.task_exit(task_id)

def delete_instance(task_id, result):
    """
    删除虚机
    :param task_id:
    :param result:
    :return:
    """
    os_inst_id = result.get('os_inst_id', '')
    nova_client = OpenStack.nova_client
    resource_type = result.get('resource_type','')
    resource_name = result.get('resource_name','')
    try:
        if resource_type == "app":
            namespace = result.get('namespace') if result.get('namespace') else NAMESPACE
            K8sDeployment = K8sDeploymentApi()
            K8sDeployment.delete_deployment(resource_name,namespace)
            result['msg'] = 'delete deployment begin query deployment status'
        else:
            nova_client.servers.delete(os_inst_id)
            result['msg'] = 'delete instance begin query Instance status'
        result['current_status'] = QUERY_VM
        result['code'] = 200
        Log.logger.debug(
              "Query Task ID " + str(task_id) +
              " query Instance ID " + str(os_inst_id) +
              " result " + result.__str__())
    except Exception as e:
        result['msg'] = 'delete instance or deployment failed'
        result['code'] = 400
        err_msg = " [CRP] delete_instance failed, Exception:{e}".format(e=str(e))
        Log.logger.error(
            "Query Task ID " + str(task_id) + " result " + result.__str__() + err_msg)
        raise CrpException(err_msg)



def detach_volume(task_id, result, resource):
    """
    卸载卷
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_inst_id = resource.get('os_inst_id')
    os_vol_id = resource.get('os_vol_id')
    Log.logger.debug(
        'Task ID %s,begin detach_volume, os_inst_id is %s, os_vol_id is %s.'% (task_id, os_inst_id, os_vol_id))

    try:
        if os_vol_id:
            nova_client = OpenStack.nova_client
            nova_client.volumes.delete_server_volume(os_inst_id, os_vol_id)
        elif not os_vol_id:
            #如果volume不存在直接删除虚机
            result['current_status'] = QUERY_VM
    except Exception as e:
        err_msg=str(e)
        Log.logger.error('Task ID %s,detach_volume error, os_inst_id is %s, os_vol_id is %s.error msg is %s'% (task_id, os_inst_id, os_vol_id,err_msg))
        raise CrpException(err_msg)
    else:
        result['current_status'] = QUERY_VOLUME


def query_volume_status(task_id, result, resource):
    """
    查询volume状态
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    try:
        os_vol_id = resource.get('os_vol_id')
        if os_vol_id:
            #如果volume存在直接查询volume状态
            cinder_client = OpenStack.cinder_client
            vol = cinder_client.volumes.get(os_vol_id)
            Log.logger.debug(
                    "Task ID %s, query_detach_status, Volume status: %s, info: %s" % (task_id, vol.status, vol))
            if vol.status == 'available':
                result['current_status'] = DETACH_VOLUME_SUCCESSFUL
                result['vol_state'] = 1
                Log.logger.info(
                    "Task ID %s, detach volume(%s) successful." % (task_id, os_vol_id))
            elif vol.status == 'in-use':
                result['current_status'] = DETACH_VOLUME
                result['vol_state'] = 1
                Log.logger.debug(
                    "Task ID %s, begin detach volume , vol_id is %s" %(task_id,os_vol_id))
            elif vol.status == 'error' or 'error' in vol.status:
                Log.logger.error(
                    "Task ID %s, volume status is error begin delete volume, vol_id is %s" %(task_id,os_vol_id))
                result['current_status'] = DETACH_VOLUME_SUCCESSFUL
                result['vol_state'] = 1
        elif not os_vol_id:
            #volume 不存在 直接删除虚机
            result['current_status']=QUERY_VM
    except Exception as e:
        vol_state = result.get("vol_state",0)
        if vol_state == 0:
            result['current_status'] = QUERY_VM
        else:
            err_msg=str(e)
            Log.logger.error('Task ID %s,query_volume_status error.error msg is %s' % (task_id, err_msg))
            raise CrpException(err_msg)



def delete_volume(task_id,result,resource):
    """
    删除卷
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_vol_id = resource.get('os_vol_id')
    try:
        if os_vol_id:
            cinder_client = OpenStack.cinder_client
            cinder_client.volumes.delete(os_vol_id)
        result['current_status'] = QUERY_VM
        Log.logger.debug(
            "Task ID %s, delete volume , vol_id is %s" % (task_id,os_vol_id))
    except Exception as e:
        Log.logger.error(
            "[CRP] _delete_volume failed, Exception:%s" % str(e))
        result['current_status'] = QUERY_VM
        raise CrpException(str(e))


def delete_instance_and_query2(task_id, result, resource):
    """
    查询和删除虚机和卷的类状态机
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    current_status = result.get('current_status', None)
    Log.logger.debug(
         "Task ID %s,\r\n resource %s .current_status %s" %
         (task_id, resource,current_status))
    try:
        if current_status == QUERY_VOLUME:
            query_volume_status(task_id, result, resource)
        elif current_status == DETACH_VOLUME:
            detach_volume(task_id, result, resource)
        elif current_status == DETACH_VOLUME_SUCCESSFUL:
            delete_volume(task_id, result,resource)
        elif current_status == QUERY_INGRESS:
            query_ingress(task_id,result)
        elif current_status == DELETE_INGRESS:
            delete_ingress(task_id,result)
        elif current_status == QUERY_SERVICE:
            query_service(task_id,result)
        elif current_status == DELETE_SERVICE:
            delete_service(task_id,result)
        elif current_status == QUERY_VM:
            query_instance(task_id, result, resource)
        elif current_status == DELETE_VM:
            delete_instance(task_id, result)
    except Exception as e:
        err_msg = " [CRP] delete_instance_and_query failed, Exception:%s" % str(e)
        Log.logger.error("Query Task ID " + str(task_id) + err_msg)
        result['msg'] = err_msg
        result['status'] = "fail"
        delete_request_callback(task_id, result)
        TaskManager.task_exit(task_id)




def delete_vip2(port_id):
    """
    删除虚拟IP
    :param port_id:
    :return:
    """
    try:
        neutron_client = OpenStack.neutron_client
        neutron_client.delete_port(port_id)
        Log.logger.debug('vip delete success port_id:%s' % port_id)
    except Exception as e:
        Log.logger.error(" delete vip  error, Exception:%s" % e)
        raise CrpException(str(e))







