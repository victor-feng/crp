# coding=utf8
class  BasePlugin(object):
    def __init__(self, version=None):
        self.version = version

    def push(self, *args, **kwargs):
        '''
        # 实现中间件的信息配置推送
        :return:
        '''
        raise NotImplementedError

    def info(self, *args, **kwargs):
        '''
        # 获取中间件配置信息
        :return:
        '''
        raise NotImplementedError

    def verify(self, *args, **kwargs):
        '''
        # 校验中间件配置是否成功
        :return:
        '''
        raise NotImplementedError

    def modify(self, *args, **kwargs):
        '''
        # 修改中间件配置
        :return:
        '''
        raise NotImplementedError

    def operation(self, *args, **kwargs):
        '''
        # 操作中间件的状态，重启，开关等
        :return:
        '''
        raise NotImplementedError