import ctypes
import time
from datetime import datetime
import threading
import traceback

from .plistener import test_listeners
from . import screencapturer
from .enumeration import TestCaseStatus, TestFixtureStatus, PopStatus
from .plogger import pconsole, preporter
from .testsuite import test_suite, NoTestUnitAvailableForThisThread, BeforeClass, AfterClass, BeforeGroup, \
    AfterGroup, TestCase, BeforeMethod, BeforeSuite, AfterSuite

__author__ = 'karl.gong'


class TestFixtureExecutor(threading.Thread):
    def __init__(self, test_fixture):
        threading.Thread.__init__(self)
        self.test_fixture = test_fixture
        self.__properties = {}
        self.setDaemon(True)

    def run(self):
        self.update_properties(running_test_fixture=self.test_fixture)
        try:
            if self.test_fixture.arguments_count == 1:
                self.test_fixture.test_fixture_ref.__call__()
            elif self.test_fixture.arguments_count == 2:
                self.test_fixture.test_fixture_ref.__call__(self.test_fixture.context)
        except Exception as e:
            self.test_fixture.status = TestFixtureStatus.FAILED
            self.test_fixture.failure_message = "\n".join([str(arg) for arg in e.args])
            self.test_fixture.failure_type = e.__class__.__name__
            self.test_fixture.stack_trace = traceback.format_exc()
            preporter.error("Failed with following message:\n%s" % self.test_fixture.stack_trace)
            screencapturer.take_screenshot()
        else:
            self.test_fixture.status = TestFixtureStatus.PASSED
        self.clear_properties()

    def update_properties(self, **kwargs):
        self.__properties.update(kwargs)

    def clear_properties(self):
        self.__properties.clear()

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None


class TestExecutor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__properties = {}

    def run(self):
        while True:
            try:
                test_unit = test_suite.pop_test_unit()
            except NoTestUnitAvailableForThisThread:
                break

            if test_unit is None:
                time.sleep(1)
                continue

            if isinstance(test_unit, TestCase):
                test_case = test_unit
                test_listeners.on_test_case_start(test_case)
                test_case.start_time = datetime.now()

                before_method = test_case.before_method
                failed_setup_fixture = test_case.get_failed_setup_fixture()
                if not failed_setup_fixture:
                    before_method.run()
                else:
                    before_method.skip(failed_setup_fixture)

                test = test_case.test
                failed_setup_fixture = test_case.get_failed_setup_fixture()
                if not failed_setup_fixture:
                    test.run()
                else:
                    test.skip(failed_setup_fixture)

                logger_filler = "-" * (100 - len(test_case.full_name) - 6)
                if test_case.status == TestCaseStatus.PASSED:
                    pconsole.write_line("%s%s|PASS|" % (test_case.full_name, logger_filler))
                elif test_case.status == TestCaseStatus.FAILED:
                    pconsole.write_line("%s%s|FAIL|" % (test_case.full_name, logger_filler))
                elif test_case.status == TestCaseStatus.SKIPPED:
                    pconsole.write_line("%s%s|SKIP|" % (test_case.full_name, logger_filler))

                after_method = test_case.after_method
                failed_setup_fixture = test_case.get_failed_setup_fixture()
                if not failed_setup_fixture or (
                    isinstance(failed_setup_fixture, BeforeMethod) and after_method.always_run):
                    after_method.run()
                else:
                    after_method.skip(failed_setup_fixture)

                test_case.end_time = datetime.now()
                test_case.pop_status = PopStatus.FINISHED
                test_listeners.on_test_case_finish(test_case)

            elif isinstance(test_unit, BeforeSuite):
                test_listeners.on_test_suite_start(test_unit.test_suite)
                test_unit.test_suite.start_time = datetime.now()
                test_unit.run()

            elif isinstance(test_unit, AfterSuite):
                failed_setup_fixture = test_unit.test_suite.get_failed_setup_fixture()
                if not failed_setup_fixture or (isinstance(failed_setup_fixture, BeforeSuite) and test_unit.always_run):
                    test_unit.run()
                else:
                    test_unit.skip(failed_setup_fixture)
                test_unit.test_suite.end_time = datetime.now()
                test_listeners.on_test_suite_finish(test_unit.test_suite)

            elif isinstance(test_unit, BeforeClass):
                test_listeners.on_test_class_start(test_unit.test_class)
                test_unit.test_class.start_time = datetime.now()
                failed_setup_fixture = test_unit.test_class.get_failed_setup_fixture()
                if not failed_setup_fixture:
                    test_unit.run()
                else:
                    test_unit.skip(failed_setup_fixture)

            elif isinstance(test_unit, AfterClass):
                failed_setup_fixture = test_unit.test_class.get_failed_setup_fixture()
                if not failed_setup_fixture or (isinstance(failed_setup_fixture, BeforeClass) and test_unit.always_run):
                    test_unit.run()
                else:
                    test_unit.skip(failed_setup_fixture)
                test_unit.test_class.end_time = datetime.now()
                test_listeners.on_test_class_finish(test_unit.test_class)

            elif isinstance(test_unit, BeforeGroup):
                test_listeners.on_test_group_start(test_unit.test_group)
                test_unit.test_group.start_time = datetime.now()
                failed_setup_fixture = test_unit.test_group.get_failed_setup_fixture()
                if not failed_setup_fixture:
                    test_unit.run()
                else:
                    test_unit.skip(failed_setup_fixture)

            elif isinstance(test_unit, AfterGroup):
                failed_setup_fixture = test_unit.test_group.get_failed_setup_fixture()
                if not failed_setup_fixture or (isinstance(failed_setup_fixture, BeforeGroup) and test_unit.always_run):
                    test_unit.run()
                else:
                    test_unit.skip(failed_setup_fixture)
                test_unit.test_group.end_time = datetime.now()
                test_listeners.on_test_group_finish(test_unit.test_group)

    def update_properties(self, **kwargs):
        self.__properties.update(kwargs)

    def clear_properties(self):
        self.__properties.clear()

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None


def update_properties(**kwargs):
    threading.currentThread().update_properties(**kwargs)


def clear_properties():
    threading.current_thread().clear_properties()


def get_property(key):
    return threading.currentThread().get_property(key)


def get_name():
    return threading.currentThread().getName()


def kill_thread(thread):
    """Kill a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
