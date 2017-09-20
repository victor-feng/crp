#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import subprocess
def delete():
    print sys.argv
    domain = sys.argv[1]
    print domain
    filepath = "/usr/local/nginx/conf/servers_systoon/" + domain
    if os.path.exists(filepath):
        print "will delete %s" % filepath
    else:
        return "%s already deleted" % filepath
    subprocess.Popen('rm -fr %s' %  filepath, shell=True, stdout=subprocess.PIPE)
    subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)
delete()
