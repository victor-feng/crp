# -*- coding: utf-8 -*-


from flask_restful import reqparse, Api, Resource
from crp.availability_zone import az_blueprint
from crp.availability_zone.errors import az_errors
from handler import OpenStack_Api,OpenStack2_Api
from crp.log import Log
from crp.openstack import OpenStack


az_api = Api(az_blueprint, errors=az_errors)

class AZListAPI(Resource):

    def get(self):
        try:
            azs = OpenStack2_Api.get_availability_zones()
        except Exception as e:
            Log.logger.error('get az err: %s' % e.args)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.args
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


#class HostsListAPI(Resource):
#
#    def get(self):
#        parser = reqparse.RequestParser()
#        parser.add_argument('host', type=str, location='args', action='append')
#
#        args = parser.parse_args()
#        host_set = None
#        if args.host:
#            # Log.logger.debug(type(args.host))
#            Log.logger.debug(type(args.host))
#            host_set = set(args.host)
#        Log.logger.debug('HostsListAPI: query %s' % host_set)
#
#        hosts = []
#        try:
#            nova_cli = OpenStack.nova_client
#            rst = nova_cli.hypervisors.list(detailed=True)
#            Log.logger.debug(len(rst))
#            for host_item in rst:
#                Log.logger.debug(dir(host_item))
#                if host_set is None or\
#                                host_item.hypervisor_hostname in host_set:
#                    hosts.append({
#                        "host_name": host_item.hypervisor_hostname,
#                        "host_ip": host_item.host_ip,
#                        "running_vms": host_item.running_vms,
#                        "vcpu_total": host_item.vcpus,
#                        "vcpu_use": host_item.vcpus_used,
#                        "memory_mb_total": host_item.memory_mb,
#                        "memory_mb_use": host_item.memory_mb_used,
#                        "storage_gb_total": host_item.local_gb,
#                        "storage_gb_use": host_item.local_gb_used,
#                    })
#        except Exception as e:
#            Log.logger.error('get hosts err: %s' % e.args)
#            res = {
#                "code": 400,
#                "result": {
#                    "res": "failed",
#                    "msg": e.message
#                }
#            }
#            return res, 400
#        else:
#            res = {
#                "code": 200,
#                "result": {
#                    "msg": "请求成功",
#                    "res": hosts
#                }
#            }
#            return res, 200
#
#
#class StatisticAPI(Resource):
#
#    def get(self):
#        hypervisors_statistics = {}
#        try:
#            nova_cli = OpenStack.nova_client
#            statistics = nova_cli.hypervisors.statistics()
#            Log.logger.debug(dir(statistics))
#            if statistics:
#                hypervisors_statistics["running_vms"]= statistics.running_vms
#                hypervisors_statistics["vcpu_total"]= statistics.vcpus
#                hypervisors_statistics["vcpu_use"]= statistics.vcpus_used
#                hypervisors_statistics["memory_mb_total"]= statistics.memory_mb
#                hypervisors_statistics["memory_mb_use"]= statistics.memory_mb_used
#                hypervisors_statistics["storage_gb_total"]= statistics.local_gb
#                hypervisors_statistics["storage_gb_use"]= statistics.local_gb_used
#        except Exception as e:
#            Log.logger.error('get hypervisors_statistics err: %s' % e.args)
#            res = {
#                "code": 400,
#                "result": {
#                    "res": "failed",
#                    "msg": e.args
#                }
#            }
#            return res, 400
#        else:
#            res = {
#                "code": 200,
#                "result": {
#                    "msg": "请求成功",
#                    "res": hypervisors_statistics
#                }
#            }
#            return res, 200




class UOPStatisticAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str,location='json')
        args = parser.parse_args()
        env=args.env
        hypervisors_statistics = {}
        try:
            vcpus1, vcpus_used1, memory_mb1, memory_mb_used1, local_gb1, local_gb_used1, running_vms1 = OpenStack_Api.get_hypervisors_statistics(env)
            vcpus2, vcpus_used2, memory_mb2, memory_mb_used2, local_gb2, local_gb_used2, running_vms2 = OpenStack2_Api.get_hypervisors_statistics(
                env)
            vcpus = vcpus1 + vcpus2
            vcpus_used = vcpus_used1 + vcpus_used2
            memory_mb = memory_mb1 + memory_mb2
            memory_mb_used = memory_mb_used1 + memory_mb_used2
            local_gb = local_gb1 + local_gb2
            local_gb_used = local_gb_used1 + local_gb_used2
            running_vms = running_vms1 + running_vms2
            hypervisors_statistics["running_vms"] = running_vms
            hypervisors_statistics["vcpu_total"] = vcpus
            hypervisors_statistics["vcpu_use"] = vcpus_used
            hypervisors_statistics["memory_mb_total"] = memory_mb
            hypervisors_statistics["memory_mb_use"] = memory_mb_used
            hypervisors_statistics["storage_gb_total"] = local_gb
            hypervisors_statistics["storage_gb_use"] = local_gb_used

        except Exception as e:
            Log.logger.error('get azuop_hypervisors_statistics err: %s' % str(e.args))

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
#az_api.add_resource(HostsListAPI, '/getHosts')
#az_api.add_resource(StatisticAPI, '/statistics')
az_api.add_resource(UOPStatisticAPI, '/uopStatistics')
