# -*- coding: utf-8 -*-
from threading import Timer, Thread, Lock
from time import sleep
import datetime
import requests
from crp.log import Log


class TaskManager(object):
    # 全局任务列表
    tasks = []
    # 全局唯一任务ID
    global_task_id = 0
    # 全局锁
    global_mutex = None

    # 创建全局锁
    if global_mutex is None:
        global_mutex = Lock()

    def __init__(self):
        super(TaskManager, self).__init__()

    # 任务添加方法
    @staticmethod
    def task_start(sleep_time, time_out, function, *args, **kwargs):
        """ 生成任务ID，并添加任务线程到任务列表中
         :param sleep_time: 定时任务定时间隔时间，单位秒
         :param time_out: 定时任务超时时间，单位秒
         :param function: 定时任务函数体
         :param args: 参数透传
         :param kwargs: 参数透传
        """
        _has_task = False
        _task_id = 0
        task_thread = Scheduler(sleep_time, time_out, function, *args, **kwargs)
        # 锁定和释放全局锁
        with TaskManager.global_mutex:
            for task in TaskManager.tasks:
                if task.task_id == task_thread.task_id:
                    _has_task = True
            if _has_task is not True:
                TaskManager.global_task_id += 1
                _task_id = TaskManager.global_task_id
                TaskManager.tasks.append(task_thread)
        task_thread.start(_task_id)
        return _task_id

    # 任务退出方法
    @staticmethod
    def task_exit(task_id=0, task_thread=None):
        """ 从任务列表中删除已停止的任务线程
         :param task_id: 任务ID
         :param task_thread: 任务线程对象
        """
        with TaskManager.global_mutex:
            for task in TaskManager.tasks:
                if task_id is not 0 and task.task_id == task_id:
                    task.stop()
                    TaskManager.tasks.remove(task)
                    return
                if task is task_thread:
                    task_thread.stop()
                    TaskManager.tasks.remove(task_thread)
                    return


task_manager = TaskManager()


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

    def start(self, task_id):
        if self._t is None:
            self.task_id = task_id
            Log.logger.debug("Task id " + self.task_id.__str__() + " start.")
            # 启动任务定时器
            self._t = Timer(self.sleep_time, self._run, self.args, self.kwargs)
            self._t.start()
        else:
            raise Exception("this timer is already running")
        return

    def _run(self, *args, **kwargs):
        # 超时退出
        self.delta_time += self.sleep_time
        if self.delta_time >= self.timeout:
            Log.logger.debug("Task id " + self.task_id.__str__() + " timeout.")
            self.stop()
            return
        # 执行定时任务
        if self.task_id is not None:
            self.function(self.task_id, *args, **kwargs)
        else:
            self.function(*args, **kwargs)
        if self.exit_flag is True:
            # 任务主动触发任务线程退出
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
            Log.logger.debug("Task id " + self.task_id.__str__() + " exit.")
        return

    def run(self):
        self.start()


# 以下为使用示例
URL = "http://localhost:8000/api/user/users"
TIMEOUT = 10
SLEEP_TIME = 3


# 示例用延时方法
def delay(handler):
    """ 延时函数 """
    old = datetime.datetime.now()
    Log.logger.debug("delay start at " + old.__str__() + " by " + handler)
    for _ in range(10000):
        for j in range(500):
            i = 1
    now = datetime.datetime.now()
    Log.logger.debug("delay end at" + now.__str__() + " by " + handler)
    delta_time = (now - old).seconds*1000 + (now - old).microseconds/1000
    return delta_time


# 示例用功能函数
def query_modify_db(task_id=None, args1=None, args2=None):
    """ 需要定时处理的任务函数 """
    handler = "Task id " + task_id.__str__() + " query_db"
    delta_time = delay(handler)
    Log.logger.debug("IM QUERYING A DB use " + delta_time.__str__() + " microseconds" + " by " + handler)
    Log.logger.debug("Test args is args1: " + args1 + "; args2:" + args2 + " by " + handler)
    try:
        # TODO(handle): Timer Handle
        res = requests.get(URL)
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
                requests.post(URL + "/callback_success", data=req)
                # TODO(thread exit): 执行成功停止定时任务退出任务线程
                TaskManager.task_exit(task_id)
    except Exception as e:
        # TODO(error handle): Error Handle
        ret = {
            "code": 500,
            "result": {
                "res": res.status_code,
                "msg": "Error Msg"
            }
        }
        requests.post(URL + "/callback_exception", data=ret)
        # TODO(thread exit): 抛出异常停止定时任务退出任务线程
        TaskManager.task_exit(task_id)


# # TODO(scheduler): 定时任务示例代码，实例化Scheduler并start定时任务，需要添加到API处理方法中
# from crp.sched import *
#
# TaskManager.task_start(SLEEP_TIME, TIMEOUT, query_modify_db, "testargs1", "testargs2")
#
# Log.logger.debug("This is debug.")
