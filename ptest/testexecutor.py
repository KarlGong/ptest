from datetime import datetime
import threading
import traceback

import plistener
import plogger
import screencapturer
from enumeration import PDecoratorType, TestCaseStatus
from plogger import pconsole
from testsuite import test_suite, NoTestCaseAvailableForThisThread

__author__ = 'karl.gong'


class TestExecutor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__properties = {}

    def run(self):
        while True:
            try:
                test_case = test_suite.pop_test_case()
            except NoTestCaseAvailableForThisThread:
                break
            test_case_full_name = test_case.full_name
            logger_filler = "-" * (100 - len(test_case_full_name) - 6)

            before_method = test_case.before_method
            test = test_case.test
            after_method = test_case.after_method

            plistener.test_listener.on_test_case_start(test_case)
            test_case.start_time = datetime.now()
            is_before_method_failed = False
            # before method
            if before_method is not None:
                self.update_properties(running_test_case_fixture=before_method)
                before_method.start_time = datetime.now()
                try:
                    before_method.run()
                except Exception as e:
                    # before method failed
                    is_before_method_failed = True
                    plogger.error("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                    screencapturer.take_screen_shot()
                before_method.end_time = datetime.now()

            # test  case
            self.update_properties(running_test_case_fixture=test)
            test.start_time = datetime.now()
            if is_before_method_failed:
                # skip test case
                plogger.warn("@%s failed, so skipped." % PDecoratorType.BeforeMethod)
                pconsole.warning("%s%s|SKIP|" % (test_case_full_name, logger_filler))
                test_case.status = TestCaseStatus.SKIPPED
                test_case.skip_message = "@%s failed, so skipped." % PDecoratorType.BeforeMethod
            else:
                # run test case
                try:
                    test.run()
                    pconsole.info("%s%s|PASS|" % (test_case_full_name, logger_filler))
                    test_case.status = TestCaseStatus.PASSED
                except Exception as e:
                    plogger.error("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                    screencapturer.take_screen_shot()
                    pconsole.error("%s%s|FAIL|" % (test_case_full_name, logger_filler))
                    test_case.status = TestCaseStatus.FAILED
                    test_case.failure_message = e.message
                    test_case.failure_type = e.__class__.__name__
                    test_case.stack_trace = traceback.format_exc()
            test.end_time = datetime.now()

            # after method
            if after_method is not None:
                self.update_properties(running_test_case_fixture=after_method)
                after_method.start_time = datetime.now()
                if not is_before_method_failed or after_method.always_run:
                    # run after method
                    try:
                        after_method.run()
                    except Exception as e:
                        plogger.error("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                        screencapturer.take_screen_shot()
                else:
                    # skip after method
                    plogger.warn("@%s failed, so skipped." % PDecoratorType.BeforeMethod)
                after_method.end_time = datetime.now()
            test_case.end_time = datetime.now()
            plistener.test_listener.on_test_case_finish(test_case)

    def update_properties(self, **kwargs):
        self.__properties.update(kwargs)

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None


def update_properties(**kwargs):
    threading.currentThread().update_properties(**kwargs)


def get_property(key):
    return threading.currentThread().get_property(key)


def get_name():
    return threading.currentThread().getName()
