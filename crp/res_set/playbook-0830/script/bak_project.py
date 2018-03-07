#!/usr/bin/env python
#coding:utf-8



import os,sys

def copy_dir(project_name):
    base_path = "/home/webapp"
    project_dir_path = os.path.join(base_path,project_name)
    if os.path.exists(project_dir_path):
        cmd = "cp -a {project_name} {project_name}.bak".format(project_name=project_name)
        os.system(cmd)




if __name__ == "__main__":
    project_name = sys.argv[1]
    copy_dir(project_name)