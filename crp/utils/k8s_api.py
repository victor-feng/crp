# -*- coding: utf-8 -*-


from kubernetes import client
from kubernetes import  config
from config import APP_ENV, configs



K8S_CONF_PATH = configs[APP_ENV].K8S_CONF_PATH



def k8s_client_setting(k8s_conf_path):
    config.load_kube_config(k8s_conf_path)
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

def create_deployment_object(deployment_name,container_name,image_url,port,labels_name):
    """
    创建deployment模板
    :param deployment_name:
    :param container_name:
    :param image_url:
    :param port:
    :param labels_name:
    :return:
    """
    # Configureate Pod template container
    container = client.V1Container(
        name=container_name,
        image=image_url,
        ports=[client.V1ContainerPort(container_port=port)])
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": labels_name}),
        spec=client.V1PodSpec(containers=[container]))
    # Create the specification of deployment
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=3,
        template=template)
    # Instantiate the deployment object
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=spec)

    return deployment


def create_deployment(api_instance, deployment,namespace):
    """
    创建deployment
    :param api_instance:
    :param deployment:
    :return:
    """
    # Create deployement
    api_response = api_instance.create_namespaced_deployment(
        body=deployment,
        namespace=namespace)
    print("Deployment created. status='%s'" % str(api_response.status))


def update_deployment(api_instance, deployment,deployment_name,new_image_url,namespace):
    """
    更新deployment
    :param api_instance:
    :param deployment:
    :param deployment_name:
    :param new_image_url:
    :return:
    """
    # Update container image
    deployment.spec.template.spec.containers[0].image = new_image_url
    # Update the deployment
    api_response = api_instance.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=deployment)
    print("Deployment updated. status='%s'" % str(api_response.status))


def delete_deployment(api_instance,deployment_name,namespace):
    """
    删除deployment
    :param api_instance:
    :param deployment_name:
    :return:
    """
    # Delete deployment
    api_response = api_instance.delete_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5))
    print("Deployment deleted. status='%s'" % str(api_response.status))

def update_scale_deployment(api_instance,deployment,deployment_name,namespace):
    """
    deployment扩缩容
    :param api_instance:
    :param deployment:
    :param deployment_name:
    :param namespace:
    :return:
    """
    api_response = api_instance.patch_namespaced_deployment_scale(
        name=deployment_name,
        namespace=namespace,
        body=deployment)
    print("Deployment update scale. status='%s'" % str(api_response.status))






