# -*- coding: utf-8 -*-
import threading
import subprocess
import os
import time
import json
import re
from crp.log import Log
from config import APP_ENV, configs

UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER
SCRIPTPATH = configs[APP_ENV].SCRIPTPATH
HARBOR_URL = configs[APP_ENV].HARBOR_URL


mysql_conf_temp="""
    <Resource name="jdbc/{{prdatasource}}_w"
                type="javax.sql.DataSource"
                driverClassName="com.mysql.jdbc.Driver"
                url="jdbc:mysql://{{mysqlIP_master}}/{{prdata}}?useUnicode=true&amp;characterEncoding=UTF-8&amp;allowMultiQueries=true"
                username="{{mysqlUser}}"
                password="{{mysqlPass}}"
                initialSize="2"
                minIdle="2"
                maxIdle="5"
                maxWait="4000"
                maxActive="10"
                removeAbandoned="true"
                removeAbandonedTimeout="180"
                logAbandoned="true"
                testWhileIdle="true"
                testOnBorrow="true"
                testOnReturn="false"
                validationQuery="SELECT 1"
                validationInterval="30000"
                timeBetweenEvictionRunsMillis="30000"
                factory="org.apache.tomcat.jdbc.pool.DataSourceFactory" />

    <Resource name="jdbc/{{prdatasource}}_r"
                type="javax.sql.DataSource"
                driverClassName="com.mysql.jdbc.Driver"
                url="jdbc:mysql://{{mysqlIP_slave}}/{{prdata}}?useUnicode=true&amp;characterEncoding=UTF-8&amp;allowMultiQueries=true"
                username="{{mysqlUser}}"
                password="{{mysqlPass}}"
                initialSize="2"
                minIdle="2"
                maxIdle="5"
                maxWait="4000"
                maxActive="10"
                removeAbandoned="true"
                removeAbandonedTimeout="180"
                logAbandoned="true"
                testWhileIdle="true"
                testOnBorrow="true"
                testOnReturn="false"
                validationQuery="SELECT 1"
                validationInterval="30000"
                timeBetweenEvictionRunsMillis="30000"
                factory="org.apache.tomcat.jdbc.pool.DataSourceFactory" />
"""

mycat_conf_temp = """
    <Resource name="jdbc/{{prmycatsource}}"
                     type="javax.sql.DataSource"
                     driverClassName="com.mysql.jdbc.Driver"
                     url="jdbc:mysql://{{mycatIP}}/{{prmycatdata}}?useUnicode=true&amp;characterEncoding=UTF-8&amp;allowMultiQueries=true"
                     username="{{mycatUser}}"
                     password="{{mycatPass}}"
                     initialSize="2"
                     minIdle="10"
                     maxIdle="10"
                     maxWait="4000"
                     maxActive="10"
                     removeAbandoned="true"
                     removeAbandonedTimeout="180"
                     logAbandoned="true"
                     testWhileIdle="true"
                     testOnBorrow="true"
                     testOnReturn="false"
                     validationQuery="SELECT 1"
                     validationInterval="30000"
                     timeBetweenEvictionRunsMillis="30000"
                     factory="org.apache.tomcat.jdbc.pool.DataSourceFactory" />
"""

start_tomcat_str="""
#!/bin/bash
cat /etc/hosts
ip=`ifconfig|grep 'inet addr:'|grep -v '127.0.0.1' |cut -d: -f2|awk '{ print $1}'`
hostname=`hostname`
echo "127.0.0.1" $hostname >>/etc/hosts
cat /etc/hosts
echo "--------------------"
service sshd start
exec ${CATALINA_HOME}/bin/catalina.sh run
"""

def replace_file_text(base_path,remote_path,old_text,new_text):
    with open(base_path,'r') as f:
        res=f.read()
    res=res.replace(old_text,new_text)
    with open(remote_path, 'a+') as f:
        f.truncate()
        f.write(res)

def exec_cmd(cmd):
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout = p.stdout.read()
    return stdout

def deal_templates_xml(database_config,project_name,base_context_path,remote_context_path,base_server_path, remote_server_path):
    err_msg = None
    try:
        base_path = ''
        remote_path = ''
        if database_config:
            database_config = json.loads(database_config)
            conf_text = ""
            mysql_info_list = database_config.get("mysql")
            if mysql_info_list:
                for mysql_info in mysql_info_list:
                    mysql_conf_text = mysql_conf_temp
                    for k, v in mysql_info.items():
                        key_word = re.sub(r'([\d]+)','',k)
                        mysql_conf_text=mysql_conf_text.replace("{{%s}}"% key_word,v)
                    conf_text = conf_text + "\n" + mysql_conf_text
            mycat_info_list = database_config.get("mycat")
            if mycat_info_list:
                for mycat_info in mycat_info_list:
                    mycat_conf_text = mycat_conf_temp
                    for k, v in mycat_info.items():
                        key_word = re.sub(r'([\d]+)', '', k)
                        mycat_conf_text = mycat_conf_text.replace("{{%s}}" % key_word, v)
                    conf_text = conf_text + "\n" + mycat_conf_text
        replace_file_text(base_context_path,remote_context_path,"UOP",conf_text)
        replace_file_text(base_server_path, remote_server_path, "{{hosts}}", project_name)
    except Exception as e:
        err_msg = "deal templates xml error {e}".format(e=str(e))
    return  err_msg


def create_docker_file(project_name):
    err_msg = None
    try:
        dk_dir = os.path.join(os.path.join(UPLOAD_FOLDER, "war"), project_name)
        dk_file_path = os.path.join(dk_dir,"Dockerfile")
        start_tomcat_path = os.path.join(dk_dir,"starttomcat.sh")
        with open(start_tomcat_path, "wb+") as f:
            f.write("{start_tomcat_str}\n".format(start_tomcat_str=start_tomcat_str))
        with open(dk_file_path, "wb+") as f:
            f.write("FROM reg1.syswin.com/base/os69-tomcat7:v0.1\n")
            f.write("\n")
            f.write("COPY ./server.xml /home/java/tomcat7_8081/conf/server.xml\n")
            f.write("COPY ./context.xml  /home/java/tomcat7_8081/conf/context.xml\n")
            f.write("COPY ./{project_name} /home/webapp/{project_name}\n".format(project_name=project_name))
            f.write('''ENTRYPOINT ["sh","/home/java/tomcat7_8081/bin/starttomcat.sh"]\n''')
    except Exception as e:
        err_msg = str(e)
    return  err_msg




def make_docker_image(database_config,project_name,env):
    err_msg = None
    try:
        dk_dir = os.path.join(os.path.join(UPLOAD_FOLDER,"war"),project_name)
        remote_context_path = os.path.join(dk_dir,"context.xml")
        remote_server_path = os.path.join(dk_dir,"server.xml")
        base_context_path = os.path.join(SCRIPTPATH,"roles/wardeploy/templates/base_context_template.xml")
        base_server_path = os.path.join(SCRIPTPATH, "roles/wardeploy/templates/server_template.xml")
        err_msg=deal_templates_xml(database_config,project_name,base_context_path,remote_context_path,base_server_path, remote_server_path)
        if not err_msg:
            unzip_cmd = "unzip -oq {dk_dir}/{project_name}_{env}.war -d {dk_dir}/{project_name}".format(dk_dir=dk_dir,project_name=project_name,env=env)
            err_msg = exec_cmd(unzip_cmd)
            if not err_msg:
                err_msg = create_docker_file(project_name)
                if not err_msg:
                    image_url = "{harbor_url}/uop/{project_name}:v-1.0.1".format(harbor_url=HARBOR_URL,project_name=project_name.lower())
                    build_image_cmd = "cd {dk_dir};docker build -t {image_harbor_url} .".format(dk_dir=dk_dir,image_url=image_url)
                    stdout = exec_cmd(build_image_cmd)
                    if "Successfully" in stdout:
                        push_image_cmd = "docker push {image_url}".format(image_url)
                        stdout = exec_cmd(push_image_cmd)
                        if "Digest" not in stdout:
                            err_msg = stdout
                    else:
                        err_msg = stdout
    except Exception as e:
        err_msg = str(e)
    return err_msg