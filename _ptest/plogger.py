import logging
import threading

from testsuite import test_suite
from enumeration import PDecoratorType


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
    current_thread = threading.currentThread()
    test_class_full_name = current_thread.get_property("test_class")
    test_case_name = current_thread.get_property("test_case")
    test_case_fixture = current_thread.get_property("test_case_fixture")
    test_case_result = test_suite.get_test_class(test_class_full_name).get_test_case(test_case_name)

    # add nglog to testPool for reporting
    if test_case_fixture == PDecoratorType.Test:
        test_case_result.test.logs.append(msg)
    elif test_case_fixture == PDecoratorType.BeforeMethod:
        test_case_result.before_method.logs.append(msg)
    elif test_case_fixture == PDecoratorType.AfterMethod:
        test_case_result.after_method.logs.append(msg)

    if pconsole_verbose:
        # output nglog to pconsole
        message = "[%s.%s @%s] %s" % (test_class_full_name, test_case_name, test_case_fixture, msg)
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