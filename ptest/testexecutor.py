from copy import copy
import ctypes
import threading
import traceback
import time

from datetime import datetime

from . import screencapturer, config
from .enumeration import TestFixtureStatus, TestClassRunMode, TestCaseStatus
from .plogger import preporter, pconsole
from .testsuite import AfterSuite, BeforeSuite, AfterClass, BeforeClass, BeforeGroup, AfterGroup, AfterMethod, \
    BeforeMethod
from .plistener import test_listeners

__author__ = 'karl.gong'


class TestExecutor(threading.Thread):
    def __init__(self, parent_test_executor):
        threading.Thread.__init__(self)
        self.parent_test_executor = parent_test_executor
        if self.parent_test_executor:
            self.__properties = copy(self.parent_test_executor.get_properties())
        else:
            self.__properties = {}

    def start_and_join(self):
        self.start()
        self.join()

    def update_properties(self, properties):
        self.__properties.update(properties)

    def clear_properties(self):
        self.__properties.clear()

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None

    def get_properties(self):
        return self.__properties


class TestSuiteExecutor(TestExecutor):
    def __init__(self, test_suite):
        TestExecutor.__init__(self, None)
        self.test_suite = test_suite

    def run(self):
        test_listeners.on_test_suite_start(self.test_suite)
        self.test_suite.start_time = datetime.now()
        test_fixture_executor_pool.apply_for_executor(self, self.test_suite.before_suite).start_and_join()

        test_class_executors = []

        for test_class in self.test_suite.test_classes:
            test_class_executor = TestClassExecutor(self, test_class)
            test_class_executors.append(test_class_executor)
            test_class_executor.start()

        for executor in test_class_executors:
            executor.join()

        test_fixture_executor_pool.apply_for_executor(self, self.test_suite.after_suite).start_and_join()
        self.test_suite.end_time = datetime.now()
        test_listeners.on_test_suite_finish(self.test_suite)


class TestClassExecutor(TestExecutor):
    def __init__(self, test_suite_executor, test_class):
        TestExecutor.__init__(self, test_suite_executor)
        self.test_class = test_class

    def run(self):
        test_listeners.on_test_class_start(self.test_class)
        self.test_class.start_time = datetime.now()
        test_fixture_executor_pool.apply_for_executor(self, self.test_class.before_class).start_and_join()

        if self.test_class.run_mode == TestClassRunMode.SingleLine:
            for test_group in self.test_class.test_groups:
                TestGroupExecutor(self, test_group).start_and_join()
        else:
            test_group_executors = []

            for test_group in self.test_class.test_groups:
                test_group_executor = TestGroupExecutor(self, test_group)
                test_group_executors.append(test_group_executor)
                test_group_executor.start()

            for executor in test_group_executors:
                executor.join()

        test_fixture_executor_pool.apply_for_executor(self, self.test_class.after_class).start_and_join()
        self.test_class.end_time = datetime.now()
        test_listeners.on_test_class_finish(self.test_class)


class TestGroupExecutor(TestExecutor):
    def __init__(self, test_class_executor, test_group):
        TestExecutor.__init__(self, test_class_executor)
        self.test_group = test_group

    def run(self):
        test_listeners.on_test_group_start(self.test_group)
        self.test_group.start_time = datetime.now()
        test_fixture_executor_pool.apply_for_executor(self, self.test_group.before_group).start_and_join()

        if self.test_group.test_class.run_mode == TestClassRunMode.SingleLine:
            for test_case in self.test_group.test_cases:
                TestCaseExecutor(self, test_case).start_and_join()
        else:
            test_case_executors = []

            for test_case in self.test_group.test_cases:
                test_case_executor = TestCaseExecutor(self, test_case)
                test_case_executors.append(test_case_executor)
                test_case_executor.start()

            for executor in test_case_executors:
                executor.join()

        test_fixture_executor_pool.apply_for_executor(self, self.test_group.after_group).start_and_join()
        self.test_group.end_time = datetime.now()
        test_listeners.on_test_group_finish(self.test_group)


class TestCaseExecutor(TestExecutor):
    def __init__(self, test_group_executor, test_case):
        TestExecutor.__init__(self, test_group_executor)
        self.test_case = test_case

    def run(self):
        test_listeners.on_test_case_start(self.test_case)
        self.test_case.start_time = datetime.now()
        test_fixture_executor_pool.apply_for_executor(self, self.test_case.before_method).start_and_join()

        test_fixture_executor_pool.apply_for_executor(self, self.test_case.test).start_and_join()

        logger_filler = "-" * (100 - len(self.test_case.full_name) - 6)
        if self.test_case.status == TestCaseStatus.PASSED:
            pconsole.write_line("%s%s|PASS|" % (self.test_case.full_name, logger_filler))
        elif self.test_case.status == TestCaseStatus.FAILED:
            pconsole.write_line("%s%s|FAIL|" % (self.test_case.full_name, logger_filler))
        elif self.test_case.status == TestCaseStatus.SKIPPED:
            pconsole.write_line("%s%s|SKIP|" % (self.test_case.full_name, logger_filler))

        test_fixture_executor_pool.apply_for_executor(self, self.test_case.after_method).start_and_join()
        self.test_case.end_time = datetime.now()
        test_listeners.on_test_case_finish(self.test_case)


class TestFixtureExecutor(TestExecutor):
    def __init__(self, test_case_executor, test_fixture):
        TestExecutor.__init__(self, test_case_executor)
        self.test_fixture = test_fixture

    def run_test_fixture(self):
        if self.test_fixture.is_empty:
            self.test_fixture.status = TestFixtureStatus.PASSED
            return

        self.test_fixture.status = TestFixtureStatus.RUNNING
        test_fixture_sub_executor = TestFixtureSubExecutor(self)
        test_fixture_sub_executor.start()
        if self.test_fixture.timeout > 0:
            test_fixture_sub_executor.join(self.test_fixture.timeout)
            if test_fixture_sub_executor.isAlive():
                from .plogger import preporter
                from . import screencapturer
                self.test_fixture.status = TestFixtureStatus.FAILED
                self.test_fixture.failure_message = "Timed out executing this test fixture in %s seconds." % self.test_fixture.timeout
                self.test_fixture.failure_type = "TimeoutException"
                self.test_fixture.stack_trace = ""
                preporter.error("Failed with following message:\n" + self.test_fixture.failure_message)
                screencapturer.take_screenshot()
                kill_thread(test_fixture_sub_executor)
        else:
            test_fixture_sub_executor.join()

    def skip_test_fixture(self, caused_test_fixture):
        if self.test_fixture.is_empty:
            self.test_fixture.status = TestFixtureStatus.SKIPPED
            return

        from .plogger import preporter
        self.test_fixture.status = TestFixtureStatus.SKIPPED
        self.test_fixture.skip_message = "@%s failed, so skipped." % caused_test_fixture.fixture_type
        preporter.warn("@%s failed, so skipped." % caused_test_fixture.fixture_type)


    def run(self):
        self.test_fixture.start_time = datetime.now()
        self.update_properties({"running_test_fixture": self.test_fixture})

        failed_setup_fixture = self.test_fixture.context.get_failed_setup_fixture()
        if not failed_setup_fixture:
            self.run_test_fixture()
        elif isinstance(self.test_fixture, AfterSuite) and isinstance(failed_setup_fixture, BeforeSuite) and self.test_fixture.always_run:
            self.run_test_fixture()
        elif isinstance(self.test_fixture, AfterClass) and isinstance(failed_setup_fixture, BeforeClass) and self.test_fixture.always_run:
            self.run_test_fixture()
        elif isinstance(self.test_fixture, AfterGroup) and isinstance(failed_setup_fixture, BeforeGroup) and self.test_fixture.always_run:
            self.run_test_fixture()
        elif isinstance(self.test_fixture, AfterMethod) and isinstance(failed_setup_fixture, BeforeMethod) and self.test_fixture.always_run:
            self.run_test_fixture()
        else:
            self.skip_test_fixture(failed_setup_fixture)

        self.update_properties({"running_test_fixture": None})
        self.test_fixture.end_time = datetime.now()


class TestFixtureSubExecutor(TestExecutor):
    def __init__(self, parent_executor):
        TestExecutor.__init__(self, parent_executor)
        self.test_fixture = parent_executor.test_fixture
        self.setDaemon(True)

    def run(self):
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


class TestFixtureExecutorPool(threading.Thread):
    def __init__(self, size):
        threading.Thread.__init__(self)
        self.size = size
        self.running_test_executors = []
        self.pending_test_fixtures = []
        self.__test_fixture_lock = threading.Lock()
        self.__test_executor_lock = threading.Lock()

    def get_top_test_fixture(self):
        self.__test_fixture_lock.acquire()
        try:
            self.pending_test_fixtures = sorted(self.pending_test_fixtures, key=lambda item: item.execution_priority)
            return self.pending_test_fixtures[0]
        finally:
            self.__test_fixture_lock.release()

    def get_running_test_executors_count(self):
        self.__test_executor_lock.acquire()
        try:
            self.running_test_executors = [test_executor for test_executor in self.running_test_executors if
                                           test_executor.isAlive()]
            return len(self.running_test_executors)
        finally:
            self.__test_executor_lock.release()

    def apply_for_executor(self, test_executor, test_fixture):
        self.__test_fixture_lock.acquire()
        try:
            self.pending_test_fixtures.append(test_fixture)
        finally:
            self.__test_fixture_lock.release()

        while self.get_running_test_executors_count() >= self.size or self.get_top_test_fixture() != test_fixture:
            time.sleep(1)

        test_fixture_executor = TestFixtureExecutor(test_executor, test_fixture)

        self.__test_executor_lock.acquire()
        try:
            self.running_test_executors.append(test_fixture_executor)
        finally:
            self.__test_executor_lock.release()

        self.__test_fixture_lock.acquire()
        try:
            self.pending_test_fixtures.remove(test_fixture)
        finally:
            self.__test_fixture_lock.release()

        return test_fixture_executor


test_fixture_executor_pool = TestFixtureExecutorPool(int(config.get_option("test_executor_number")))


def current_executor():
    return threading.currentThread()


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
