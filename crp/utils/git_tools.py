# -*- coding: utf-8 -*-



import os
from crp.log import Log
from config import APP_ENV, configs
from crp.utils.aio import exec_cmd


UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER
GIT_USER = configs[APP_ENV].GIT_USER
GIT_PASSWORD = configs[APP_ENV].GIT_PASSWORD


def deal_git_url(git_url):
    if  git_url.startswith("http"):
        git_url = git_url.strip().split("//")[1]
    elif git_url.startswith("git"):
        git_url = git_url.strip().split("@")[1].replace(":", "/")
    else:
        raise Exception("git url format error,url is {git_url}".format(git_url=git_url))
    return git_url


def write_build_log(context,project_name,env):
    build_log_path = os.path.exists(UPLOAD_FOLDER, "build_log")
    if not build_log_path:
        os.makedirs(build_log_path)
    file_name1 = "{project_name}_{env}_1".format(project_name=project_name,env=env)
    file_name2 = "{project_name}_{env}_2".format(project_name=project_name, env=env)
    file_name3 = "{project_name}_{env}_3".format(project_name=project_name, env=env)
    build_log_file1 = os.path.join(build_log_path,file_name1)
    build_log_file2 = os.path.join(build_log_path,file_name2)
    build_log_file3 = os.path.join(build_log_path, file_name3)
    if os.path.exists(build_log_file1):
        os.rename(build_log_file1,build_log_file2)
    if os.path.exists(build_log_file2):
        os.rename(build_log_file1,build_log_file3)
    with open(build_log_file1,"wb") as f:
        f.write(context)

def git_code_to_war(git_url,branch,project_name,pom_path,env,language_env):
    err_msg = None
    out_context = ""
    try:
        if language_env == "java":
            git_url = deal_git_url(git_url)
            repo_path = os.path.join(UPLOAD_FOLDER,"repo")
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            git_http_url = "http://{git_user}:{git_password}@{git_url}".format(git_user=GIT_USER,git_password=GIT_PASSWORD,git_url=git_url)
            project_path = os.path.join(repo_path,project_name)
            if os.path.exists(project_path):
                git_pull_cmd = "cd {project_path} && git pull origin {branch}".format(project_path=project_path,branch=branch)
                stdout = exec_cmd(git_pull_cmd)
            else:
                git_clone_cmd = "git clone -b {branch} {git_http_url}".format(branch=branch, git_http_url=git_http_url)
                stdout = exec_cmd(git_clone_cmd)
            out_context = out_context + '\n' + stdout
            if "error" in stdout.lower():
                err_msg = "git clone or pull error"
                return err_msg
            pom_path = os.path.join(project_path,pom_path)
            mvn_to_war_cmd = "mvn -B -f {pom_path} clean package -U -Dmaven.test.skip=true".format(pom_path=pom_path)
            stdout = exec_cmd(mvn_to_war_cmd)
            out_context = out_context + '\n' + stdout
            if "error" in stdout.lower():
                err_msg = "maven build war error"
                return err_msg
            base_war_name = "{project_name}.war".format(project_name=project_name)
            remote_war_name = "{project_name}_{env}.war".format(project_name=project_name,env=env)
            base_war = os.path.join(os.path.join(project_name,"target"),base_war_name)
            project_war_path = os.path.join(os.path.join(UPLOAD_FOLDER, "war"), project_name)
            if not project_war_path:
                os.makedirs(project_war_path)
            remote_war = os.path.join(project_war_path,remote_war_name)
            os.rename(base_war,remote_war)
    except Exception as e:
        err_msg = "Git code to war error {e}".format(e=str(e))
        out_context = out_context + '\n' + err_msg
        Log.logger.error(err_msg)
    write_build_log(out_context, project_name, env)
    return  err_msg