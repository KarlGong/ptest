import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List

from ptest.util import escape_filename

from . import config


class PConsole:
    def __init__(self, out):
        self.out = out

    def write(self, msg: str):
        self.out.write(str(msg))

    def write_line(self, msg: str):
        self.out.write(str(msg) + "\n")


pconsole = PConsole(sys.stdout)
pconsole_err = PConsole(sys.stderr)


class PReporter:
    def __init__(self):
        pass

    def debug(self, msg: str, screenshot: bool = False, images: List[bytes] = []):
        self.__log(logging.DEBUG, msg, screenshot, images)

    def info(self, msg: str, screenshot: bool = False, images: List[bytes] = []):
        self.__log(logging.INFO, msg, screenshot, images)

    def warn(self, msg: str, screenshot: bool = False, images: List[bytes] = []):
        self.__log(logging.WARN, msg, screenshot, images)

    def error(self, msg: str, screenshot: bool = False, images: List[bytes] = []):
        self.__log(logging.ERROR, msg, screenshot, images)

    def critical(self, msg: str, screenshot: bool = False, images: List[bytes] = []):
        self.__log(logging.CRITICAL, msg, screenshot, images)

    def __log(self, level: int, msg: str, screenshot: bool = False, images: List[bytes] = []):
        from . import test_executor, screen_capturer

        try:
            running_test_fixture = test_executor.current_executor().get_property("running_test_fixture")
        except AttributeError as e:
            pconsole.write_line("[%s] %s" % (logging.getLevelName(level), msg))
        else:
            log = {"time": str(datetime.now()), "level": logging.getLevelName(level).lower(), "message": str(msg)}
            log_hash_code = str(uuid.uuid4()).split("-")[0]
            path_prefix = "%s-%s" % (escape_filename(running_test_fixture.full_name), log_hash_code)
            if screenshot and not config.get_option("disable_screenshot"):
                log["screenshots"] = screen_capturer.take_screenshots(path_prefix)
            if images:
                image_dicts = []
                for index, image in enumerate(images):
                    image_dict = {
                        "path": "%s-image-%s.png" % (path_prefix, index + 1)
                    }
                    with open(os.path.join(config.get_option("temp"), image_dict["path"]), mode="wb") as f:
                        f.write(image)
                    image_dicts.append(image_dict)
                log["images"] = image_dicts

            running_test_fixture.logs.append(log)

            if config.get_option("verbose"):
                # output to pconsole
                message = "[%s] %s" % (running_test_fixture.full_name, msg)
                pconsole.write_line(message)


preporter = PReporter()
