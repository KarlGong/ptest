import logging
import threading


__author__ = 'karl.gong'

DEBUG = 10
INFO = 20
WARN = 30
ERROR = 40
CRITICAL = 50

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
    __log(DEBUG, msg)


def info(msg):
    __log(INFO, msg)


def warn(msg):
    __log(WARN, msg)


def error(msg):
    __log(ERROR, msg)


def critical(msg):
    __log(CRITICAL, msg)


def __log(level, msg):
    running_test_case_fixture = threading.currentThread().get_property("running_test_case_fixture")
    running_test_case_fixture.logs.append(msg)

    if pconsole_verbose:
        # output log to pconsole
        message = "[%s @%s] %s" % (
            running_test_case_fixture.test_case.full_name, running_test_case_fixture.fixture_type, msg)
        if level == DEBUG:
            pconsole.debug(message)
        elif level == INFO:
            pconsole.info(message)
        elif level == WARN:
            pconsole.warning(message)
        elif level == ERROR:
            pconsole.error(message)
        elif level == CRITICAL:
            pconsole.critical(message)