# -*- coding: utf-8 -*-
from novaclient.v1_1 import client as nova_client
from cinderclient.v1 import client as cinder_client
from neutronclient.neutron import client as neutron_client
# from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient import session
from glanceclient.v1 import client as glance_client
from config import APP_ENV, configs


OPENRC_PATH = configs[APP_ENV].OPENRC_PATH


def openstack_client_setting():
    info = AuthInfo(OPENRC_PATH)
    info.get_env(info.rc)
    OpenStack.auth_info = info
    OpenStack.nova_client = nova_client.Client(username=info.user_name, api_key=info.user_password,
                                               project_id=info.tenant_name, auth_url=info.auth_url)
    # OpenStack.keystone_client = keystone_client.Client(username=info.user_name, password=info.user_password,
    #                                                    tenant_name=info.tenant_name, auth_url=info.auth_url)
    OpenStack.neutron_client = neutron_client.Client('2.0', username=info.user_name, password=info.user_password,
                                                     tenant_name=info.tenant_name, auth_url=info.auth_url)
    OpenStack.cinder_client = cinder_client.Client(username=info.user_name, api_key=info.user_password,
                                                   project_id=info.tenant_name, auth_url=info.auth_url)
    OpenStack.cinder_client.format = 'json'

    # # just for glance now.
    # def get_endpoint():
    #     service_list = OpenStack.keystone_client.services.list()
    #     for i in range(len(service_list)):
    #         if service_list[i].type == "image":
    #             glance_id = service_list[i].id
    #     if glance_id == None:
    #         return
    #     endpoint_list = OpenStack.keystone_client.endpoints.list()
    #     for j in range(len(endpoint_list)):
    #         if endpoint_list[j].service_id == glance_id:
    #             return endpoint_list[j].publicurl
    #
    # glance_endpoint = get_endpoint()
    # OpenStack.glance_client = glance_client.Client(endpoint=glance_endpoint, token=OpenStack.keystone_client.auth_token)

    # g_client = OpenStack.glance_client()
    # filters = {'name': 'trove-centos6-liberty-mm-docker-29'}
    # kwargs = {'filters': filters}
    # images = g_client.images.list(**kwargs)
    # for item in images:
    #     print type(item)
    #     print item


class AuthInfo(object):
    """
    get infomation from openrc file.
    """
    def __init__(self, rc_file):
        self.url_suffix = "35357/v2.0"
        self.user_name = None
        self.tenant_name = None
        self.user_password = None
        self.auth_url = None
        self.keystone_token = None
        with open(rc_file, 'r') as f:
            self.rc = f.read().split('\n')

    @classmethod
    def _value_inline(cls,line):
        return line.split('=')[1].split('\'')[1]

    def get_env(self, rc):
        for line in rc:
            if 'OS_USERNAME' in line:
                self.user_name = self._value_inline(line)
            elif 'OS_TENANT_NAME' in line:
                self.tenant_name = self._value_inline(line)
            elif 'OS_PASSWORD' in line:
                self.user_password = self._value_inline(line)
            elif 'OS_AUTH_URL' in line:
                tmp = self._value_inline(line).split(':')
                self.auth_url = tmp[0] + ":" + tmp[1] + ":" + self.url_suffix

        # I dont know how to get keystone token, Set it to the value of user_password.
        self.keystone_token = self.user_password


class OpenStack(object):
    auth_i = None
    nova_c = None
    neutron_c = None
    glance_c = None
    cinder_c = None
    keystone_c = None

    @property
    def auth_info(self):
        return OpenStack.auth_i

    @auth_info.setter
    def auth_info(self, value):
        if value is not None:
            OpenStack.auth_i = value

    @property
    def nova_client(self):
        if OpenStack.nova_c is not None:
            return OpenStack.nova_c

    @nova_client.setter
    def nova_client(self, value):
        if value is not None:
            OpenStack.nova_c = value

    @property
    def neutron_client(self):
        if OpenStack.neutron_c is not None:
            return OpenStack.neutron_c

    @neutron_client.setter
    def neutron_client(self, value):
        if value is not None:
            OpenStack.neutron_c = value

    # @property
    # def glance_client(self):
    #     if OpenStack.glance_c is not None:
    #         return OpenStack.glance_c

    # @glance_client.setter
    # def glance_client(self, value):
    #     if value is not None:
    #         OpenStack.glance_c = value

    @property
    def cinder_client(self):
        if OpenStack.cinder_c is not None:
            return OpenStack.cinder_c

    @cinder_client.setter
    def cinder_client(self, value):
        if value is not None:
            OpenStack.cinder_c = value

    @property
    def keystone_client(self):
        if OpenStack.keystone_c is not None:
            return OpenStack.keystone_c

    @keystone_client.setter
    def keystone_client(self, value):
        if value is not None:
            OpenStack.keystone_c = value

    @classmethod
    def find_vm_from_ipv4(cls, ip):
        search_opts = {'ip': ip}
        if cls.nova_client is not None:
            vms = cls.nova_client.servers.list(detailed=True, search_opts=search_opts)
            for vm in vms:
                for _, ips in vm.addresses.items():
                    for i in ips:
                        i = i['addr'].encode("utf-8")
                        if i == ip :
                            return vm
        return None

    @classmethod
    def _get_endpoint_and_token(
            cls, service_type,
            auth_url, username,
            password, tenant_name):
        kwargs = {
            'auth_url': auth_url,
            'username': username,
            'password': password,
            'tenant_name': tenant_name,
        }
        ks_session = session.Session.construct(kwargs)
        auth = v2_auth.Password(
            auth_url=auth_url, username=username,
            password=password, tenant_name=tenant_name)
        ks_session.auth = auth
        token = ks_session.get_token()
        endpoint = ks_session.get_endpoint(
            service_type=service_type, endpoint_type='public')
        return endpoint, token

    @classmethod
    def glance_client(cls):

        if OpenStack.auth_info is not None:
            glance_endpoint, token = cls._get_endpoint_and_token(
                'image',
                OpenStack.auth_info.auth_url,
                OpenStack.auth_info.user_name,
                OpenStack.auth_info.user_password,
                OpenStack.auth_info.tenant_name)

            OpenStack.glance_c = glance_client.Client(
                endpoint=glance_endpoint, token=token)

        if OpenStack.glance_c is not None:
            return OpenStack.glance_c

    @classmethod
    def get_cinder_endpoint_and_token(cls):
        cinder_endpoint, token = cls._get_endpoint_and_token(
            'volume',
            OpenStack.auth_info.auth_url,
            OpenStack.auth_info.user_name,
            OpenStack.auth_info.user_password,
            OpenStack.auth_info.tenant_name)
        return cinder_endpoint, token
