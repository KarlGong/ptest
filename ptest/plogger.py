import logging
import sys
from . import config

__author__ = 'karl.gong'


class PConsole:
    def __init__(self, out):
        self.out = out

    def write(self, msg):
        self.out.write(msg)

    def write_line(self, msg):
        self.write(msg + "\n")


pconsole = PConsole(sys.stdout)


class PReporter:
    def __init__(self):
        pass

    def debug(self, msg):
        self.__log(logging.DEBUG, msg)

    def info(self, msg):
        self.__log(logging.INFO, msg)

    def warn(self, msg):
        self.__log(logging.WARN, msg)

    def error(self, msg):
        self.__log(logging.ERROR, msg)

    def critical(self, msg):
        self.__log(logging.CRITICAL, msg)

    def __log(self, level, msg):
        from . import testexecutor

        running_test_case_fixture = testexecutor.get_property("running_test_case_fixture")
        running_test_case_fixture.logs.append((logging.getLevelName(level).lower(), str(msg),))

        if config.get_option("verbose"):
            # output to pconsole
            message = "[%s] %s" % (running_test_case_fixture.full_name, msg)
            pconsole.write_line(message)


preporter = PReporter()
