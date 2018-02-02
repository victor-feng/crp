# -*- coding: utf-8 -*-

from crp.openstack import OpenStack
from crp.openstack2 import OpenStack as OpenStack2
from crp.log import Log
from config import configs, APP_ENV

AVAILABILITY_ZONE = configs[APP_ENV].AVAILABILITY_ZONE
AVAILABILITY_ZONE2 = configs[APP_ENV].AVAILABILITY_ZONE2



class OpenStack_Api(object):

    @classmethod
    def get_hypervisors_statistics(cls,env):

        vcpus = 0
        vcpus_used = 0
        memory_mb = 0
        memory_mb_used = 0
        local_gb = 0
        local_gb_used = 0
        running_vms = 0
        target_zone = None
        try:
            nova_cli = OpenStack.nova_client
            availability_zones = nova_cli.availability_zones.list()
            hypervisors = nova_cli.hypervisors.list()
            for zone in availability_zones:
                if AVAILABILITY_ZONE[env] == zone.zoneName:
                    target_zone = zone
                    break
            hosts = []
            if target_zone:
                hosts = target_zone.hosts.keys()

            for hypervisor in hypervisors:
                if hypervisor.hypervisor_hostname in hosts:
                    vcpus = vcpus + hypervisor.vcpus
                    vcpus_used = vcpus_used + hypervisor.vcpus_used
                    memory_mb = memory_mb + hypervisor.memory_mb
                    memory_mb_used = memory_mb_used + hypervisor.memory_mb_used
                    local_gb = local_gb + hypervisor.local_gb
                    local_gb_used = local_gb_used + hypervisor.local_gb_used
                    running_vms = running_vms + hypervisor.running_vms
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack get hypervisors statistics error %s",err_msg)
        return vcpus, vcpus_used, memory_mb, memory_mb_used, local_gb, local_gb_used, running_vms

    @classmethod
    def get_availability_zones(cls):
        azs = []
        nova_cli = OpenStack.nova_client
        try:
            for az_item in nova_cli.availability_zones.list():
                if az_item.zoneName != 'internal':
                    Log.logger.debug("az_item.hosts: %s, az_item.zoneName: %s, az_item.zoneState: %s",
                                  az_item.hosts, az_item.zoneName, az_item.zoneState)
                    azs.append({
                        "pool_name": az_item.zoneName,
                        "hosts": az_item.hosts.keys()
                    })
            return azs 
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack get availability zones error %s",err_msg)
            return None
            

class OpenStack2_Api(object):

    @classmethod
    def get_hypervisors_statistics(cls, env):

        vcpus = 0
        vcpus_used = 0
        memory_mb = 0
        memory_mb_used = 0
        local_gb = 0
        local_gb_used = 0
        running_vms = 0
        target_zone = None
        try:
            nova_cli = OpenStack2.nova_client
            availability_zones = nova_cli.availability_zones.list()
            hypervisors = nova_cli.hypervisors.list()
            for zone in availability_zones:
                if AVAILABILITY_ZONE2[env] == zone.zoneName:
                    target_zone = zone
                    break
            hosts = []
            if target_zone:
                hosts = target_zone.hosts.keys()

            for hypervisor in hypervisors:
                if hypervisor.hypervisor_hostname in hosts:
                    vcpus = vcpus + hypervisor.vcpus
                    vcpus_used = vcpus_used + hypervisor.vcpus_used
                    memory_mb = memory_mb + hypervisor.memory_mb
                    memory_mb_used = memory_mb_used + hypervisor.memory_mb_used
                    local_gb = local_gb + hypervisor.local_gb
                    local_gb_used = local_gb_used + hypervisor.local_gb_used
                    running_vms = running_vms + hypervisor.running_vms
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack2 get hypervisors statistics error %s",err_msg)
        return vcpus, vcpus_used, memory_mb, memory_mb_used, local_gb, local_gb_used, running_vms

    @classmethod
    def get_availability_zones(cls):
        azs = []
        nova_cli = OpenStack2.nova_client
        try:
            for az_item in nova_cli.availability_zones.list():
                if az_item.zoneName != 'internal':
                    Log.logger.debug("az_item.hosts: %s, az_item.zoneName: %s, az_item.zoneState: %s",
                                  az_item.hosts, az_item.zoneName, az_item.zoneState)
                    azs.append({
                        "pool_name": az_item.zoneName,
                        "hosts": az_item.hosts.keys()
                    })
            return azs 
        except Exception as e:
            err_msg=str(e)
            Log.logger.error("CRP OpenStack get availability zones error %s",err_msg)
            return None

    @classmethod
    def get_hypervisor_hosts(cls, host_set):

        hosts = []
        try:
            nova_cli = OpenStack2.nova_client
            rst = nova_cli.hypervisors.list(detailed=True)
            for host_item in rst:
                if host_set is None or \
                                host_item.hypervisor_hostname in host_set:
                    hosts.append({
                        "host_name": host_item.hypervisor_hostname,
                        "host_ip": host_item.host_ip,
                        "running_vms": host_item.running_vms,
                        "vcpu_total": host_item.vcpus,
                        "vcpu_use": host_item.vcpus_used,
                        "memory_mb_total": host_item.memory_mb,
                        "memory_mb_use": host_item.memory_mb_used,
                        "storage_gb_total": host_item.local_gb,
                        "storage_gb_use": host_item.local_gb_used,
                    })
            return hosts
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get hypervisor hosts error %s", err_msg)
            return None

    @classmethod
    def get_hypervisor_statistics(cls):

        hypervisors_statistics = {}
        try:
            nova_cli = OpenStack2.nova_client
            statistics = nova_cli.hypervisors.statistics()
            if statistics:
                hypervisors_statistics["running_vms"] = statistics.running_vms
                hypervisors_statistics["vcpu_total"] = statistics.vcpus
                hypervisors_statistics["vcpu_use"] = statistics.vcpus_used
                hypervisors_statistics["memory_mb_total"] = statistics.memory_mb
                hypervisors_statistics["memory_mb_use"] = statistics.memory_mb_used
                hypervisors_statistics["storage_gb_total"] = statistics.local_gb
                hypervisors_statistics["storage_gb_use"] = statistics.local_gb_used
            return hypervisors_statistics
        except Exception as e:
            err_msg = str(e)
            Log.logger.error("CRP OpenStack get hypervisor statistics error %s", err_msg)
            return None
