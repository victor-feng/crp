# -*- coding: utf-8 -*-



from crp.openstack import OpenStack
from crp.openstack2 import OpenStack as OpenStack2
from crp.log import Log
from config import configs, APP_ENV
from crp.utils.aio import isopenrc
OS_EXT_PHYSICAL_SERVER_ATTR=configs[APP_ENV].OS_EXT_PHYSICAL_SERVER_ATTR
OPENRC_PATH = configs[APP_ENV].OPENRC_PATH
OPENRC2_PATH = configs[APP_ENV].OPENRC2_PATH

class OpenStack_Api(object):

    @classmethod
    def get_network_info(cls):
        subnet_info = {}
        name2id = {}
        try:
            if OPENRC_PATH:
                net_cli = OpenStack.neutron_client
                networks = net_cli.list_networks()
                networks = networks.get('networks', [])
                subnets = net_cli.list_subnets()["subnets"]
                for subnet in subnets:
                    network_id = subnet["network_id"]
                    sub_vlan=subnet["cidr"]
                    if network_id in subnet_info.keys():
                        subnet_info[network_id].append(sub_vlan)
                    else:
                        subnet_info[network_id] = [sub_vlan]
                for network in networks:
                    name = network.get('name')
                    id_ = network.get('id')
                    for network_id in subnet_info.keys():
                        if network_id == id_:
                            sub_vlans=subnet_info[network_id]
                            name2id[name] = [id_,sub_vlans,"1"]
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack get network info error %s",err_msg)
        return name2id

    @classmethod
    def get_ports(cls,network_id):
        ports=[]
        try:
            if OPENRC_PATH:
                net_cli = OpenStack.neutron_client
                ports = net_cli.list_ports(**{'network_id': network_id})
                ports = ports.get('ports',[])
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get port info error %s", err_msg)
        return  ports

    @classmethod
    def get_vm_status(cls,os_inst_id):
        vm_state = None
        try:
            if OPENRC_PATH:
                nova_cli = OpenStack.nova_client
                vm = nova_cli.servers.get(os_inst_id)
                vm_state = vm.status.lower()
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get vm status error %s", err_msg)
        return  vm_state
    @isopenrc(OPENRC_PATH,res={})
    @classmethod
    def get_all_vm_status(cls):
        vm_info_dict = {}
        try:
            #if OPENRC_PATH:
            nova_cli = OpenStack.nova_client
            vms = nova_cli.servers.list()
            for vm in vms:
                os_inst_id = vm.id
                ips = vm.networks
                if ips:
                    ip = vm.networks.values()[0][0]
                else:
                    ip = "127.0.0.1"
                status = vm.status.lower()
                physical_server = getattr(vm, OS_EXT_PHYSICAL_SERVER_ATTR)
                vm_info_dict[os_inst_id] = [ip, status,physical_server]
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get all vm status error %s", err_msg)
        return vm_info_dict



class OpenStack2_Api(object):

    @classmethod
    def get_network_info(cls):
        subnet_info = {}
        name2id = {}
        try:
            if OPENRC2_PATH:
                net_cli = OpenStack2.neutron_client
                networks = net_cli.list_networks()
                networks = networks.get('networks', [])
                subnets = net_cli.list_subnets()["subnets"]
                for subnet in subnets:
                    network_id = subnet["network_id"]
                    sub_vlan=subnet["cidr"]
                    if network_id in subnet_info.keys():
                        subnet_info[network_id].append(sub_vlan)
                    else:
                        subnet_info[network_id] = [sub_vlan]
                for network in networks:
                    name = network.get('name')
                    id_ = network.get('id')
                    for network_id in subnet_info.keys():
                        if network_id == id_:
                            sub_vlans=subnet_info[network_id]
                            name2id[name] = [id_,sub_vlans,"2"]
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack2 get network info error %s",err_msg)
        return name2id

    @classmethod
    def get_ports(cls,network_id):
        ports=[]
        try:
            if  OPENRC2_PATH:
                net_cli = OpenStack2.neutron_client
                ports = net_cli.list_ports(**{'network_id': network_id})
                ports = ports.get('ports',[])
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack2 get port info error %s", err_msg)
        return  ports

    @classmethod
    def get_vm_status(cls,os_inst_id):
        vm_state = None
        try:
            if OPENRC2_PATH:
                nova_cli = OpenStack2.nova_client
                vm = nova_cli.servers.get(os_inst_id)
                vm_state = vm.status.lower()
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack2 get vm status error %s", err_msg)
        return  vm_state

    @classmethod
    def get_all_vm_status(cls):
        vm_info_dict = {}
        try:
            if OPENRC2_PATH:
                nova_cli = OpenStack2.nova_client
                vms = nova_cli.servers.list()
                for vm in vms:
                    os_inst_id = vm.id
                    ips = vm.networks
                    if ips:
                        ip = vm.networks.values()[0][0]
                    else:
                        ip = "127.0.0.1"
                    status = vm.status.lower()
                    physical_server = getattr(vm, OS_EXT_PHYSICAL_SERVER_ATTR)
                    vm_info_dict[os_inst_id] = [ip, status,physical_server]
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack2 get all vm status error %s", err_msg)
        return vm_info_dict






