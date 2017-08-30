# -*- coding: utf-8 -*-
import logging

from flask_restful import reqparse, Api, Resource

# TODO: import * is bad!!!
from crp.taskmgr import *

from crp.availability_zone import az_blueprint
from crp.availability_zone.errors import az_errors
from crp.openstack import OpenStack
from crp.log import Log
from config import configs, APP_ENV


# 配置可用域
AVAILABILITY_ZONE_AZ_UOP = configs[APP_ENV].AVAILABILITY_ZONE_AZ_UOP

az_api = Api(az_blueprint, errors=az_errors)

class AZListAPI(Resource):

    def get(self):
        azs = []
        try:
            nova_cli = OpenStack.nova_client
            for az_item in nova_cli.availability_zones.list():
                if az_item.zoneName != 'internal':
                    # Log.logger.debug(az_item.zoneName)
                    # Log.logger.debug(az_item.zoneState)
                    # Log.logger.debug(az_item.hosts)
                    logging.debug("az_item.hosts: %s, az_item.zoneName: %s, az_item.zoneState: %s", 
                                  az_item.hosts, az_item.zoneName, az_item.zoneState)
                    azs.append({
                        "pool_name": az_item.zoneName,
                        "hosts": az_item.hosts.keys()
                    })
        except Exception as e:
            logging.error('get az err: %s' % e.message)
            #Log.logger.error('get az err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": azs
                }
            }
            return res, 200


class HostsListAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('host', type=str, location='args', action='append')

        args = parser.parse_args()
        host_set = None
        if args.host:
            # Log.logger.debug(type(args.host))
            logging.debug(type(args.host))
            host_set = set(args.host)
        logging.debug('HostsListAPI: query %s' % host_set)
        #Log.logger.debug('HostsListAPI: query %s' % host_set)

        hosts = []
        try:
            nova_cli = OpenStack.nova_client
            rst = nova_cli.hypervisors.list(detailed=True)
            # Log.logger.debug(len(rst))
            logging.debug(len(rst))
            for host_item in rst:
                # Log.logger.debug(dir(host_item))
                logging.debug(dir(host_item))
                if host_set is None or\
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
        except Exception as e:
            logging.error('get hosts err: %s' % e.message)
            #Log.logger.error('get hosts err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": hosts
                }
            }
            return res, 200


class StatisticAPI(Resource):

    def get(self):
        hypervisors_statistics = {}
        try:
            nova_cli = OpenStack.nova_client
            statistics = nova_cli.hypervisors.statistics()
            # Log.logger.debug(dir(statistics))
            logging.debug(dir(statistics))
            if statistics:
                hypervisors_statistics["running_vms"]= statistics.running_vms
                hypervisors_statistics["vcpu_total"]= statistics.vcpus
                hypervisors_statistics["vcpu_use"]= statistics.vcpus_used
                hypervisors_statistics["memory_mb_total"]= statistics.memory_mb
                hypervisors_statistics["memory_mb_use"]= statistics.memory_mb_used
                hypervisors_statistics["storage_gb_total"]= statistics.local_gb
                hypervisors_statistics["storage_gb_use"]= statistics.local_gb_used
        except Exception as e:
            #Log.logger.error('get hypervisors_statistics err: %s' % e.message)
            logging.error('get hypervisors_statistics err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": hypervisors_statistics
                }
            }
            return res, 200

class UOPStatisticAPI(Resource):

    def get(self):
        hypervisors_statistics = {}
        try:
            nova_cli = OpenStack.nova_client
            availability_zones = nova_cli.availability_zones.list()
            hypervisors = nova_cli.hypervisors.list()
            logging.info('-------availability_zones-----:%s',(availability_zones))
	    zones = [ zone for zone in availability_zones if AVAILABILITY_ZONE_AZ_UOP==zone.zoneName ]
            vcpus = 0
            vcpus_used = 0
            memory_mb = 0
            memory_mb_used = 0
            local_gb = 0
            local_gb_used = 0  
            running_vms = 0 

            hosts = zones[0].hosts.keys()
            logging.info('-------hostname-------------:%s'%(hosts))
	    for hypervisor in hypervisors:
                if hypervisor.hypervisor_hostname in hosts:
                    vcpus = vcpus + hypervisor.vcpus
                    vcpus_used = vcpus_used + hypervisor.vcpus_used
                    memory_mb = memory_mb + hypervisor.memory_mb
                    memory_mb_used = memory_mb_used + hypervisor.memory_mb_used
                    local_gb = local_gb + hypervisor.local_gb
                    local_gb_used = local_gb_used + hypervisor.local_gb_used
                    running_vms = running_vms + hypervisor.running_vms
            
            if hypervisors:
                hypervisors_statistics["running_vms"] = running_vms
                hypervisors_statistics["vcpu_total"] = vcpus
                hypervisors_statistics["vcpu_use"] = vcpus_used
                hypervisors_statistics["memory_mb_total"] = memory_mb
                hypervisors_statistics["memory_mb_use"] = memory_mb_used
                hypervisors_statistics["storage_gb_total"] = local_gb
                hypervisors_statistics["storage_gb_use"] = local_gb_used
        except Exception as e:
            #Log.logger.error('get hypervisors_statistics err: %s' % e.message)
            logging.error('get azuop_hypervisors_statistics err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": hypervisors_statistics
                }
            }
            return res, 200

az_api.add_resource(AZListAPI, '/azs')
az_api.add_resource(HostsListAPI, '/getHosts')
az_api.add_resource(StatisticAPI, '/statistics')
az_api.add_resource(UOPStatisticAPI, '/uopStatistics')
