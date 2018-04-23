#!/usr/bin/env python
#coding:utf-8



import os,sys


#判断/data目录是否存在，不存在创建

if not os.path.exists("/data"):
    os.mkdir("/data")
#挂载卷
if len(sys.argv) == 2:
    cluster_type = sys.argv[1]
    #如果是mysql和mongodb必须修改/data目录的权限
    if cluster_type == "mysql":
        chown_cmd="chown -R mysql.mysql /data"
    elif cluster_type == "mongodb":
        chown_cmd="chown -R mongodb01:db /data"
    else:
        chown_cmd = None

    if os.path.exists("/dev/vdb"):
        os.system("mkfs.ext4 /dev/vdb")
    else:
        sys.exit()
    if  os.path.exists("/data") and not os.path.exists("/data1"):
        os.system("mv /data /data1")
        os.mkdir("/data")

    res=os.popen("cat /etc/fstab | grep '/dev/vdb' | wc -l").read().strip()

    if int(res) == 0:
        os.system("echo '/dev/vdb       /data         ext4    defaults,noatime,nodiratime,nobarrier   1 1' >> /etc/fstab")

    os.system("mount -a")

    os.system("cp -rp /data1/* /data")

    os.system("chmod 700 /data")

    if chown_cmd:
        os.system(chown_cmd)
#扩容卷
elif len(sys.argv) == 1:
    #卸载卷
    os.system("umount /data")
    #检查卷
    os.system("e2fsck -f /dev/vdb")
    #调整卷大小
    os.system("resize2fs /dev/vdb")
    #挂载卷
    os.system("mount /data")
    res = os.popen("cat /etc/fstab | grep '/dev/vdb' | wc -l").read().strip()
    #写入配置文件
    if int(res) == 0:
        os.system(
            "echo '/dev/vdb       /data         ext4    defaults,noatime,nodiratime,nobarrier   1 1' >> /etc/fstab")
    #修改目录权限
    os.system("chmod 700 /data")