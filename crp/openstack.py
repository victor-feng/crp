# -*- coding: utf-8 -*-
from novaclient import client as novaclient


def openstack_client_setting():
    pass


class OpenStack(object):
    nova_c = None
    neutron_c = None
    glance_c = None
    cinder_c = None
    keystone_c = None

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

    @property
    def glance_client(self):
        if OpenStack.glance_c is not None:
            return OpenStack.glance_c

    @glance_client.setter
    def glance_client(self, value):
        if value is not None:
            OpenStack.glance_c = value

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
