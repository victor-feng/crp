# -*- coding: utf-8 -*-


from kubernetes import client
from kubernetes import  config
from config import APP_ENV, configs
from crp.utils.aio import get_k8s_err_code
import datetime



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

    @classmethod
    def create_deployment_object(cls,deployment_name,
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
                                 hostnames,
                                 ip,
                                 replicas
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
                host_aliases=[
                    client.V1HostAlias(hostnames=hostnames, ip=ip),
                ],
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
        spec = client.ExtensionsV1beta1DeploymentSpec(
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
        return deployment

    @classmethod
    def create_deployment(cls,api_instance, deployment,namespace):
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
            api_response = api_instance.create_namespaced_deployment(
                body=deployment,
                namespace=namespace)
        except Exception as e:
            err_msg = "create deployment error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def update_deployment_image_object(cls,deployment_name,filebeat_name):
        """
        deployment image 更新镜像时创建模板
        :param deployment_name:
        :return:
        """
        deployment_name = deployment_name.lower()
        filebeat_container = client.V1Container(
            name=filebeat_name,
        )
        app_container = client.V1Container(
            name="app",
            image="",
        )
        template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                containers=[
                    filebeat_container,
                    app_container,
                ],
            ),
        )
        spec = client.ExtensionsV1beta1DeploymentSpec(
            template=template,
        )

        # Instantiate the deployment object
        update_image_deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec,
        )

        return update_image_deployment

    @classmethod
    def update_deployment_image(cls,api_instance, update_image_deployment, deployment_name, new_image_url, namespace):
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
            deployment_name = deployment_name.lower()
            update_image_deployment.spec.template.spec.containers[1].image = new_image_url
            # Update the deployment
            api_response = api_instance.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=update_image_deployment)
        except Exception as e:
            err_msg = "update deployment image error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def delete_deployment(cls,api_instance, deployment_name, namespace):
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
            api_response = api_instance.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=5))
        except Exception as e:
            err_msg = "delete deployment error %s" %str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def update_deployment_replicas_object(cls,deployment_name):
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

    @classmethod
    def update_deployment_scale(cls,api_instance, update_replicas_deployment, deployment_name, namespace, new_replicas):
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
            update_replicas_deployment.spec.replicas = new_replicas
            api_response = api_instance.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body=update_replicas_deployment)
        except Exception as e:
            err_msg = "update deployment scale error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg, code

    @classmethod
    def get_deployment_status(cls,api_instance, namespace, deployment_name):
        """
        获取deployment状态
        :param api_instance:ExtensionsV1beta1Api()
        :param namespace:
        :param deployment_name:
        :return:
        """
        deployment_name = deployment_name.lower()
        api_response = api_instance.read_namespaced_deployment_status(deployment_name, namespace)
        ready_replicas=api_response.status.ready_replicas
        replicas=api_response.status.replicas
        if replicas == ready_replicas:
            return 'available'
        else:
            return 'unavailable'

    @classmethod
    def get_deployment_pod_info(cls, api_instance, namespace, deployment_name):
        """
        获取deployment pod的ip和宿主机主机名，pod名字
        :param api_instance:CoreV1Api
        :param namespace:
        :param deployment_name:
        :return:
        """
        deployment_name = deployment_name.lower()
        deployment_info_list = []
        api_response = api_instance.list_namespaced_pod(namespace)
        result = api_response.items
        for res in result:
            deployment_dict = {}
            pod_name = res.metadata.name
            node_name = res.spec.node_name
            pod_ip = res.status.pod_ip
            if deployment_name in pod_name:
                deployment_dict['deployment_name'] = deployment_name.low()
                deployment_dict['pod_ip'] = pod_ip
                deployment_dict['node_name'] = node_name
                deployment_dict['pod_name'] = pod_name
                deployment_info_list.append(deployment_dict)
        return deployment_info_list

    @classmethod
    def get_deployment(cls, api_instance, namespace, deployment_name):
        """
        获取deployment
        :param api_instance:ExtensionsV1beta1Api()
        :param namespace:
        :param deployment_name:
        :return:
        """
        deployment_name = deployment_name.lower()
        api_response = api_instance.read_namespaced_deployment(deployment_name, namespace)
        return api_response

    # 重启deployment下的全部pod
    @classmethod
    def restart_deployment_pod_object(cls,deployment_name):
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
    @classmethod
    def restart_deployment_pod(cls,api_instance, restart_deployment,deployment_name,namespace):
        # restart pod label
        deployment_name = deployment_name.lower()
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

    @classmethod
    def get_namespace_deployment_info(cls,api_instance,namespace):
        deployment_info=[]
        deploy_ret = api_instance.list_namespaced_deployment(namespace, watch=False)
        for i in deploy_ret.items:
            deployment_dict={}
            deployment_dict["namespace"] = i.metadata.namespace
            deployment_dict["deployment_name"] = i.metadata.name
            deployment_dict["replicas"] = i.status.replicas
            deployment_dict["available_replicas"] = i.status.available_replicas
            deployment_info.append(deployment_dict)
        return deployment_info

    @classmethod
    def get_deployment_info(cls, api_instance, namespace,deployment_name):
        deployment_name = deployment_name.lower()
        deployment_info = []
        deployment_dict = {}
        deploy_ret = api_instance.read_namespaced_deployment(deployment_name,namespace)
        deployment_dict["namespace"] = deploy_ret.metadata.namespace
        deployment_dict["deployment_name"] = deploy_ret.metadata.name
        deployment_dict["replicas"] = deploy_ret.status.replicas
        deployment_dict["available_replicas"] = deploy_ret.status.available_replicas
        deployment_info.append(deployment_dict)
        return deployment_info


class K8sServiceApi(object):

    @classmethod
    def create_service_object(cls,service_name,namespace,sercice_port):
        """

        :param service_name:"filebeat-test"
        :param namespace:"test-uop"
        :param sercice_port:8081
        :return:
        """
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

    @classmethod
    def create_service(cls,api_instance, service,namespace):
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
            api_response = api_instance.create_namespaced_service(
                body=service,
                namespace=namespace)
        except Exception as e:
            err_msg = "create service error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def delete_service(cls,api_instance,service_name,namespace):
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
            api_response = api_instance.delete_namespaced_service(
                name=service_name,
                namespace=namespace,
            )
        except Exception as e:
            err_msg = "delete service error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg
    @classmethod
    def get_service(cls,api_instance,service_name,namespace):
        """

        :param api_instance:CoreV1Api
        :param service_name:
        :param namespace:
        :return:
        """
        code = 200
        msg = None
        try:
            api_response = api_instance.read_namespaced_service(service_name, namespace)
            msg=api_response
        except Exception as e:
            msg = "get service error %s" % str(e)
            code = get_k8s_err_code(e)
        return msg,code


class K8sIngressApi(object):

    @classmethod
    def create_ingress_object(cls,ingress_name,namespace,service_name,service_port,domain):
        """

        :param ingress_name:"tomcat-cssapi-ingress"
        :param namespace:"test-uop"
        :param service_name:"filebeat-test"
        :param service_port:8081
        :param host:"tomcat.k8s.me"
        :return:
        """
        spec = client.V1beta1IngressSpec(
            rules=[
                client.V1beta1IngressRule(
                    host=domain,
                    http=client.V1beta1HTTPIngressRuleValue(
                        paths=[
                            client.V1beta1HTTPIngressPath(
                                backend=client.V1beta1IngressBackend(
                                    service_name=service_name,
                                    service_port=service_port,
                                )
                            )
                        ]
                    )
                )
            ]
        )
        ingress = client.V1beta1Ingress(
            api_version="extensions/v1beta1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=ingress_name,
                namespace=namespace
            ),
            spec=spec
        )

        return ingress

    @classmethod
    def create_ingress(cls,api_instance, ingress,namespace):
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
            api_response = api_instance.create_namespaced_ingress(
                body=ingress,
                namespace=namespace)
        except Exception as e:
            err_msg = "create ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def delete_ingress(cls,api_instance,ingress_name,namespace):
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
            api_response = api_instance.delete_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Foreground',
                    grace_period_seconds=5
                )
            )
        except Exception as e:
            err_msg = "delete ingress error %s" % str(e)
            code = get_k8s_err_code(e)
        return err_msg,code

    @classmethod
    def get_ingress(cls,api_instance, ingress_name, namespace):
        msg = None
        code = 200
        try:
            api_response = api_instance.read_namespaced_ingress(ingress_name, namespace)
            msg = api_response
        except Exception as e:
            msg= "get ingress error %s" % str(e)
            code=get_k8s_err_code(e)
        return  msg,code

class K8sLogApi(object):

    @classmethod
    def get_namespace_pod_log(cls,api_instance,pod_name,namespace,container):
        code=200
        try:
            api_response = api_instance.read_namespaced_pod_log(pod_name, namespace,container=container,previous=False,limit_bytes = 1024*1024)
            msg=api_response
        except Exception as e:
            code=get_k8s_err_code(e)
            msg = "get pod log error %s" % str(e)
        return msg,code

    @classmethod
    def get_deployment_log(cls, api_instance, deployment_name, namespace):
        code = 200
        try:
            deployment_name = deployment_name.lower()
            deployment_info_list=K8sDeploymentApi.get_deployment_pod_info(api_instance,namespace,deployment_name)
            if deployment_info_list:
                pod_name = deployment_info_list[0]["pod_name"]
                container="app"
                msg = cls.get_namespace_pod_log(api_instance,pod_name,namespace,container)
            else:
                msg=""
        except Exception as e:
            code = get_k8s_err_code(e)
            msg = "get deployment log error %s" % str(e)
        return msg, code






