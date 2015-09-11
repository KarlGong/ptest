import ctypes
from datetime import datetime
import threading
import traceback

from .plistener import test_listeners
from . import screencapturer
from .enumeration import PDecoratorType, TestCaseStatus, TestFixtureStatus
from .plogger import pconsole, preporter
from .testsuite import test_suite, NoTestFixtureAvailableForThisThread, BeforeClass, AfterClass, BeforeGroup, \
    AfterGroup, Test, BeforeMethod, AfterMethod

__author__ = 'karl.gong'


class TestFixtureExecutor(threading.Thread):
    def __init__(self, test_fixture):
        threading.Thread.__init__(self)
        self.test_fixture = test_fixture
        self.__properties = {}

    def run(self):
        self.test_fixture.status = TestFixtureStatus.RUNNING
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
                test_fixture = test_suite.pop_test_fixture()
            except NoTestFixtureAvailableForThisThread:
                break

            def warn_and_mark_skipped(pdecorator_type):
                preporter.warn("%s failed, so skipped." % pdecorator_type)
                test_fixture.skip_message = "%s failed, so skipped." % pdecorator_type
                test_fixture.status = TestFixtureStatus.SKIPPED

            self.update_properties(running_test_fixture=test_fixture)

            before_suite = test_fixture.test_suite.before_suite
            is_before_suite_failed = before_suite and before_suite.status == TestFixtureStatus.FAILED

            if isinstance(test_fixture, BeforeClass):
                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                else:
                    test_fixture.run()
                continue

            before_class = test_fixture.test_class.before_class
            is_before_class_failed = before_class and before_class.status == TestFixtureStatus.FAILED

            if isinstance(test_fixture, AfterClass):
                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed and not test_fixture.always_run:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                else:
                    test_fixture.run()
                continue

            if isinstance(test_fixture, BeforeGroup):
                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                else:
                    test_fixture.run()
                continue

            before_group = test_fixture.test_group.before_group
            is_before_group_failed = before_group and before_group.status == TestFixtureStatus.FAILED

            if isinstance(test_fixture, AfterGroup):
                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                elif is_before_group_failed and not test_fixture.always_run:
                    warn_and_mark_skipped(PDecoratorType.BeforeGroup)
                else:
                    test_fixture.run()
                continue

            if isinstance(test_fixture, BeforeMethod):
                test_listeners.on_test_case_start(test_fixture.test_case)
                test_fixture.test_case.start_time = datetime.now()

                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                elif is_before_group_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeGroup)
                else:
                    test_fixture.run()
                continue

            before_method = test_fixture.test_case.before_method
            is_before_method_failed = before_method and before_method.status == TestFixtureStatus.FAILED

            if isinstance(test_fixture, AfterMethod):
                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                elif is_before_group_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeGroup)
                elif is_before_method_failed and not test_fixture.always_run:
                    warn_and_mark_skipped(PDecoratorType.BeforeMethod)
                else:
                    test_fixture.run()

                test_fixture.test_case.end_time = datetime.now()
                test_listeners.on_test_case_finish(test_fixture.test_case)
                continue

            if isinstance(test_fixture, Test):
                if test_fixture.test_case.before_method is None:
                    test_listeners.on_test_case_start(test_fixture.test_case)
                    test_fixture.test_case.start_time = datetime.now()

                if is_before_suite_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeSuite)
                elif is_before_class_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeClass)
                elif is_before_group_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeGroup)
                elif is_before_method_failed:
                    warn_and_mark_skipped(PDecoratorType.BeforeMethod)
                else:
                    test_fixture.run()
                test_case = test_fixture.test_case
                logger_filler = "-" * (100 - len(test_case.full_name) - 6)
                if test_case.status == TestCaseStatus.PASSED:
                    pconsole.write_line("%s%s|PASS|" % (test_case.full_name, logger_filler))
                elif test_case.status == TestCaseStatus.FAILED:
                    pconsole.write_line("%s%s|FAIL|" % (test_case.full_name, logger_filler))
                elif test_case.status == TestCaseStatus.SKIPPED:
                    pconsole.write_line("%s%s|SKIP|" % (test_case.full_name, logger_filler))

                if test_fixture.test_case.after_method is None:
                    test_fixture.test_case.end_time = datetime.now()
                    test_listeners.on_test_case_finish(test_fixture.test_case)

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


def update_properties(**kwargs):
    threading.currentThread().update_properties(**kwargs)


def clear_properties():
    threading.current_thread().clear_properties()


def get_property(key):
    return threading.currentThread().get_property(key)


def get_name():
    return threading.currentThread().getName()


def kill_thread(thread):
    """Terminates a python thread from another thread.

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
