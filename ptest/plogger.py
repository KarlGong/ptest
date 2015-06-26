import logging
import threading


__author__ = 'karl.gong'


# pconsole config
pconsole = logging.getLogger("ptest")
pconsole.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")

# output to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
pconsole.addHandler(console_handler)

# set pconsole verbose
pconsole_verbose = False


def debug(msg):
    __log(logging.DEBUG, msg)


def info(msg):
    __log(logging.INFO, msg)


def warn(msg):
    __log(logging.WARN, msg)


warning = warn


def error(msg):
    __log(logging.ERROR, msg)


def critical(msg):
    __log(logging.CRITICAL, msg)


def __log(level, msg):
    running_test_case_fixture = threading.currentThread().get_property("running_test_case_fixture")
    running_test_case_fixture.logs.append((logging.getLevelName(level).lower(), str(msg),))

    if pconsole_verbose:
        # output log to pconsole
        message = "[%s] %s" % (running_test_case_fixture.full_name, msg)
        pconsole.log(level, message)