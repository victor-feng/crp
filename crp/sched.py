# -*- coding: utf-8 -*-
from threading import Timer, Thread, Lock
from time import sleep
import datetime
import requests


# 全局任务列表
tasks = []
# 全局唯一任务ID
global_task_id = 0
# 创建全局锁
global_mutex = Lock()


# 任务退出方法
def task_exit(task_id):
    for task in tasks:
        if task.task_id == task_id:
            task.stop()


# class Scheduler(Thread): 定时任务类，每一个任务起一个线程单独处理
class Scheduler(Thread):
    def __init__(self, sleep_time, time_out, function, *args, **kwargs):
        self.sleep_time = sleep_time
        self.timeout = time_out
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._t = None
        self.task_id = 0
        self.delta_time = 0
        self.exit_flag = False

    def start(self):
        if self._t is None:
            # 生成任务ID，全局加锁
            global global_mutex
            with global_mutex:
                # 锁定全局锁
                # mutex.acquire()
                global global_task_id
                global_task_id += 1
                self.task_id = global_task_id
                # 释放全局锁
                # mutex.release()
            print "Task id " + self.task_id.__str__() + " start."
            # 启动任务定时器
            self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
            self._t.start()
            # 添加任务线程到任务列表中
            tasks.append(self)
        else:
            raise Exception("this timer is already running")
        return

    def _run(self, *args, **kwargs):
        # 执行定时任务
        if self.task_id is not None:
            self.function(self.task_id, *args, **kwargs)
        else:
            self.function(*args, **kwargs)
        if self.exit_flag is True:
            # 任务主动触发任务线程退出
            return
        # 超时退出
        self.delta_time += self.sleep_time
        if self.delta_time >= self.timeout:
            print "Task id " + self.task_id.__str__() + " timeout."
            self.stop()
            return
        # 循环间隔时间启动任务线程定时器
        self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
        self._t.start()
        return

    def stop(self):
        if self._t is not None:
            # 终止任务线程定时器
            self._t.cancel()
            self._t = None
            # 标记任务线程退出标记
            self.exit_flag = True
            print "Task id " + self.task_id.__str__() + " exit."
            # 从任务列表中删除已停止的任务线程
            tasks.remove(self)
        return

    def run(self):
        self.start()


# 以下为使用示例
url = "http://localhost:8000/api/user/users"
TIMEOUT = 10
SLEEP_TIME = 5


# 示例用延时方法
def delay(handler):
    """ 延时函数 """
    old = datetime.datetime.now()
    print "delay start at " + old.__str__() + " by " + handler
    for _ in range(10000):
        for j in range(500):
            i = 1
    now = datetime.datetime.now()
    print "delay end at" + now.__str__() + " by " + handler
    delta_time = (now - old).seconds*1000 + (now - old).microseconds/1000
    return delta_time


# 示例用功能函数
def query_modify_db(task_id=None, args1=None, args2=None):
    """ 需要定时处理的任务函数 """
    handler = "Task id " + task_id.__str__() + " query_db"
    delta_time = delay(handler)
    print "IM QUERYING A DB use " + delta_time.__str__() + " microseconds" + " by " + handler
    print "Test args is args1: " + args1 + "; args2:" + args2 + " by " + handler
    try:
        # TODO(handle): Timer Handle
        res = requests.get(url)
        ret = eval(res.content)
        res_list = ret['result']['res']
        for u in res_list:
            if u['email'] == "test@syswin.com":
                req = {
                    "email": "modify" + u['email'],
                    "first_name": u['first_name'],
                    "last_name": u['last_name']
                }
                u['email'] = "modify@edu.cn"
                requests.post(url + "/callback_success", data=req)
                # TODO(thread exit): 执行成功停止定时任务退出任务线程
                task_exit(task_id)
    except Exception as e:
        # TODO(error handle): Error Handle
        ret = {
            "code": 500,
            "result": {
                "res": res.status_code,
                "msg": "Error Msg"
            }
        }
        requests.post(url + "/callback_exception", data=ret)
        # TODO(thread exit): 抛出异常停止定时任务退出任务线程
        task_exit(task_id)


# # TODO(scheduler): 定时任务示例代码，实例化Scheduler并start定时任务，需要添加到API处理方法中
# scheduler = Scheduler(SLEEP_TIME, TIMEOUT, query_modify_db, "testargs1", "testargs2")
# scheduler.start()
