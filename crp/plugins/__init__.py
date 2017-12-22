# coding=utf8
from crp.plugins.Mongodb import MongodbCluster

__all__ = ["MiddlewarePlugins"]

class MiddlewarePlugins(object):
    def __init__(self):
        self.__plugin_factory = {
            "mongodb": Mongodb.MongodbCluster
        }
        pass

    def get_plugin(self, kind):
        return self.__plugin_factory.get(kind, None)


