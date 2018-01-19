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


class OpenStack2_Api(object):

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
