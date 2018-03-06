# -*- coding: utf-8 -*-

import json
import commands
import time
import uuid
import subprocess
import threading

from flask_restful import reqparse, Api, Resource
from flask import request
from flask import current_app
import requests

from crp.app_deployment import app_deploy_blueprint
from crp.app_deployment.errors import user_errors
from crp.utils.docker_tools import image_transit
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.dns.dns_api import NamedManagerApi
from crp.log import Log
from crp.disconf.disconf_api import *
from crp.utils.aio import exec_cmd_ten_times,async
from handler import _dep_detail_callback,_dep_callback,closed_nginx_conf,\
    open_nginx_conf,start_write_log,get_war_from_ftp,make_database_config

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from config import APP_ENV, configs
from crp.k8s_api import K8S,K8sDeploymentApi


app_deploy_api = Api(app_deploy_blueprint, errors=user_errors)
#TODO: move to global conf
UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER
HEALTH_CHECK_PORT = configs[APP_ENV].HEALTH_CHECK_PORT
HEALTH_CHECK_PATH = configs[APP_ENV].HEALTH_CHECK_PATH
NAMESPACE = configs[APP_ENV].NAMESPACE
FILEBEAT_NAME = configs[APP_ENV].FILEBEAT_NAME
SCRIPTPATH = configs[APP_ENV].SCRIPTPATH


class AppDeploy(Resource):

    def __init__(self):
        self.all_ips=[]

    def do_app_push(self, app):
        # TODO: do app push
        def do_push_nginx_config(kwargs):
            """
            need the nip domain ip
            nip:这是nginx那台机器的ip
            need write the update file into vm
            :param kwargs:
            :return:
            """
            selfdir = os.path.dirname(os.path.abspath(__file__))
            nip = kwargs.get('nip')
            Log.logger.debug('----->start push:{}dir:{}'.format(kwargs, selfdir))
            yum_install_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip, dir=selfdir)
            scp_update_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/update.py dest=/tmp/'".format(
                    nip=nip, dir=selfdir)
            scp_template_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/template dest=/tmp/'".format(
                    nip=nip, dir=selfdir)
            chmod_update_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/update.py'".format(
                nip=nip, dir=selfdir)
            chmod_template_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/template'".format(
                nip=nip, dir=selfdir)
            exec_shell_cmd='ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a ''"/tmp/update.py {domain} {ip} {port}"'.format(
                    nip=kwargs.get('nip'),
                    dir=selfdir,
                    domain=kwargs.get('domain'),
                    ip=kwargs.get('ip'),
                    port=kwargs.get('port'))
            exec_cmd_ten_times(nip,yum_install_cmd,1)
            exec_cmd_ten_times(nip, scp_update_cmd, 1)
            exec_cmd_ten_times(nip, scp_template_cmd, 1)
            Log.logger.debug('------>上传配置文件完成')
            exec_cmd_ten_times(nip, chmod_update_cmd, 1)
            exec_cmd_ten_times(nip, chmod_template_cmd, 1)
            exec_cmd_ten_times(nip, exec_shell_cmd, 1)
            Log.logger.debug('------>end push')

        real_ip = ''
        ips = app.get('ips')
        Log.logger.debug("####current compute instance is:{}".format(app))
        domain_ip = app.get('domain_ip', "")
        domain = app.get('domain', '')
        for ip in ips:
            ip_str = ip + ' '
            real_ip += ip_str
        ports = str(app.get('port'))
        Log.logger.debug(
            'the receive (domain, nginx, ip, port) is (%s, %s, %s, %s)' %
            (domain, domain_ip, real_ip, ports))
        try:
            do_push_nginx_config({'nip': domain_ip,
                                'domain': domain,
                                'ip': real_ip.strip(),
                                'port': ports.strip()})
        except Exception as e:
            Log.logger.error("error:{}".format(e))

    @async
    def run_delete_cmd(self, **kwargs):
        """
        删除nginx配置
        :param kwargs:
        :return:
        """
        selfdir = os.path.dirname(os.path.abspath(__file__))
        domain_list = kwargs.get("domain_list")
        disconf_list = kwargs.get("disconf_list")
        Log.logger.debug("--------->start delete nginx profiles")
        for dl in domain_list:
            nip = dl.get("domain_ip")
            domain = dl.get('domain')
            if not nip or not domain:
                Log.logger.info("nginx ip or domain is null, do nothing")
                continue
            yum_install_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip, dir=selfdir)
            scp_delete_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/delete.py dest=/tmp/'".format(
                    nip=nip, dir=selfdir)
            chmod_delete_cmd="ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/delete.py'".format(
                nip=nip, dir=selfdir)
            exec_shell_cmd='ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a ''"/tmp/delete.py {domain}"'.format(
                    nip=nip,
                    dir=selfdir,
                    domain=domain)
            exec_cmd_ten_times(nip,yum_install_cmd,1)
            exec_cmd_ten_times(nip,scp_delete_cmd,1)
            Log.logger.debug('------>上传删除脚本完成')
            exec_cmd_ten_times(nip, chmod_delete_cmd, 1)
            exec_cmd_ten_times(nip, exec_shell_cmd, 1)
        Log.logger.debug("--------->stop delete nginx profiles: success")

    def delete(self):
        code = 200
        msg = "ok"
        try:
            request_data = json.loads(request.data)
            disconf_list = request_data.get('disconf_list')
            domain_list = request_data.get('domain_list')
            self.run_delete_cmd(domain_list=domain_list, disconf_list=disconf_list)
        except Exception as msg:
            Log.logger.error("delete nginx ip error {}".format(msg))
            code = 500
            msg = msg
        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code

    def put(self):
        code=200
        msg="ok"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('appinfo', type=list, location='json')
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('set_flag', type=str)
            args = parser.parse_args()
            appinfo = args.appinfo
            deploy_id=args.deploy_id
            set_flag = args.set_flag
            deploy_type=set_flag
            msg_dict={
                "increase":"扩容完成",
                "reduce":"缩容完成",
                "deploy_increase_nginx":"nginx增加扩容docker完成",
                "deploy_reduce_nginx":"nginx缩减缩容docker完成",
            }
            for app in appinfo:
                self.do_app_push(app)
            if appinfo:
                _dep_detail_callback(deploy_id, "deploy_%s_nginx" % set_flag, set_flag, msg_dict["deploy_%s_nginx" % set_flag])
                _dep_detail_callback(deploy_id, deploy_type, set_flag, msg_dict[set_flag])
            elif not appinfo:
                _dep_detail_callback(deploy_id, deploy_type, set_flag, msg_dict[set_flag])
        except Exception as e:
            Log.logger.error("AppDeploy put exception:%s " %str(e))
            code = 500
            msg = "internal server error: %s"  %str(e)
        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code



    def post(self):
        code = 200
        msg = "ok"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('mysql', type=dict)
            parser.add_argument('docker', type=list, location='json')
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('mongodb', type=dict)
            parser.add_argument('dns', type=list, location='json')
            parser.add_argument('appinfo', type=list, location='json')
            parser.add_argument('disconf_server_info', type=list, location='json')
            parser.add_argument('deploy_type', type=str)
            parser.add_argument('environment', type=str)
            parser.add_argument('cloud', type=str)
            parser.add_argument('resource_name', type=str)
            parser.add_argument('deploy_name', type=str)
            parser.add_argument('project_name', type=str)
            args = parser.parse_args()
            Log.logger.debug("AppDeploy receive post request. args is " + str(args))
            deploy_id = args.deploy_id
            deploy_type = args.deploy_type
            Log.logger.debug("deploy_id is " + str(deploy_id))
            docker = args.docker
            dns = args.dns
            disconf_server_info = args.disconf_server_info
            appinfo = args.appinfo
            environment=args.environment
            cloud = args.cloud
            resource_name = args.resource_name
            deploy_name=args.deploy_name
            project_name = args.project_name
            Log.logger.debug("Thread exec start")
            t = threading.Thread(target=self.deploy_anything, args=(docker, dns, deploy_id, appinfo, disconf_server_info,deploy_type,environment,cloud,resource_name,deploy_name,project_name))
            t.start()
            Log.logger.debug("Thread exec done")

        except Exception as e:
            msg = "internal server error: " + str(e.args)
            Log.logger.error("AppDeploy exception: %s" % msg)
            code = 500

        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code

    def deploy_anything(self,docker, dns, deploy_id, appinfo, disconf_server_info,deploy_type,environment,cloud,resource_name,deploy_name,project_name):
        try:
            lock = threading.RLock()
            lock.acquire()
            code = 200
            msg = "ok"
            unique_flag = str(uuid.uuid1())
            #添加disconf配置
            for disconf_info in disconf_server_info:
                Log.logger.debug('The disconf_info: %s' % disconf_info)
                disconf_api_connect = DisconfServerApi(disconf_info)
                if disconf_info.get('disconf_env','').isdigit():
                    env_id = disconf_info.get('disconf_env')
                else:
                    env_id = disconf_api_connect.disconf_env_id(env_name=disconf_info.get('disconf_env'))

                if len(disconf_info.get('disconf_admin_content','').strip()) == 0:
                    disconf_admin_name = exchange_disconf_name(disconf_info.get('disconf_content'))
                else:
                    disconf_admin_name = exchange_disconf_name(disconf_info.get('disconf_admin_content'))

                result,message = disconf_api_connect.disconf_add_app_config_api_file(
                                                app_name=disconf_info.get('disconf_app_name'),
                                                myfilerar=disconf_admin_name,
                                                version=disconf_info.get('disconf_version'),
                                                env_id=env_id
                                                )
                Log.logger.debug("disconf result:{result},{message}".format(result=result,message=message))
            if disconf_server_info:
                _dep_detail_callback(deploy_id,"deploy_disconf","res")
            #部署
            if cloud == "2":
                deployment_name=resource_name
                for i in docker:
                    image_url = i.get('url', '')
                    cluster_name = i.get("ins_name", "")
                    host_env = i.get("host_env")
                    if host_env == "docker":
                        update_image_deployment = K8sDeploymentApi.update_deployment_image_object(deployment_name,
                                                                                                  FILEBEAT_NAME)
                        update_deployment_err_msg, update_deployment_err_code = K8sDeploymentApi.update_deployment_image(
                            update_image_deployment, deployment_name, image_url, NAMESPACE)
                        end_flag = True
                        if update_deployment_err_msg is None:
                            #不报错开始检查应用和pod的状态
                            self._check_deployment_status(deployment_name, deploy_id, cluster_name,
                                                   end_flag, deploy_type,
                                                   unique_flag, cloud,deploy_name)
                        else:
                            _dep_callback(deploy_id, '127.0.0.1', host_env, update_deployment_err_msg, "None", False, cluster_name, end_flag, deploy_type,
                                          unique_flag,cloud,deploy_name)
                    elif host_env == "kvm":
                        deploy_kvm_flag, msg=self.deploy_kvm(project_name,i,environment)
                        if deploy_kvm_flag:
                            _dep_callback(deploy_id, '127.0.0.1', host_env, msg, "None", True, cluster_name,
                                          end_flag,
                                          deploy_type,
                                          unique_flag, cloud, deploy_name)
                        else:
                            _dep_callback(deploy_id, '127.0.0.1',host_env, msg, "None", False,
                                          cluster_name, end_flag, deploy_type,
                                          unique_flag, cloud, deploy_name)



            else:
                cloud = '1'
                if not appinfo:
                    Log.logger.info("No nginx ip information, no need to push nginx something")
                for app in appinfo:
                    self.do_app_push(app)
                if appinfo:
                    _dep_detail_callback(deploy_id, "deploy_nginx", "res")

                # 添加dns解析
                for item in dns:
                    domain_name = item.get('domain', '')
                    domain_ip = item.get('domain_ip', '')
                    Log.logger.debug('domain_name:%s,domain_ip:%s' % (domain_name, domain_ip))
                    if len(domain_name.strip()) != 0 and len(domain_ip.strip()) != 0:
                        dns_api = NamedManagerApi(environment)
                        msg = dns_api.named_dns_domain_add(domain_name=domain_name, domain_ip=domain_ip)
                        Log.logger.debug('The dns add result: %s' % msg)
                    else:
                        Log.logger.debug(
                            'domain_name:{domain_name},domain_ip:{domain_ip} is null'.format(domain_name=domain_name,
                                                                                             domain_ip=domain_ip))
                if dns:
                    _dep_detail_callback(deploy_id, "deploy_dns", "res")
                Log.logger.debug("All Docker is " + str(docker))
                #pull docker images
                id2name = {}
                err_dockers=[]
                for i in docker:
                    image_url = i.get('url','')
                    cluster_name = i.get("ins_name", "")
                    ip=i.get('ip',[])
                    ip=','.join(ip)
                    host_env = i.get("host_env")
                    if host_env == "docker":
                        if image_url in id2name.keys():
                            image_uuid = id2name.get(image_url)
                            i["image_uuid"] = image_uuid
                        else:
                            err_msg, image_uuid = image_transit(image_url)
                            id2name[image_url] = image_uuid
                            i["image_uuid"] = image_uuid
                            if err_msg is None:
                                Log.logger.debug(
                                    "Transit harbor docker image success. The result glance image UUID is " + str(image_uuid))
                            else:
                                Log.logger.error(
                                     "Transit harbor docker image failed. image_url is " + str(image_url) + " error msg:" + str(err_msg))
                                err_msg="image get error image url is: %s, err_msg is: %s " % (str(image_url),str(err_msg))
                                #将错误信息返回给uop
                                err_dockers.append(i)
                                end_flag=False
                                if len(docker) == (docker.index(i)+1):
                                    end_flag=True
                                _dep_callback(deploy_id, ip, "docker", err_msg, "None", False, cluster_name, end_flag, 'deploy',unique_flag)
                #如果有集群拉取镜像失败，将这个集群从docker中删除
                for err_docker in err_dockers:
                    docker.remove(err_docker)
                    Log.logger.debug("The Latest Docker is " + str(docker))
                #获取所有集群的ip
                all_ips = []
                for info in docker:
                    ips = info.get('ip')
                    all_ips.extend(ips)
                self.all_ips = all_ips
                #部署
                for info in docker:
                    host_env = info.get("host_env")
                    if host_env == "docker":
                        self._image_transit(deploy_id, info,appinfo,deploy_type,unique_flag,cloud,deploy_name)
                    elif host_env == "kvm":
                        deploy_kvm_flag, msg = self.deploy_kvm(project_name, i, environment)
                        if deploy_kvm_flag:
                            _dep_callback(deploy_id, '127.0.0.1', host_env, msg, "None", True, cluster_name,
                                          end_flag,
                                          deploy_type,
                                          unique_flag, cloud, deploy_name)
                        else:
                            _dep_callback(deploy_id, '127.0.0.1', host_env, msg, "None", False,
                                          cluster_name, end_flag, deploy_type,
                                          unique_flag, cloud, deploy_name)
            lock.release()
        except Exception as e:
            code = 500
            msg = "internal server error: " + str(e.args)
            Log.logger.error(msg)
        return code, msg

    def _deploy_docker(self, info,deploy_id, image_uuid,appinfo,deploy_type,unique_flag,cloud,deploy_name):
        deploy_flag=True
        end_flag=False
        first_error_flag=False
        cluster_name=info.get("ins_name","")
        ip_index_dict={}
        ip_list=info.get('ip')
        health_check=int(info.get("health_check",0))
        #获取每个ip在列表中的索引
        for ip in ip_list:
            ip_index_dict[ip]=ip_list.index(ip)
        while 1:
            ips = info.get('ip')
            length_ip = len(ips)
            if length_ip > 0:
                Log.logger.debug('ip and url: ' + str(ips) + str(info.get('url')))
                ip = ips[0]
                os_flag,vm_state,err_msg=self._deploy_query_instance_set_status(ip, image_uuid,appinfo,health_check)
                #执行写日志的操作
                start_write_log(ip)
                if os_flag:
                    self.all_ips.remove(ip)
                    if len(self.all_ips) == 0:
                        end_flag=True
                    if health_check == 1:
                        msg=u"应用健康检查正常"
                    else:
                        msg=u"docker网络检查正常"
                    _dep_callback(deploy_id, ip, "docker", msg, vm_state, True, cluster_name,end_flag,deploy_type,unique_flag,cloud,deploy_name)
                    Log.logger.debug(
                        "Cluster name " + cluster_name + " IP is " + ip + " Status is " + vm_state + " self.all_ips:" + self.all_ips.__str__())
                else:
                    #如果索引为0，表示第一个ip部署失败，部署停止
                    ip_index = int(ip_index_dict[ip])
                    Log.logger.debug(
                        "Cluster name " + cluster_name + " IP is " + ip + " Status is " + vm_state + " ip_index:" + str(ip_index))
                    if ip_index == 0:
                        first_error_flag = True
                        for d_ip in ips:
                            self.all_ips.remove(d_ip)
                    else:
                        self.all_ips.remove(ip)
                    if len(self.all_ips) == 0:
                        end_flag=True
                        deploy_flag = False
                    _dep_callback(deploy_id, ip, "docker", err_msg, vm_state, False,cluster_name,end_flag,deploy_type,unique_flag,cloud,deploy_name)
                    Log.logger.debug(
                        "Cluster name " + cluster_name + " IP is " + ip + " Status is " + vm_state + " self.all_ips:" + self.all_ips.__str__())
                    if first_error_flag:break
                ips.pop(0)
            else:
                break
        return deploy_flag


    def _deploy_query_instance_set_status(self,ip=None,image_uuid=None,appinfo=[],health_check=0):
        try:
            os_flag=True
            err_msg=""
            nova_client = OpenStack.nova_client
            Log.logger.debug( "Begin rebuild docker,IP is:" + ip)
            #开始注释nginx配置
            closed_nginx_conf(appinfo,ip)
            #开始rebuild
            server = OpenStack.find_vm_from_ipv4(ip=ip)
            newserver = OpenStack.nova_client.servers.rebuild(server=server, image=image_uuid)
            os_inst_id=newserver.id
            for i in range(20):
                vm = nova_client.servers.get(os_inst_id)
                vm_state = vm.status.lower()
                task_state = getattr(vm, 'OS-EXT-STS:task_state')
                #check_res=True
                check_res,check_msg=self.app_health_or_network_check(ip, HEALTH_CHECK_PORT, HEALTH_CHECK_PATH,health_check)
                Log.logger.debug(
                    " query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state + " check res:" + str(
                        check_res) + " Query Times is:" + str(i))
                if vm_state == "error" and  "rebuild" not in str(task_state) :
                    os_flag=False
                    err_msg="vm status is error " + check_msg
                    Log.logger.debug( " query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state +  " check res:"+ str(check_res) +" Error msg is:" +err_msg)
                    break
                elif vm_state == "shutoff" and "rebuild" not in str(task_state):
                    # 如果vm状态是关闭时重启3次
                    Log.logger.debug(" query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state +" Begin start 3 times")
                    for i in range(3):
                        #启动vm
                        vm = nova_client.servers.get(os_inst_id)
                        task_state=getattr(vm,'OS-EXT-STS:task_state')
                        vm_state = vm.status.lower()
                        if task_state != "powering-on" and  vm_state == "shutoff":
                            nova_client.servers.start(server=server)
                            time.sleep(10)
                        vm = nova_client.servers.get(os_inst_id)
                        vm_state = vm.status.lower()
                        if vm_state != "active":
                            Log.logger.debug( " query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state + " start %s times" %i)
                            time.sleep(5)
                            continue
                        elif vm_state == "active":break
                    else:
                        os_flag = False
                        err_msg="vm status is shutoff " + check_msg
                        Log.logger.debug(" query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state + " check res:"+ str(check_res) + " Error msg is:" +err_msg )
                        break
                elif vm_state == "active" and check_res == True and "rebuild" not in str(task_state):
                    os_flag = True
                    Log.logger.debug(" query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state + " check res:"+ str(check_res))
                    open_nginx_conf(appinfo,ip)
                    break
                time.sleep(6)
            else:
                os_flag = False
                err_msg = check_msg
                Log.logger.debug(
                    " query Instance ID " + os_inst_id.__str__() + " Status is " + vm_state + " check res:" + str(check_res) + " Error msg is:" + err_msg)
            return os_flag,vm_state,err_msg
        except Exception as e:
            os_flag=False
            err_msg=str(e.args)
            Log.logger.error( "CRP _deploy_query_instance_set_status Error msg is:" + err_msg)
            return os_flag,None,err_msg


    def _image_transit(self,deploy_id, info,appinfo,deploy_type,unique_flag,cloud,deploy_name):
        result_list = []
        timeout = 10000
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, self._image_transit_task, deploy_id, info, appinfo,deploy_type,unique_flag,cloud,deploy_name)

    def _image_transit_task(self,task_id=None, result_list=None, deploy_id=None, info=None, appinfo=[],deploy_type=None,unique_flag=None,cloud=None,deploy_name=None):
        image_uuid = info.get("image_uuid")
        if self._check_image_status(image_uuid):
            deploy_flag = self._deploy_docker(info, deploy_id, image_uuid, appinfo, deploy_type,unique_flag,cloud,deploy_name)
            if not deploy_flag:
                TaskManager.task_exit(task_id)
        else:
            # 检查镜像五次状态不为active将错误返回给uop
            image_url = info.get('url', '')
            cluster_name = info.get("ins_name", "")
            ips = info.get('ip', [])
            ip = ','.join(ips)
            #将这个集群的ip 从总集群中删除
            for d_ip in ips:
                self.all_ips.remove(d_ip)
            end_flag=False
            if len(self.all_ips) == 0:
                end_flag=True
            msg = "check image five times,image status not active,image url is:%s,Image id is %s" % (image_url,image_uuid)
            _dep_callback(deploy_id, ip, "docker", msg, "None", False, cluster_name, end_flag, 'deploy',unique_flag,cloud,deploy_name)
        TaskManager.task_exit(task_id)

    def _check_image_status(self,image_uuid):
        nova_client = OpenStack.nova_client
        check_times = 5
        check_interval = 5
        for i in range(check_times):
            img = nova_client.glance.find_image(image_uuid)
            Log.logger.debug(
                "check image status " + str(i) + " times, status: " + img.status.lower() + " image_uuid:" + image_uuid)
            if (img.status.lower() != "active"):
                time.sleep(check_interval)
            else:
                return True
        return False



    def app_health_or_network_check(self,ip,port,url_path,health_check):
        """
        健康检查或判断网络是否正常
        :param ip:
        :param port:
        :param url_path:
        :param health_check:
        :return:
        """
        check_url="http://%s:%s/%s" % (ip,port,url_path)
        headers = {'Content-Type': 'application/json'}
        network_check_cmd="ping -c 4 %s -w 4" %ip
        res_dict = {True: "success", False: "failed"}
        res=False
        if health_check == 1:
            msg_str="app health check %s"
            try:
                result = requests.get(check_url, headers=headers,timeout=3)
                result = json.loads(result.content)
                app_status=result["status"]
                if app_status == "UP":res=True
                return res,msg_str % res_dict[res]
            except Exception as e:
                res = False
                return res,msg_str % res_dict[res]
        else:
            msg_str = "app network check %s"
            try:
                res=os.popen(network_check_cmd).read().strip().split('\n')[-2].split()
                if int(res[3]) > 0:res=True
                return res,msg_str % res_dict[res]
            except Exception as e:
                res=False
                return res,msg_str % res_dict[res]

    def _check_deployment_status(self, deployment_name=None, deploy_id=None, cluster_name=None, end_flag=None, deploy_type=None,
                                unique_flag=None, cloud=None,deploy_name=None):
        try:
            for i in range(10):
                time.sleep(30)
                deployment_status = K8sDeploymentApi.get_deployment_status(NAMESPACE, deployment_name)
                if deployment_status == "available":
                    _dep_callback(deploy_id, '127.0.0.1', "docker", "None", "None", True, cluster_name, end_flag,
                                  deploy_type,
                                  unique_flag, cloud,deploy_name)
                    break
                else:
                    s_flag, err_msg = K8sDeploymentApi.get_deployment_pod_status(NAMESPACE, deployment_name)
                    if s_flag is not True:
                        _dep_callback(deploy_id, '127.0.0.1', "docker", err_msg, "None", False,
                                      cluster_name, end_flag, deploy_type,
                                      unique_flag, cloud,deploy_name)
                        break
            else:
                err_msg = "deploy deployment failed"
                _dep_callback(deploy_id, '127.0.0.1', "docker", err_msg, "None", False,
                              cluster_name, end_flag, deploy_type,
                              unique_flag, cloud, deploy_name)

        except Exception as e:
            err_msg = "check deployment status error %s" % str(e)
            Log.logger.error(err_msg)

    def deploy_kvm(self,project_name,info,env):
        try:
            war_url = info.get("url")
            database_config = info.get("database_config",'{}')
            ip = info.get("ip",[])
            war_err_msg=get_war_from_ftp(project_name,war_url)
            if war_err_msg:
                return  war_err_msg
            config_err_msg = make_database_config(database_config,project_name,ip,env)
            if config_err_msg:
                return  config_err_msg
            #执行playbook命令
            data_config_path= os.path.join(UPLOAD_FOLDER,"wardeploy")
            wardeploy_yml_path = os.path.join(SCRIPTPATH,"roles/wardeploy.yml")
            key_path = os.path.join(SCRIPTPATH,"id_rsa_java_new")
            deploy_war_cmd = """ansible-playbook -i {data_config_path} {wardeploy_yml_path} 
            --private-key={key_path} -e hosts={project_name} update""".format(data_config_path=data_config_path,
                                                                              wardeploy_yml_path=wardeploy_yml_path,
                                                                              key_path = key_path,
                                                                              project_name=project_name
                                                                              )
            p = subprocess.Popen(
                deploy_war_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            res = p.stdout.read()
            if "unreachable=0" in res and "failed=0" in res:
                msg = "Deploy war to kvm success"
                deploy_kvm_flag = True
            else:
                msg = "Deploy war to kvm failed,failed msg is {res}".format(res=res)
                deploy_kvm_flag = False
        except Exception as e:
            msg = "Deploy war to kvm error,error msg is {e}".format(e=str(e))
            deploy_kvm_flag = False
        return deploy_kvm_flag,msg








class Upload(Resource):
    def post(self):
        try:
            UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
            type = request.form.get('type','')

            if type == 'disconf':
                file = request.files['file']
                disconf_file_name = file.filename
                disconf_file_path = request.form.get('disconf_file_path')
                disconf_abspath = os.path.dirname(disconf_file_path)
                if not os.path.exists(disconf_abspath):
                    os.makedirs(disconf_abspath)
                file.save(disconf_file_path)
                result = "{disconf_file_name} upload success".format(disconf_file_name=disconf_file_name)
            else:
                file_dic = {}
                for _type, file in request.files.items():
                    if not os.path.exists(os.path.join(UPLOAD_FOLDER, _type)):
                        os.makedirs(os.path.join(UPLOAD_FOLDER, _type))
                    file_path = os.path.join(UPLOAD_FOLDER, _type, file.filename)
                    file.save(file_path)
                    file_dic[_type] = (file_path, file.filename)
                    result = file_dic
        except Exception as e:
            return {
                'code': 500,
                'msg': str(e.args)
            }
        return {
            'code': 200,
            'msg': '上传成功！',
            'file_info': result,
        }






app_deploy_api.add_resource(AppDeploy, '/deploys')
app_deploy_api.add_resource(Upload, '/upload')
