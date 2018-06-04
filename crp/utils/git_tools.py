# -*- coding: utf-8 -*-
import os
import datetime
from crp.log import Log
from config import APP_ENV, configs
from crp.utils.aio import exec_cmd
from ftplib import FTP
from crp.utils import res_instance_push_callback
from crp.app_deployment.handler import _dep_detail_callback
ADD_LOG = configs[APP_ENV].ADD_LOG

pull_code_success = ADD_LOG.get("GIT_PACKAGE")[0]
clone_branch_success = ADD_LOG.get("GIT_PACKAGE")[1]
package_success = ADD_LOG.get("GIT_PACKAGE")[2]
pull_or_clone_error = ADD_LOG.get("GIT_PACKAGE")[3]
package_error = ADD_LOG.get("GIT_PACKAGE")[4]


UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER
GIT_USER = configs[APP_ENV].GIT_USER
GIT_PASSWORD = configs[APP_ENV].GIT_PASSWORD
FTP_USER = configs[APP_ENV].FTP_USER
FTP_PASSWORD = configs[APP_ENV].FTP_PASSWORD
FTP_HOST = configs[APP_ENV].FTP_HOST
FTP_DIR = configs[APP_ENV].FTP_DIR


def deal_git_url(git_url):
    git_dir=git_url.strip().split('/')[-1].split('.')[0]
    if  git_url.startswith("http"):
        git_url = git_url.strip().split("//")[1]
    elif git_url.startswith("git"):
        git_url = git_url.strip().split("@")[1].replace(":", "/")
    else:
        raise Exception("git url format error,url is {git_url}".format(git_url=git_url))
    return git_url,git_dir


def write_build_log(context,project_name,resource_name):
    build_log_path = os.path.join(os.path.join(UPLOAD_FOLDER, "build_log"),project_name)
    if not os.path.exists(build_log_path):
        os.makedirs(build_log_path)
    file_name1 = "{resource_name}_1".format(resource_name=resource_name)
    file_name2 = "{resource_name}_2".format(resource_name=resource_name)
    file_name3 = "{resource_name}_3".format(resource_name=resource_name)
    build_log_file1 = os.path.join(build_log_path,file_name1)
    build_log_file2 = os.path.join(build_log_path,file_name2)
    build_log_file3 = os.path.join(build_log_path, file_name3)
    if os.path.exists(build_log_file2):
        os.rename(build_log_file2,build_log_file3)
    if os.path.exists(build_log_file1):
        os.rename(build_log_file1,build_log_file2)
    with open(build_log_file1,"wb") as f:
        f.write(context)


def git_code_to_war(git_url,branch,project_name,pom_path,env,language_env,resource_name,deploy_id=None,deploy_type=None, set_flag=None, resource_id=None):
    err_msg = None
    out_context = ""
    war_url = None
    try:
        if set_flag in ["increase","reduce"]:
            resource_id = None
        req_dict = {"resource_id": resource_id}
        if language_env == "java":
            pom_paths = pom_path.split('/')
            git_url,git_dir = deal_git_url(git_url)
            repo_path = os.path.join(UPLOAD_FOLDER,"repo")
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            git_http_url = "http://{git_user}:{git_password}@{git_url}".format(git_user=GIT_USER,git_password=GIT_PASSWORD,git_url=git_url)
            project_path = os.path.join(repo_path,git_dir)
            if os.path.exists(project_path):
                git_pull_cmd = "cd {project_path} && git pull origin {branch}".format(project_path=project_path,branch=branch)
                stdout = exec_cmd(git_pull_cmd)
                # success
                if deploy_id:
                    _dep_detail_callback(deploy_id, deploy_type, set_flag, "更新代码成功")
                else:
                    res_instance_push_callback('', req_dict, 0, {}, {}, pull_code_success, set_flag)
            else:
                git_clone_cmd = "cd {repo_path} && git clone -b {branch} {git_http_url}".format(repo_path=repo_path,branch=branch, git_http_url=git_http_url)
                stdout = exec_cmd(git_clone_cmd)
                # success
                if deploy_id:
                    _dep_detail_callback(deploy_id, deploy_type, set_flag, "拉取代码成功")
                else:
                    res_instance_push_callback('', req_dict, 0, {}, {}, clone_branch_success, set_flag)
            out_context = out_context + '\n' + stdout
            if "error" in stdout.lower() or "fatal" in stdout.lower():
                err_msg = "git clone or pull error"
                if deploy_id:
                    _dep_detail_callback(deploy_id, deploy_type, set_flag, "代码获取失败 {err_msg}".format(err_msg=err_msg))
                else:
                    res_instance_push_callback('', req_dict, 0, {}, {}, pull_or_clone_error, set_flag)
                Log.logger.debug(out_context)
                write_build_log(out_context, project_name, resource_name)
                return err_msg,war_url
            pom_path = os.path.join(project_path,pom_path)
            mvn_to_war_cmd = "source /etc/profile && /usr/local/maven/bin/mvn -B -f {pom_path} clean package -U -Dmaven.test.skip=true".format(pom_path=pom_path)
            stdout = exec_cmd(mvn_to_war_cmd)

            # success
            if deploy_id:
                _dep_detail_callback(deploy_id, deploy_type, set_flag, "包构建成功")
            else:
                res_instance_push_callback('', req_dict, 0, {}, {}, package_success, set_flag)

            out_context = out_context + '\n' + stdout
            if "BUILD SUCCESS" not  in stdout:
                err_msg = "maven build war error"
                if deploy_id:
                    _dep_detail_callback(deploy_id, deploy_type, set_flag, "包构建失败 {err_msg}".format(err_msg=err_msg))
                else:
                    res_instance_push_callback('', req_dict, 0, {}, {}, package_error, set_flag)
                Log.logger.debug(out_context)
                write_build_log(out_context, project_name, resource_name)
                return err_msg,war_url
            war_name = "{project_name}.war".format(project_name=project_name)
            if len(pom_paths) > 1:
                pom_dir = '/'.join(pom_paths[:-1])
                base_war_dir = os.path.join(os.path.join(project_path, pom_dir), "target")
                base_war_name = get_war_file(base_war_dir) if get_war_file(base_war_dir) else war_name
                base_war = os.path.join(os.path.join(os.path.join(project_path, pom_dir), "target"),base_war_name)
            else:
                base_war_dir = os.path.join(project_path,"target")
                base_war_name = get_war_file(base_war_dir) if get_war_file(base_war_dir) else war_name
                base_war = os.path.join(os.path.join(project_path,"target"),base_war_name)
            err_msg,war_url = put_war_to_ftp(env, project_name, base_war,base_war_name)
    except Exception as e:
        err_msg = "Git code to war error {e}".format(e=str(e))
        out_context = out_context + '\n' + err_msg
        Log.logger.error(err_msg)
    Log.logger.debug(out_context)
    write_build_log(out_context,project_name, resource_name)
    return  err_msg,war_url


def put_war_to_ftp(env,project_name,base_war,base_war_name):
    err_msg = None
    war_url = None
    try:
        war_name = base_war_name
        tag = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        ftp_host = FTP_HOST[env]
        ftp_user = FTP_USER
        ftp_passwd = FTP_PASSWORD
        ftp = FTP(host=ftp_host, user=ftp_user, passwd=ftp_passwd)
        remote_dir = "{ftp_dir}/uop/{project_name}_{env}_{tag}".format(ftp_dir=FTP_DIR,env=env,project_name=project_name,tag=tag)
        ftp.mkd(remote_dir)
        remote_war = os.path.join(remote_dir,war_name)
        f = open(base_war, "rb")
        ftp.storbinary('STOR {remote_war}'.format(remote_war=remote_war), f, 1024)
        f.close()
        war_url = "http://{ftp_host}/uop/{project_name}_{env}_{tag}/{war_name}".format(ftp_host=ftp_host,env=env,project_name=project_name,tag=tag,war_name=war_name)
    except Exception as e:
        err_msg = "Put war to ftp server error {e}".format(e=str(e))
        Log.logger.error(err_msg)
    return  err_msg ,war_url


def get_war_file(path):
    war_file = None
    try:
        files = os.listdir(path)
        for file in files:
            if file.endswith(".war"):
                war_file = file
    except Exception as e:
        raise Exception("Get war file error {e}".format(e=str(e)))
    return war_file



