# -*- coding: utf-8 -*-


from kubernetes import client
from kubernetes import  config
from config import APP_ENV, configs
from crp.utils.aio import get_k8s_err_code
from crp.log import Log
import datetime
import json



K8S_CONF_PATH = configs[APP_ENV].K8S_CONF_PATH



def k8s_client_setting(k8s_conf_path):
    config.load_kube_config(config_file=k8s_conf_path)
    K8S.core_v1=client.CoreV1Api()
    K8S.extensions_v1 = client.ExtensionsV1beta1Api()


class K8S(object):
    core_v1=None
    extensions_v1=None

    @property
    def core_v1(self):
        if K8S.core_v1 is not None:
            return K8S.core_v1

    @core_v1.setter
    def core_v1(self,value):
        if value is not None:
            K8S.core_v1 = value
    @property
    def extensions_v1(self):
        if K8S.extensions_v1 is not None:
            return K8S.extensions_v1

    @extensions_v1.setter
    def extensions_v1(self,value):
        if value is not None:
            K8S.extensions_v1 = value


class K8sDeploymentApi(object):

    def __init__(self):

        config.load_kube_config(config_file=K8S_CONF_PATH)
        self.corev1 = client.CoreV1Api()
        self.extensionsv1 = client.ExtensionsV1beta1Api()
        self.deletev1 = client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=5
                    )
        self.force_deletev1 = client.V1DeleteOptions(
                     propagation_policy='Background',
                     grace_period_seconds=5)

    def create_deployment_object(self,deployment_name,
                                 filebeat_name,
                                 filebeat_image_url,
                                 filebeat_requests,
                                 filebeat_limits,
                                 app_image_url,
                                 app_container_port,
                                 app_requests,
                                 app_limits,
                                 networkName,
                                 tenantName,
                                 host_mapping,
                                 replicas,
                                 ready_probe_path
                                 ):
        """

        :param deployment_name:"filebeat-test"
        :param filebeat_name:"filebeat"
        :param filebeat_image_url:"dkreg-wj.syswin.com/base/filebeat:5.4.0"
        :param filebeat_requests:{"cpu": 0.5, "memory": "20Mi"}
        :param filebeat_limits:{"cpu": 1, "memory": "100Mi"}
        :param app_image_url:"reg1.syswin.com/sit/tomcat-cssapi:v0.1"
        :param app_container_port:8081
        :param app_requests:{"cpu": 1, "memory": "1Gi"}
        :param app_limits:{"cpu": 2, "memory": "2Gi"}
        :param labels_name:"filebeat-test"
        :param networkName:"contiv-vlan651"
        :param tenantName:"tenant-vlan651"
        :param hostnames:["www.baidu.com"]
        :param ip:"127.0.0.1"
        :param replicas:3
        :return:
        """
        deployment_name=deployment_name.lower()
        host_aliases=[]
        err_msg = None
        deployment = None
        try:
            host_mapping = json.loads(host_mapping)
            if host_mapping:
                for host_map in host_mapping:
                    ip = host_map.get("ip", '127.0.0.1')
                    hostnames = host_map.get("hostnames", ['"uop-k8s.syswin.com"'])
                    host_aliase=client.V1HostAlias(hostnames=hostnames, ip=ip)
                    host_aliases.append(host_aliase)
            filebeat_container = client.V1Container(
                name=filebeat_name,
                image=filebeat_image_url,
                resources=client.V1ResourceRequirements(
                    requests=filebeat_requests,
                    limits=filebeat_limits
                ),
                volume_mounts=[
                    client.V1VolumeMount(name="app-logs", mount_path="/log"),
                    client.V1VolumeMount(name="%s-config" % filebeat_name , mount_path="/etc/filebeat/"),
                ],
                image_pull_policy="IfNotPresent"
            )
            if app_container_port:
                if ready_probe_path:
                    app_container = client.V1Container(
                        name='app',
                        image=app_image_url,
                        ports=[
                            client.V1ContainerPort(container_port=app_container_port)
                        ],
                        resources=client.V1ResourceRequirements(
                            requests=app_requests,
                            limits=app_limits,
                        ),
                        volume_mounts=[
                            client.V1VolumeMount(name="app-logs", mount_path="/home/logs"),
                        ],
                        image_pull_policy="Always",
                        readiness_probe=client.V1Probe(
                            failure_threshold=3,
                            http_get=client.V1HTTPGetAction(
                                path=ready_probe_path,
                                port=app_container_port,
                            ),
                            initial_delay_seconds=10,
                            period_seconds=10,
                            success_threshold=1,
                            timeout_seconds=1,
                        )
                    )
                else:
                    app_container = client.V1Container(
                        name='app',
                        image=app_image_url,
                        ports=[
                            client.V1ContainerPort(container_port=app_container_port)
                        ],
                        resources=client.V1ResourceRequirements(
                            requests=app_requests,
                            limits=app_limits,
                        ),
                        volume_mounts=[
                            client.V1VolumeMount(name="app-logs", mount_path="/home/logs"),
                        ],
                        image_pull_policy="Always",
                    )

            else:
                app_container = client.V1Container(
                    name='app',
                    image=app_image_url,
                    resources=client.V1ResourceRequirements(
                        requests=app_requests,
                        limits=app_limits,
                    ),
                    volume_mounts=[
                        client.V1VolumeMount(name="app-logs", mount_path="/home/logs"),
                    ],
                    image_pull_policy="Always",
                )

            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": deployment_name,
                        "io.contiv.tenant":tenantName ,
                        "io.contiv.network": networkName,
                    }
                ),
                spec=client.V1PodSpec(
                    host_aliases=host_aliases,
                    containers=[
                        filebeat_container,
                        app_container,
                    ],
                    volumes=[
                        client.V1Volume(name="app-logs", empty_dir={}),
                        client.V1Volume(
                            name="%s-config" % filebeat_name,
                            config_map=client.V1ConfigMapVolumeSource(name="%s-config" % filebeat_name)
                        ),
                    ]
                ),
            )
            selector = client.V1LabelSelector(
                match_labels={
                    "app": deployment_name
                }
            )
            spec = client.ExtensionsV1beta1DeploymentSpec(
                revision_history_limit=10,
                selector=selector,
                replicas=replicas,
                template=template,
            )
            # Instantiate the deployment object
            deployment = client.ExtensionsV1beta1Deployment(
                api_version="extensions/v1beta1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=deployment_name),
                spec=spec,
            )
        except Exception as e:
            err_msg = "Create deployment object error {e}".format(e=str(e))
        return deployment,err_msg

    def create_deployment(self,deployment,namespace):
        """

        :param api_instance: ExtensionsV1beta1Api()
        :param deployment:
        :param namespace:
        :return:
        """
        # Create deployement
        err_msg = None
        code=200
        try:
            api_instance = self.extensionsv1
            api_response = api_instance.create_namespaced_deployment(
                body=deployment,
                namespace=namespace)
        except Exception as e:
            err_msg = "create deployment error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def update_deployment_image_object(self,deployment_name,filebeat_name,app_requests,app_limits,host_mapping,networkName,tenantName):
        """
        deployment image 更新镜像时创建模板,配额
        :param deployment_name:
        :return:
        """
        host_aliases = []
        err_msg = None
        update_image_deployment = None
        try:
            deployment_name = deployment_name.lower()
            host_mapping = json.loads(host_mapping)
            if host_mapping:
                for host_map in host_mapping:
                    ip = host_map.get("ip", '127.0.0.1')
                    hostnames = host_map.get("hostnames", ['"uop-k8s.syswin.com"'])
                    host_aliase = client.V1HostAlias(hostnames=hostnames, ip=ip)
                    host_aliases.append(host_aliase)
            filebeat_container = client.V1Container(
                name=filebeat_name,
            )
            app_container = client.V1Container(
                name="app",
                image="",
                resources=client.V1ResourceRequirements(
                    requests=app_requests,
                    limits=app_limits,
                )
            )
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": deployment_name,
                        "io.contiv.tenant":tenantName,
                        "io.contiv.network": networkName,
                            }
                ),
                spec=client.V1PodSpec(
                    host_aliases=host_aliases,
                    containers=[
                        filebeat_container,
                        app_container,
                    ],
                ),
            )
            selector = client.V1LabelSelector(

                match_labels={
                    "app": deployment_name
                }
            )

            spec = client.ExtensionsV1beta1DeploymentSpec(
                selector=selector,
                template=template,
            )

            # Instantiate the deployment object
            update_image_deployment = client.ExtensionsV1beta1Deployment(
                api_version="extensions/v1beta1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=deployment_name),
                spec=spec,
            )

        except Exception as e:
            err_msg = "Update deployment object error {e}".format(e=str(e))
        return update_image_deployment,err_msg

    def update_deployment_image(self, update_image_deployment, deployment_name, namespace):
        """
        更新deployment
        :param api_instance:
        :param deployment:
        :param deployment_name:
        :param new_image_url:
        :return:
        """
        # Update container image
        err_msg = None
        code=200
        try:
            api_instance = self.extensionsv1
            deployment_name = deployment_name.lower()
            #update_image_deployment.spec.template.spec.containers[1].image = new_image_url
            # Update pod label
            update_image_deployment.spec.template.metadata.labels["restartLatestTime"] = \
                datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            # Update the deployment
            api_response = api_instance.replace_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=update_image_deployment)
        except Exception as e:
            err_msg = "update deployment image error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def delete_deployment(self, deployment_name, namespace):
        """
        删除deployment
        :param api_instance:ExtensionsV1beta1Api()
        :param deployment_name:
        :return:
        """
        # Delete deployment
        err_msg = None
        code=200
        try:
            deployment_name = deployment_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=self.deletev1)
        except Exception as e:
            err_msg = "delete deployment error %s" %str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def delete_force_deployment(self, deployment_name, namespace):
        """
        强制删除deployment
        :param api_instance:ExtensionsV1beta1Api()
        :param deployment_name:
        :return:
        """
        # Delete deployment
        err_msg = None
        code=200
        try:
            deployment_name = deployment_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=self.force_deletev1)
        except Exception as e:
            err_msg = "delete deployment error %s" %str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def update_deployment_replicas_object(self,deployment_name):
        """
        deployment 扩缩容时创建的模板
        :param deployment_name:
        :return:
        """
        deployment_name = deployment_name.lower()
        spec = client.ExtensionsV1beta1DeploymentSpec(
            replicas=3,
            template=client.V1PodTemplateSpec(),
        )

        # Instantiate the deployment object
        update_replicas_deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec,
        )

        return update_replicas_deployment

    def update_deployment_scale(self, update_replicas_deployment, deployment_name, namespace, new_replicas):
        """
        deployment扩缩容
        :param api_instance:ExtensionsV1beta1Api()
        :param deployment:
        :param deployment_name:
        :param namespace:
        :return:
        """
        err_msg = None
        code = 200
        try:
            deployment_name = deployment_name.lower()
            api_instance = self.extensionsv1
            update_replicas_deployment.spec.replicas = new_replicas
            api_response = api_instance.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body=update_replicas_deployment)
        except Exception as e:
            err_msg = "update deployment scale error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code

    def get_deployment_status(self, namespace, deployment_name):
        """
        获取deployment状态
        :param api_instance:ExtensionsV1beta1Api()
        :param namespace:
        :param deployment_name:
        :return:
        """
        try:
            deployment_name = deployment_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.read_namespaced_deployment_status(deployment_name, namespace)
            available_replicas=api_response.status.available_replicas
            replicas=api_response.status.replicas
            if replicas is not None and replicas == available_replicas:
                return 'available'
            else:
                return 'unavailable'
        except Exception as e:
            return 'unavailable'

    def get_deployment_pod_info(self, namespace, deployment_name):
        """
        获取deployment pod的ip和宿主机主机名，pod名字
        :param api_instance:CoreV1Api
        :param namespace:
        :param deployment_name:
        :return:
        """
        deployment_info_list = []
        try:
            resource_name = deployment_name
            deployment_name = deployment_name.lower()
            api_instance = self.corev1
            api_response = api_instance.list_namespaced_pod(namespace)
            result = api_response.items
            for res in result:
                deployment_dict = {}
                pod_name = res.metadata.name
                pod_ip = res.status.pod_ip
                if deployment_name in pod_name and pod_ip:
                    status = res.status.phase
                    if status == "Running":
                        vm_state = "active"
                    else:
                        vm_state = "shutoff"
                    node_name = res.spec.node_name
                    host_ip = res.status.host_ip
                    deployment_dict['deployment_name'] = deployment_name
                    deployment_dict['pod_ip'] = pod_ip
                    deployment_dict['node_name'] = node_name
                    deployment_dict['pod_name'] = pod_name
                    deployment_dict['host_ip'] = host_ip
                    deployment_dict['resource_name'] = resource_name
                    deployment_dict['status'] = vm_state
                    deployment_info_list.append(deployment_dict)
        except Exception as e:
            err_msg = "Get deployment pod info error {e}".format(e=str(e))
            Log.logger.ereor(err_msg)
        return deployment_info_list

    def get_deployment(self, namespace, deployment_name):
        """
        获取deployment
        :param api_instance:ExtensionsV1beta1Api()
        :param namespace:
        :param deployment_name:
        :return:
        """
        code = 200
        msg = None
        try:
            deployment_name = deployment_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.read_namespaced_deployment(deployment_name, namespace)
            msg=api_response
        except Exception as e:
            msg = "Get deployment error {e}".format(e=str(e))
            code = get_k8s_err_code(e)
        return msg,code


    # 重启deployment下的全部pod
    def restart_deployment_pod_object(self,deployment_name):
        deployment_name = deployment_name.lower()
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={}
            ),
        )
        spec = client.ExtensionsV1beta1DeploymentSpec(
            template=template,
        )

        # Instantiate the deployment object
        restart_deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec,
        )

        return restart_deployment


    def restart_deployment_pod(self, restart_deployment,deployment_name,namespace):
        # restart pod label
        deployment_name = deployment_name.lower()
        api_instance = self.extensionsv1
        restart_deployment.spec.template.metadata.labels["restartLatestTime"] = \
            datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # reatart  the deployment
        err_msg = None
        code = 200
        try:
            api_response = api_instance.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=restart_deployment)
        except Exception as e:
            err_msg = "restart deployment error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code

    def get_namespace_deployment_info(self,namespace):
        deployment_info=[]
        api_instance = self.extensionsv1
        deploy_ret = api_instance.list_namespaced_deployment(namespace, watch=False)
        for i in deploy_ret.items:
            deployment_dict={}
            deployment_dict["namespace"] = i.metadata.namespace
            deployment_dict["deployment_name"] = i.metadata.name
            deployment_dict["replicas"] = i.status.replicas
            deployment_dict["available_replicas"] = i.status.available_replicas
            deployment_info.append(deployment_dict)
        return deployment_info

    def get_deployment_info(self, namespace,deployment_name):
        deployment_name = deployment_name.lower()
        deployment_info = []
        deployment_dict = {}
        api_instance = self.extensionsv1
        deploy_ret = api_instance.read_namespaced_deployment(deployment_name,namespace)
        deployment_dict["namespace"] = deploy_ret.metadata.namespace
        deployment_dict["deployment_name"] = deploy_ret.metadata.name
        deployment_dict["replicas"] = deploy_ret.status.replicas
        deployment_dict["available_replicas"] = deploy_ret.status.available_replicas
        deployment_info.append(deployment_dict)
        return deployment_info

    def get_deployment_pod_status(self, namespace, deployment_name):
        """
        获取deployment pod的状态和信息
        :param api_instance:CoreV1Api
        :param namespace:
        :param deployment_name:
        :return:
        """
        err_msg = None
        s_flag = True
        deployment_name = deployment_name.lower()
        try:
            api_instance = self.corev1
            api_response = api_instance.list_namespaced_pod(namespace)
            result = api_response.items
            for res in result:
                pod_name = res.metadata.name
                if deployment_name in pod_name:
                    res = api_instance.read_namespaced_pod(pod_name, namespace)
                    conditions = res.status.conditions
                    if conditions:
                        for cond in conditions:
                            if cond.status == 'False':
                                err_msg = cond.message
                                s_flag = False
                    phase = res.status.phase
                    container_statuses=res.status.container_statuses
                    if container_statuses:
                        waiting = res.status.container_statuses[0].state.waiting
                        if phase is not None and waiting is not None:
                            message = waiting.message
                            if message is not None:
                                err_msg = str(err_msg) + " , " + waiting.message
                                s_flag = False
                    mesg = res.status.message
                    if mesg and phase != "Running":
                        err_msg = str(err_msg) + " , " + mesg
                        s_flag = False
                if not s_flag:
                    return s_flag, err_msg
        except Exception as e:
            Log.logger.error("get deployment's pod status error: %s" ,str(e))
        return s_flag, err_msg

    def get_namespace_pod_list_info(self,namespace):
        code = 200
        err_msg = None
        vm_info_dict = {}
        try:
            api_instance = self.corev1
            api_response = api_instance.list_namespaced_pod(namespace)
            for i in api_response.items:
                name = i.metadata.name
                status = i.status.phase
                physical_server = i.spec.node_name
                if status == "Running":
                    vm_state = "active"
                else:
                    vm_state = "shutoff"
                ip = i.status.pod_ip
                vm_info_dict[name] = [ip, vm_state,physical_server]
        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "get namespace pod list info error {e}".format(e=str(e))
        return vm_info_dict,err_msg,code

    def list_namespace_all_pod_info(self,namespace):
        code = 200
        err_msg = None
        pod_info_list = []
        try:
            api_instance = self.corev1
            api_response = api_instance.list_namespaced_pod(namespace)
            for i in api_response.items:
                pod_info_dict={}
                pod_info_dict["pod_name"] = i.metadata.name
                status = i.status.phase
                if status == "Running":
                    vm_state = "active"
                else:
                    vm_state = "shutoff"
                pod_info_dict["status"] = vm_state
                pod_info_dict["ip"] = i.status.pod_ip
                pod_info_dict["host_ip"] = i.status.host_ip
                pod_info_dict["node_name"] = i.spec.node_name
                pod_info_list.append(pod_info_dict)

        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "list namespace pod  info error {e}".format(e=str(e))
        return pod_info_list, err_msg, code

    def delete_deployment_pod(self,name,namespace):
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            body = client.V1DeleteOptions()
            api_response = api_instance.delete_namespaced_pod(name, namespace,body)
        except Exception as e:
            code = 500
            err_msg = "delete deployment pod error {}".format(str(e))
        return  err_msg,code




class K8sServiceApi(object):

    def __init__(self):

        config.load_kube_config(config_file=K8S_CONF_PATH)
        self.corev1 = client.CoreV1Api()

    def create_service_object(self,service_name,namespace,sercice_port):
        """

        :param service_name:"filebeat-test"
        :param namespace:"test-uop"
        :param sercice_port:8081
        :return:
        """
        service_name = service_name.lower()
        spec = client.V1ServiceSpec(
            cluster_ip="None",
            ports=[
                client.V1ServicePort(
                    name="http",
                    protocol="TCP",
                    port=sercice_port,
                )
            ],
            selector={
                "app": service_name
            }
        )
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=service_name,
                namespace=namespace,
                labels={
                    "app": service_name
                }
            ),
            spec=spec,
        )

        return service

    def create_service(self, service,namespace):
        """
        创建service
        :param api_instance:CoreV1Api
        :param service:
        :param namespace:
        :return:
        """
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            api_response = api_instance.create_namespaced_service(
                body=service,
                namespace=namespace)
        except Exception as e:
            err_msg = "create service error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def delete_service(self,service_name,namespace):
        """
        删除service
        :param api_instance:CoreV1Api
        :param service_name:
        :param namespace:
        :return:
        """
        err_msg = None
        code=200
        try:
            service_name = service_name.lower()
            api_instance = self.corev1
            api_response = api_instance.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
            )
        except Exception as e:
            err_msg = "delete service error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def get_service(self,service_name,namespace):
        """

        :param api_instance:CoreV1Api
        :param service_name:
        :param namespace:
        :return:
        """
        code = 200
        msg = None
        try:
            api_instance = self.corev1
            service_name = service_name.lower()
            api_response = api_instance.read_namespaced_service(service_name, namespace)
            msg=api_response
        except Exception as e:
            msg = "get service error %s" % str(e)
            code = get_k8s_err_code(e)
        return msg,code

    def get_service_status(self,service_name,namespace):
        """

        :param api_instance:CoreV1Api
        :param service_name:
        :param namespace:
        :return:
        """
        code = 200
        err_msg = None
        try:
            api_instance = self.corev1
            service_name = service_name.lower()
            api_response = api_instance.read_namespaced_service_status(service_name, namespace)
            status = api_response.status
            if status:
                status = "active"
        except Exception as e:
            err_msg = "get service error status %s" % str(e)
            code = get_k8s_err_code(e)
        return status,err_msg,code

class K8sIngressApi(object):

    def __init__(self):

        config.load_kube_config(config_file=K8S_CONF_PATH)
        self.extensionsv1 = client.ExtensionsV1beta1Api()
        self.deletev1 = client.V1DeleteOptions()
        self.force_deletev1 = client.V1DeleteOptions(
            propagation_policy='Background',
            grace_period_seconds=5)

    def create_ingress_object(self,ingress_name,namespace,service_name,service_port,domains,lb_methods,domain_paths):
        """

        :param ingress_name:"tomcat-cssapi-ingress"
        :param namespace:"test-uop"
        :param service_name:"filebeat-test"
        :param service_port:8081
        :param host:"tomcat.k8s.me"
        :return:
        """
        service_name = service_name.lower()
        ingress_name = ingress_name.lower()
        rules=[]
        domain_list = domains.strip().split(',')
        domain_path_list = domain_paths.strip().split(',')
        domain_info_list = zip(domain_list,domain_path_list)
        for domain_info in domain_info_list:
            domain = domain_info[0]
            domain_path = domain_info[1]
            if not domain_path:
                domain_path = "/"
            else:
                domain_path = "/{domain_path}".format(domain_path=domain_path)
            rule=client.V1beta1IngressRule(
                host=domain,
                http=client.V1beta1HTTPIngressRuleValue(
                    paths=[
                        client.V1beta1HTTPIngressPath(
                            path=domain_path,
                            backend=client.V1beta1IngressBackend(
                                service_name=service_name,
                                service_port=service_port,
                            )
                        )
                    ]
                )
            )
            rules.append(rule)
        spec = client.V1beta1IngressSpec(
            rules=rules
        )
        ingress = client.V1beta1Ingress(
            api_version="extensions/v1beta1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=ingress_name,
                namespace=namespace,
                annotations = {
                          # lb_methods: round_robin/least_conn/ip_hash
                          "lb_methods": lb_methods
                      },
            ),
            spec=spec
        )

        return ingress

    def update_ingress_object(self,ingress_name,namespace,service_name,service_port,domains,domain_paths):
        """
        更新ingress
        :param ingress_name:
        :param namespace:
        :param service_name:
        :param service_port:
        :param domain:
        :return:
        """
        service_name = service_name.lower()
        ingress_name = ingress_name.lower()
        rules = []
        domain_list = domains.strip().split(',')
        domain_path_list = domain_paths.strip().split(',')
        domain_info_list = zip(domain_list, domain_path_list)
        for domain_info in domain_info_list:
            domain = domain_info[0]
            domain_path = domain_info[1]
            if not domain_path:
                domain_path = "/"
            else:
                domain_path = "/{domain_path}".format(domain_path=domain_path)
            rule = client.V1beta1IngressRule(
                host=domain,
                http=client.V1beta1HTTPIngressRuleValue(
                    paths=[
                        client.V1beta1HTTPIngressPath(
                            path=domain_path,
                            backend=client.V1beta1IngressBackend(
                                service_name=service_name,
                                service_port=service_port,
                            )
                        )
                    ]
                )
            )
            rules.append(rule)
        spec = client.V1beta1IngressSpec(
            rules=rules
        )
        ingress = client.V1beta1Ingress(
            api_version="extensions/v1beta1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=ingress_name,
                namespace=namespace,
                # annotations={
                #     # lb_methods: round_robin/least_conn/ip_hash
                #     "lb_methods": "least_conn"
                # },
            ),
            spec=spec
        )

        return ingress

    def create_ingress(self, ingress,namespace):
        """
        创建ingress
        :param api_instance:ExtensionsV1beta1Api()
        :param ingress:
        :param namespace:
        :return:
        """
        err_msg=None
        code=200
        try:
            api_instance = self.extensionsv1
            api_response = api_instance.create_namespaced_ingress(
                body=ingress,
                namespace=namespace)
        except Exception as e:
            err_msg = "create ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def update_ingress(self, ingress,ingress_name, namespace):
        """
        更新ingress
        :param api_instance:ExtensionsV1beta1Api()
        :param ingress:
        :param namespace:
        :return:
        """
        err_msg = None
        code = 200
        try:
            ingress_name = ingress_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.patch_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=ingress
            )
        except Exception as e:
            err_msg = "update ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code


    def delete_ingress(self,ingress_name,namespace):
        """
        删除ingress
        :param api_instance:ExtensionsV1beta1Api()
        :param ingress_name:
        :param namespace:
        :return:
        """
        err_msg=None
        code=200
        try:
            ingress_name = ingress_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.delete_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=self.deletev1
            )
        except Exception as e:
            err_msg = "delete ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code
    def delete_force_ingress(self,ingress_name,namespace):
        """
        强制删除ingress
        :param api_instance:ExtensionsV1beta1Api()
        :param ingress_name:
        :param namespace:
        :return:
        """
        err_msg=None
        code=200
        try:
            ingress_name = ingress_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.delete_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=self.force_deletev1
            )
        except Exception as e:
            err_msg = "delete ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    def get_ingress(self, ingress_name, namespace):
        msg = None
        code = 200
        try:
            ingress_name = ingress_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.read_namespaced_ingress(ingress_name, namespace)
            msg = api_response
        except Exception as e:
            msg= "get ingress error %s" % str(e)
            code=get_k8s_err_code(e)
        return  msg,code

    def get_ingress_status(self, ingress_name, namespace):
        err_msg = None
        code = 200
        try:
            ingress_name = ingress_name.lower()
            api_instance = self.extensionsv1
            api_response = api_instance.read_namespaced_ingress_status(ingress_name, namespace)
            status = api_response.status
            if status:
                status = "active"
        except Exception as e:
            err_msg= "get ingress status error %s" % str(e)
            code=get_k8s_err_code(e)
        return  status,err_msg,code

class K8sLogApi(object):

    def __init__(self):

        config.load_kube_config(config_file=K8S_CONF_PATH)
        self.corev1 = client.CoreV1Api()

    def get_namespace_pod_log(self,pod_name,namespace,container):
        code=200
        try:
            api_instance = self.corev1
            api_response = api_instance.read_namespaced_pod_log(pod_name, namespace,container=container,previous=False,limit_bytes = 1024*1024)
            msg=api_response
        except Exception as e:
            code=get_k8s_err_code(e)
            msg = "get pod log error %s" % str(e)
        return msg,code

    def get_deployment_log(self, deployment_name, namespace):
        code = 200
        try:
            deployment_name = deployment_name.lower()
            deployment_info_list=K8sDeploymentApi().get_deployment_pod_info(namespace,deployment_name)
            if deployment_info_list:
                pod_name = deployment_info_list[0]["pod_name"]
                container="app"
                msg = self.get_namespace_pod_log(pod_name,namespace,container)
            else:
                msg=""
        except Exception as e:
            code = get_k8s_err_code(e)
            msg = "get deployment log error %s" % str(e)
        return msg, code

class K8sNamespaceApi(object):

    def __init__(self):
        config.load_kube_config(K8S_CONF_PATH)
        self.corev1 = client.CoreV1Api()
        self.deletev1 = client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )


    def create_namespace_object(self,namespace_name):
        namespace_name = namespace_name.lower()
        namespace = client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata=client.V1ObjectMeta(name=namespace_name))

        return namespace

    def create_namespace(self,namespace):
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            api_response = api_instance.create_namespace(body=namespace)
        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "create namespace error {e}".format(e=str(e))
        return err_msg,code

    def delete_namespace(self,namespace_name):
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            api_response = api_instance.delete_namespace(name=namespace_name,
                                                         body=self.deletev1)
        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "delete namespace error {e}".format(e=str(e))
        return err_msg, code

    def list_namespace(self):
        err_msg = None
        code = 200
        name_list=[]
        try:
            api_instance = self.corev1
            api_response = api_instance.list_namespace()
            for item in api_response.items:
                name=item.metadata.name
                name_list.append(name)
        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "list namespace error {e}".format(e=str(e))
        return name_list,err_msg,code

    def get_namespace_status(self,namespace_name):
        err_msg = None
        code = 200
        status = None
        try:
            api_instance = self.corev1
            api_response = api_instance.read_namespace_status(namespace_name)
            status=api_response.status.phase
        except Exception as e:
            code = get_k8s_err_code(e)
            err_msg = "get namespace status error {e}".format(e=str(e))
        return status,err_msg,code

class K8sConfigMapApi(object):

    def __init__(self):
        config.load_kube_config(K8S_CONF_PATH)
        self.corev1 = client.CoreV1Api()
        self.deletev1 = client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )

    def create_config_map_object(self,config_map_nane,namespace,data):

        config_map = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(
                name=config_map_nane,
                namespace=namespace),
            data=data)

        return config_map

    def create_config_map(self, config_map,namespace):
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            api_response = api_instance.create_namespaced_config_map(
                body=config_map,
                namespace=namespace)
        except Exception as e:
            err_msg = "create config map error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code

    def delete_config_map(self,config_map_nane,namespace):
        err_msg = None
        code = 200
        try:
            api_instance = self.corev1
            api_response = api_instance.delete_namespaced_config_map(
                name=config_map_nane,
                namespace=namespace,
                body=self.deletev1)
        except Exception as e:
            err_msg = "delete config map error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code

    def get_config_map(self,config_map_nane,namespace):
        err_msg = None
        code = 200
        res = None
        try:
            api_instance = self.corev1
            api_response = api_instance.read_namespaced_config_map(config_map_nane, namespace)
            res=api_response
        except Exception as e:
            err_msg = "get config map  error %s" % str(e)
            code = get_k8s_err_code(e)
        return res,err_msg, code

    def list_namespace_config_map(self,namespace):
        err_msg = None
        code = 200
        config_map_list=[]
        try:
            api_instance = self.corev1
            api_response = api_instance.list_namespaced_config_map(namespace)
            res = api_response
            for r in res.items:
                config_map_name=r.metadata.name
                config_map_list.append(config_map_name)
        except Exception as e:
            err_msg = "list namespace config map  error %s" % str(e)
            code = get_k8s_err_code(e)
        return config_map_list, err_msg, code




