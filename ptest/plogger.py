import logging
import sys

from . import config


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

        try:
            running_test_fixture = testexecutor.current_executor().get_property("running_test_fixture")
        except AttributeError:
            pconsole.write_line("[%s] %s" % (logging.getLevelName(level), msg))
        else:
            running_test_fixture.logs.append({"level": logging.getLevelName(level).lower(), "message": str(msg)})

            if config.get_option("verbose"):
                # output to pconsole
                message = "[%s] %s" % (running_test_fixture.full_name, msg)
                pconsole.write_line(message)


preporter = PReporter()
