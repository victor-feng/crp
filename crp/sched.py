# -*- coding: utf-8 -*-
from threading import Timer, Thread
from time import sleep
import datetime
import requests


# 全局线程列表
threads = []
# 全局唯一线程ID
global_thread_id = 0


# 线程退出方法
def thread_exit(thread_id):
    for thread in threads:
        if thread.thread_id == thread_id:
            thread.stop()


# class Scheduler(Thread): 定时任务线程类
class Scheduler(Thread):
    def __init__(self, sleep_time, time_out, function, *args, **kwargs):
        self.sleep_time = sleep_time
        self.timeout = time_out
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._t = None
        self.thread_id = 0
        self.delta_time = 0
        self.exit_flag = False

    def start(self):
        if self._t is None:
            # 生成线程ID
            global global_thread_id
            global_thread_id += 1
            self.thread_id = global_thread_id
            print "Thread id " + self.thread_id.__str__() + " start."
            # 启动线程定时器
            self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
            self._t.start()
            # 添加线程到线程列表
            threads.append(self)
        else:
            raise Exception("this timer is already running")
        return

    def _run(self, *args, **kwargs):
        # 执行定时任务
        if self.thread_id is not None:
            self.function(self.thread_id, *args, **kwargs)
        else:
            self.function(*args, **kwargs)
        if self.exit_flag is True:
            # 任务主动触发线程退出
            return
        # 超时退出
        self.delta_time += self.sleep_time
        if self.delta_time >= self.timeout:
            print "Thread id " + self.thread_id.__str__() + " timeout."
            self.stop()
            return
        # 循环间隔时间启动线程定时器
        self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
        self._t.start()
        return

    def stop(self):
        if self._t is not None:
            # 终止线程定时器
            self._t.cancel()
            self._t = None
            # 标记线程退出标记
            self.exit_flag = True
            print "Thread id " + self.thread_id.__str__() + " exit."
            # 从线程列表中删除已停止线程
            threads.remove(self)
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
def query_modify_db(thread_id=None, args1=None, args2=None):
    """ 需要定时处理的任务函数 """
    handler = "Thread id " + thread_id.__str__() + " query_db"
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
                # TODO(thread exit): 执行成功停止定时任务退出线程
                thread_exit(thread_id)
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
        # TODO(thread exit): 抛出异常停止定时任务退出线程
        thread_exit(thread_id)


# # TODO(scheduler): 定时任务示例代码，实例化Scheduler并start定时任务，需要添加到API处理方法中
# scheduler = Scheduler(SLEEP_TIME, TIMEOUT, query_modify_db, "testargs1", "testargs2")
# scheduler.start()
