import threading
import traceback

from testsuite import test_suite
import plogger
from enumeration import PDecoratorType


__author__ = 'karl.gong'


def take_screen_shot():
    active_browser = threading.currentThread().get_property("browser")
    # todo: support capturing multiple browsers

    if active_browser is not None:
        current_thread = threading.currentThread()
        test_class_full_name = current_thread.get_property("test_class")
        test_case_name = current_thread.get_property("test_case")
        test_case_fixture = current_thread.get_property("test_case_fixture")
        test_case_result = test_suite.get_test_class(test_class_full_name).get_test_case(test_case_name)
        # todo: directly get test_case_fixture, put test_case_fixture to the thread property


        # todo: Dismiss alert if it is present, so the alert will not block screen capture.

        try:
            screen_shot = active_browser.get_screenshot_as_png()
        except Exception as e:
            plogger.warn("Failed to take the screenshot: \n%s\n%s" % (e.message, traceback.format_exc()))
            return

        if test_case_fixture == PDecoratorType.Test:
            test_case_result.test.screen_shot = screen_shot
        elif test_case_fixture == PDecoratorType.BeforeMethod:
            test_case_result.before_method.screen_shot = screen_shot
        elif test_case_fixture == PDecoratorType.AfterMethod:
            test_case_result.after_method.screen_shot = screen_shot

    else:
        pass # todo: take screen shot for desktop