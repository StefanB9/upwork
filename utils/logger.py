import logging
import sys
import datetime as dt
import functools
import inspect

from pythonjsonlogger import jsonlogger

from utils.misc import mem_usage_bytes

log_extra_fields = {'ref_dt': None}
loggers = dict()


def get_logger(name="logger"):
    """Creates a logger that outputs JSON with special variables"""

    if name in loggers:
        return loggers[name]

    log = logging.getLogger(name)
    log.setLevel(logging.INFO)

    log_handler = logging.StreamHandler(stream=sys.stdout)
    formatter = LogFormatter()
    log_handler.setFormatter(formatter)
    log.addHandler(log_handler)

    loggers[name] = log
    return log


class LogFormatter(jsonlogger.JsonFormatter):

    def add_fields(self, log_record, record, message_dict):
        super(LogFormatter, self).add_fields(log_record, record, message_dict)

        log_record['log_type'] = 'application_log'
        log_record['@timestamp'] = dt.datetime.now(dt.timezone.utc).isoformat()

        for k, v in log_extra_fields.items():
            if v is not None:
                log_record[k] = f'{v}'

        log_record['description'] = log_record.pop('message', None)
        log_record['mem_used'] = mem_usage_bytes()
        log_record['severity'] = record.levelname.upper()
        log_record['class'] = ':'.join([record.module, record.funcName, str(record.lineno)])
        exc_info = log_record.pop('exc_info', None)

        if exc_info:
            log_record['stacktrace'] = exc_info
        if record.process:
            log_record['pid'] = record.process
        if record.threadName:
            log_record['thread'] = record.threadName


def log_fields(refs: dict):
    def log_fields_(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            res_args = resolve_args(f, *args, *kwargs)
            try:
                for k, ref in refs.items():
                    if ref in kwargs.keys():
                        log_extra_fields[k] = kwargs[ref]
                return f(*args, **kwargs)
            finally:
                for k, ref in refs.items():
                    log_extra_fields[k] = None
        return decorated_function
    return log_fields_


def resolve_args(f, *args, **kwargs):
    res = dict()

    func_desc = inspect.getfullargspec(f)

    for i in range(len(func_desc.args)):
        res[func_desc.args[i]] = args[i]

    for k, v in kwargs.items():
        res[k] = v

    return res
