# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource
from dns_api import *
from crp.dns import dns_set_blueprint
from crp.dns.errors import dns_set_errors
from crp.log import Log
import json
import subprocess
from config import configs, APP_ENV

DNS_ENV =  configs[APP_ENV].DNS_ENV

res = {
    "code": "",
    "result": {
        "res": "failed",
        "msg": ""
    }
}

dns_set_api = Api(dns_set_blueprint, errors=dns_set_errors)


class DnServerSet(Resource):
    """
    操作dns服务器
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location='args')
        parser.add_argument('domain', type=str, location='args')

        args = parser.parse_args()

        env = args.env
        domain = args.domain
        try:
            dns_api = NamedManagerApi()
            message = dns_api.named_domain_query(domain_name=domain)
            code = 200
            res['code'] = code
            res['result']['res'] = "success"
            res['result']['msg'] = message
        except Exception as e:
            code = 400
            res['code'] = code
            res['result']['res'] = "failed"
            res['result']['msg'] = e.message
        return res, code

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location='json')
        parser.add_argument('domain', type=str, location='json')

        args = parser.parse_args()
        env = args.env
        ip = DNS_ENV.get(env)
        domain = args.domain

        try:
            dns_api = NamedManagerApi()
            message = dns_api.named_dns_domain_add(domain_name=domain, domain_ip=ip)
            code = 200
            res['code'] = code
            res['result']['res'] = "success"
            res['result']['msg'] = message
        except Exception as e:
            code = 400
            res['code'] = code
            res['result']['res'] = "failed"
            res['result']['msg'] = e.message
        return res, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str, location='json')
        parser.add_argument('domain', type=str, location='json')

        args = parser.parse_args()
        env = args.env
        domain = args.domain

        try:
            dns_server = DnsConfig.singleton()
            del_response = dns_server.delete(domain_name=domain)
            reload_response = dns_server.reload()
            code = 200
            res['code'] = code
            res['result']['res'] = "success"
            res['result']['msg'] = del_response['error']
        except Exception as e:
            code = 400
            res['code'] = code
            res['result']['res'] = "failed"
            res['result']['msg'] = e.message
        return res, code

dns_set_api.add_resource(DnServerSet, '/dns_set')
#dns_set_api.add_resource(DnServerSet, '/dns_query')
#dns_set_api.add_resource(DnServerSet, '/dns_delete')

