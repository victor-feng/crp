# -*- coding: utf-8 -*-



from crp.openstack import OpenStack
from crp.openstack2 import OpenStack as OpenStack2
from crp.log import Log

class OpenStack_Api(object):

    @classmethod
    def get_network_info(cls):
        networks=[]
        subnets=[]
        try:
            net_cli = OpenStack.neutron_client
            networks = net_cli.list_networks()
            networks = networks.get('networks', [])
            subnets = net_cli.list_subnets()["subnets"]
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack get network info error %s",err_msg)
        return networks,subnets

    @classmethod
    def get_posts(cls,network_id):
        ports=[]
        try:
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
            nova_cli = OpenStack.nova_client
            vm = nova_cli.servers.get(os_inst_id)
            vm_state = vm.status.lower()
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get vm status error %s", err_msg)
        return  vm_state

    @classmethod
    def get_all_vm_status(cls):
        vm_info_dict = {}
        try:
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
                vm_info_dict[os_inst_id] = [ip, status]
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get all vm status error %s", err_msg)
        return vm_info_dict



class OpenStack2_Api(object):

    @classmethod
    def get_network_info(cls):
        networks=[]
        subnets=[]
        try:
            net_cli = OpenStack2.neutron_client
            networks = net_cli.list_networks()
            networks = networks.get('networks', [])
            subnets = net_cli.list_subnets()["subnets"]
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack2 get network info error %s",err_msg)
        return networks,subnets

    @classmethod
    def get_posts(cls,network_id):
        ports=[]
        try:
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
                vm_info_dict[os_inst_id] = [ip, status]
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack2 get all vm status error %s", err_msg)
        return vm_info_dict






