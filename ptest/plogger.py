import logging
import sys
from datetime import datetime

from . import config


class PConsole:
    def __init__(self, out):
        self.out = out

    def write(self, msg):
        self.out.write(str(msg))

    def write_line(self, msg):
        self.out.write(str(msg) + "\n")


pconsole = PConsole(sys.stdout)
pconsole_err = PConsole(sys.stderr)


class PReporter:
    def __init__(self):
        pass

    def debug(self, msg, screenshot=False):
        self.__log(logging.DEBUG, msg, screenshot)

    def info(self, msg, screenshot=False):
        self.__log(logging.INFO, msg, screenshot)

    def warn(self, msg, screenshot=False):
        self.__log(logging.WARN, msg, screenshot)

    def error(self, msg, screenshot=False):
        self.__log(logging.ERROR, msg, screenshot)

    def critical(self, msg, screenshot=False):
        self.__log(logging.CRITICAL, msg, screenshot)

    def __log(self, level, msg, screenshot):
        from . import test_executor, screen_capturer

        try:
            running_test_fixture = test_executor.current_executor().get_property("running_test_fixture")
        except AttributeError as e:
            pconsole.write_line("[%s] %s" % (logging.getLevelName(level), msg))
        else:
            log = {"time": str(datetime.now()), "level": logging.getLevelName(level).lower(), "message": str(msg)}
            if screenshot and not config.get_option("disable_screenshot"):
                log["screenshots"] = screen_capturer.take_screenshots()

            running_test_fixture.logs.append(log)

            if config.get_option("verbose"):
                # output to pconsole
                message = "[%s] %s" % (running_test_fixture.full_name, msg)
                pconsole.write_line(message)


preporter = PReporter()
