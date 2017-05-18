# -*- coding: utf-8 -*-
from threading import Timer, Thread
from time import sleep
import datetime
import requests


threads = []
global_thread_id = 0


# class Scheduler(object):
class Scheduler(Thread):
    def __init__(self, sleep_time, time_out, function, *args, **kwargs):
        self.sleep_time = sleep_time
        self.timeout = time_out
        self.function = function
        self.thread_id = 0
        self.delta_time = 0
        self.args = args
        self.kwargs = kwargs
        self._t = None

    def start(self):
        if self._t is None:
            self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
            self._t.start()
            # 生成线程ID
            global global_thread_id
            global_thread_id += 1
            self.thread_id = global_thread_id
        else:
            raise Exception("this timer is already running")

    def _run(self, *args, **kwargs):
        if self.thread_id is not None:
            self.function(self.thread_id, *args, **kwargs)
        else:
            self.function(*args, **kwargs)
        # 超时退出
        self.delta_time += self.sleep_time
        if self.delta_time >= self.timeout:
            self.stop()
            return
        # 循环间隔时间定时
        self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
        self._t.start()

    def stop(self):
        if self._t is not None:
            self._t.cancel()
            self._t = None
            threads.remove(self)

    def run(self):
        self.start()


# 使用示例
null = "null"
url = "http://localhost:8000/api/user/users"
TIMEOUT = 10
SLEEPTIME = 5


# 示例用延时
def delay(handler):
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
    delta_time = delay("query_db")
    print "IM QUERYING A DB use " + delta_time.__str__() + " microseconds"
    print "args1: " + args1 + "; args2:" + args2
    try:
        """ TODO: Timer Handle """
        res = requests.get(url)
        ret = eval(res.content)
        res_list = ret['result']['res']
        for u in res_list:
            if u['email'] == "abc@edu.cn":
                req = {
                    "email": "modify" + u['email'],
                    "first_name": u['first_name'],
                    "last_name": u['last_name']
                }
                u['email'] = "modify@edu.cn"
                requests.post(url, data=req)
    except Exception as e:
        """ TODO: Error Handle """
        ret = {
            "code": 500,
            "result": {
                "res": res.status_code,
                "msg": "Error Msg"
            }
        }
        requests.post(url, data=ret)
        for thread in threads:
            if thread.thread_id == thread_id:
                threads.remove(thread)


# # 示例代码
# threads = []
#
# scheduler = Scheduler(1, 10, query_db)
# scheduler.start()
# # 添加线程到线程列表
# threads.append(scheduler)
# sleep(600)
# scheduler.stop()
# threads.remove(scheduler)
