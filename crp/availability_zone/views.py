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
            azs_cloud1 = OpenStack_Api.get_availability_zones()
            azs_cloud2 = OpenStack2_Api.get_availability_zones()
            Log.logger.debug("azs:{},{}".format(azs_cloud1, azs_cloud2))
            azs_cloud1.extend(azs_cloud2)
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
                    "res": azs_cloud1
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
           Log.logger.debug(type(args.host))
           host_set = set(args.host)
       Log.logger.debug('HostsListAPI: query %s' % host_set)

       try:
           hosts = OpenStack2_Api.get_hypervisor_hosts(host_set)
       except Exception as e:
           Log.logger.error('get hosts err: %s' % e.args)
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

       try:
           hypervisors_statistics = OpenStack2_Api.get_hypervisor_statistics()
       except Exception as e:
           Log.logger.error('get hypervisors_statistics err: %s' % e.args)
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
                   "res": hypervisors_statistics
               }
           }
           return res, 200


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
az_api.add_resource(HostsListAPI, '/getHosts')
az_api.add_resource(StatisticAPI, '/statistics')
az_api.add_resource(UOPStatisticAPI, '/uopStatistics')
