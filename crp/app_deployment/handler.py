# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource
from crp.app_deployment import app_deploy_blueprint
from crp.app_deployment.errors import user_errors
from json import *
import requests
import json
import commands
import os

app_deploy_api = Api(app_deploy_blueprint, errors=user_errors)

#url = "http://172.28.11.111:8001/cmdb/api/"
#url = "http://cmdb-test.syswin.com/api/dep_result/"
url = "http://172.28.11.111:5001/api/dep_result/"

class AppDeploy(Resource):
    def post(self):
        code = 200
        msg = "success"

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('image_url', type=str)
            parser.add_argument('image_name', type=str)
            parser.add_argument('mysql', type=dict)
            args = parser.parse_args()

            deploy_id = args.deploy_id
            image_url = args.image_url
            image_name = args.image_name
            sql_ret = self._sql_exec(args)
            data = {}
            data["result"] = "failed"
            if sql_ret:
                data["result"] = "success"
            data_str = json.dumps(data)

            headers = {'Content-Type': 'application/json'}
            res = requests.put(url + deploy_id + "/" , data = data_str,headers = headers )
            if res.status_code != 200:
                code = 500
                msg = "uop server error"
            ddd = 999
        except Exception as e:
            code = 500
            msg = "internal server error"

        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }

        return res, code
    def _sql_exec(self,args):
        workdir = os.getcwd()
        password = args.mysql.get("password")
        ip = args.mysql.get("ip")
        port = args.mysql.get("port")
        database = args.mysql.get("database")
        user = args.mysql.get("user")
        sql = args.mysql.get("sql_script")

        file_object = open(workdir + '/sql.sh', "wb+")
        file_object.write("#!/bin/bash\n")
        file_object.write("TMP_PWD=$MYSQL_PWD\n")
        file_object.write("export MYSQL_PWD=" + password + "\n")
        file_object.write("mysql -u" + user + " -P" + port + " -e \"\n")
        file_object.write("use " + database + ";\n")
        file_object.write(sql + "\n")
        file_object.write("quit \"\n")
        file_object.write("export MYSQL_PWD=$TMP_PWD\n")
        file_object.write("exit;")
        file_object.close()

        file_object = open(workdir + '/myhosts', "wb+")
        file_object.write(ip + " ansible_ssh_pass=123456 ansible_ssh_user=root")
        file_object.close()

        (status, output) = commands.getstatusoutput(
            'ansible -i ' + workdir + '/myhosts ' + ip + ' -u root -m script -a ' + workdir + '/sql.sh')
        ret = output.find("ERROR")
        return True if ret == -1 else False


app_deploy_api.add_resource(AppDeploy, '/deploys')
