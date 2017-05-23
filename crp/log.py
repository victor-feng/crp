# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler


# 默认LOG格式化字符串
_DEFAULT_LOG_NAME = 'CRP'
_DEFAULT_FORMATTER = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"


def logger_setting(app):
    log_name = app.config.get('LOG_NAME', _DEFAULT_LOG_NAME)
    log_filename = app.config.get('LOG_FILENAME', '/var/log/'+log_name+'.log')
    log_formatter_config = app.config.get('LOG_FORMATTER', _DEFAULT_FORMATTER)
    debug_config = app.config.get('DEBUG', False)
    testing_config = app.config.get('TESTING', False)
    warning_config = app.config.get('WARNING', True)

    # set log filename and rotating log file
    handler = RotatingFileHandler(log_filename, maxBytes=10000, backupCount=1)

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

    return handler


class Log(object):
    logger = None

    @staticmethod
    def set_logger(logger_to_set):
        Log.logger = logger_to_set

    @staticmethod
    def get_logger():
        if Log.logger is not None:
            return Log.logger
