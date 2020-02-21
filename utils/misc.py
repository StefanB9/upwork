import os
import psutil


def mem_usage_bytes():
    return psutil.Process(os.getpid()).memory_info().rss
