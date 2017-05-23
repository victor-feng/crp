# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler


# 默认LOG模块名称
_DEFAULT_LOG_NAME = 'CRP'
# 默认LOG文件滚动最大长度，单位字节
_DEFAULT_LOG_ROTATING_MAX = 1000000
# 默认LOG文件滚动个数
_DEFAULT_LOG_ROTATING_BACKUP_COUNT = 4
# 默认LOG格式化字符串
_DEFAULT_FORMATTER = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"


def logger_setting(app):
    log_name = app.config.get('LOG_NAME', _DEFAULT_LOG_NAME)
    log_filename = app.config.get('LOG_FILENAME', '/var/log/'+log_name+'.log')
    log_rotating_max = app.config.get('LOG_ROTATING_MAX', _DEFAULT_LOG_ROTATING_MAX)
    log_rotating_backup_count = app.config.get('LOG_ROTATING_BACKUP_COUNT', _DEFAULT_LOG_ROTATING_BACKUP_COUNT)
    log_formatter_config = app.config.get('LOG_FORMATTER', _DEFAULT_FORMATTER)
    debug_config = app.config.get('DEBUG', False)
    testing_config = app.config.get('TESTING', False)
    warning_config = app.config.get('WARNING', True)

    # set log filename and rotating log file
    handler = RotatingFileHandler(log_filename, maxBytes=log_rotating_max, backupCount=log_rotating_backup_count)

    # set logging level
    if debug_config is True:
        handler.setLevel(logging.DEBUG)
    elif testing_config is True:
        handler.setLevel(logging.INFO)
    elif warning_config is True:
        handler.setLevel(logging.WARNING)
    else:
        handler.setLevel(logging.ERROR)

    # set logging formatter
    formatter = logging.Formatter(log_formatter_config)
    handler.setFormatter(formatter)

    # set logger name
    app.logger_name = log_name

    # set flask app.logger handler
    app.logger.addHandler(handler)

    # set Log logger
    Log.logger = app.logger


class Log(object):
    flask_app_logger = None

    @property
    def logger(self):
        if Log.flask_app_logger is not None:
            return Log.flask_app_logger

    @logger.setter
    def logger(self, value):
        if value is not None:
            Log.flask_app_logger = value

    @staticmethod
    def set_logger(logger_to_set):
        Log.flask_app_logger = logger_to_set

    @staticmethod
    def get_logger():
        if Log.flask_app_logger is not None:
            return Log.flask_app_logger
