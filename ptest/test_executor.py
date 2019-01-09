import threading
import time
import traceback
from copy import copy
from datetime import datetime
from functools import cmp_to_key

from .enumeration import TestFixtureStatus, TestClassRunMode, TestCaseStatus
from .plistener import test_listeners
from .plogger import preporter, pconsole, pconsole_err
from .test_suite import AfterSuite, BeforeSuite, AfterClass, BeforeClass, BeforeGroup, AfterGroup, AfterMethod, \
    BeforeMethod, Test
from .util import call_function, kill_thread, format_thread_stack


class TestExecutor(threading.Thread):
    def __init__(self, parent_test_executor, workers=0):
        threading.Thread.__init__(self)
        self.parent_test_executor = parent_test_executor
        self.__properties = {}
        if self.parent_test_executor:
            for key, value in self.parent_test_executor.get_properties().items():
                if isinstance(value, (list, tuple, set, dict)):
                    self.__properties[key] = copy(value)
                else:
                    self.__properties[key] = value
        self.workers = workers
        self.lock = threading.RLock()
        if self.workers == 0:
            self.acquire_worker()

    def _run(self):
        pass

    def run(self):
        try:
            self._run()
        finally:
            self.release_worker()

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

    def allocate_worker(self, child_test_executor):
        with self.lock:
            if self.workers > 0:
                self.workers -= 1
                child_test_executor.workers += 1
                return True
            else:
                return False

    def apply_worker(self):
        if self.parent_test_executor:
            with self.lock:
                if self.parent_test_executor.allocate_worker(self):
                    return True
                else:
                    if self.parent_test_executor.apply_worker():
                        return self.parent_test_executor.allocate_worker(self)
                    else:
                        return False
        else:
            with self.lock:
                return self.workers > 0

    def acquire_worker(self):
        while True:
            if self.apply_worker():
                return
            else:
                time.sleep(1)

    def release_worker(self):
        if self.parent_test_executor:
            with self.parent_test_executor.lock:
                self.parent_test_executor.workers += self.workers
                self.workers = 0
        else:
            pass


class TestSuiteExecutor(TestExecutor):
    def __init__(self, test_suite, workers):
        TestExecutor.__init__(self, None, workers)
        self.test_suite = test_suite

    def _run(self):
        before_suite_executor = TestFixtureExecutor(self, self.test_suite.before_suite)
        test_listeners.on_test_suite_start(self.test_suite)
        self.test_suite.start_time = datetime.now()
        before_suite_executor.start_and_join()

        test_class_run_group_executors = []

        for test_class_run_group in self.test_suite.test_class_run_groups:
            test_class_run_group_executor = TestClassRunGroupExecutor(self, test_class_run_group)
            test_class_run_group_executors.append(test_class_run_group_executor)
            test_class_run_group_executor.start()

        for executor in test_class_run_group_executors:
            executor.join()

        after_suite_executor = TestFixtureExecutor(self, self.test_suite.after_suite)
        after_suite_executor.start_and_join()
        self.test_suite.end_time = datetime.now()
        test_listeners.on_test_suite_finish(self.test_suite)


class TestClassRunGroupExecutor(TestExecutor):
    def __init__(self, test_suite_executor, test_class_run_group):
        TestExecutor.__init__(self, test_suite_executor)
        self.test_class_run_group = test_class_run_group

    def _run(self):
        for test_class in self.test_class_run_group:
            TestClassExecutor(self, test_class).start_and_join()


class TestClassExecutor(TestExecutor):
    def __init__(self, test_class_run_group_executor, test_class):
        TestExecutor.__init__(self, test_class_run_group_executor)
        self.test_class = test_class

    def _run(self):
        before_class_executor = TestFixtureExecutor(self, self.test_class.before_class)
        test_listeners.on_test_class_start(self.test_class)
        self.test_class.start_time = datetime.now()
        before_class_executor.start_and_join()

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

        after_class_executor = TestFixtureExecutor(self, self.test_class.after_class)
        after_class_executor.start_and_join()
        self.test_class.end_time = datetime.now()
        test_listeners.on_test_class_finish(self.test_class)


class TestGroupExecutor(TestExecutor):
    def __init__(self, test_class_executor, test_group):
        TestExecutor.__init__(self, test_class_executor)
        self.test_group = test_group

    def _run(self):
        before_group_executor = TestFixtureExecutor(self, self.test_group.before_group)
        test_listeners.on_test_group_start(self.test_group)
        self.test_group.start_time = datetime.now()
        before_group_executor.start_and_join()

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

        after_group_executor = TestFixtureExecutor(self, self.test_group.after_group)
        after_group_executor.start_and_join()
        self.test_group.end_time = datetime.now()
        test_listeners.on_test_group_finish(self.test_group)


class TestCaseExecutor(TestExecutor):
    def __init__(self, test_group_executor, test_case):
        TestExecutor.__init__(self, test_group_executor)
        self.test_case = test_case

    def _run(self):
        before_method_executor = TestFixtureExecutor(self, self.test_case.before_method)
        test_listeners.on_test_case_start(self.test_case)
        self.test_case.start_time = datetime.now()
        before_method_executor.start_and_join()

        test_executor = TestFixtureExecutor(self, self.test_case.test)
        test_executor.start_and_join()

        logger_filler = "-" * (100 - len(self.test_case.full_name) - 6)
        if self.test_case.status == TestCaseStatus.PASSED:
            pconsole.write_line("%s%s|PASS|" % (self.test_case.full_name, logger_filler))
        elif self.test_case.status == TestCaseStatus.FAILED:
            pconsole.write_line("%s%s|FAIL|" % (self.test_case.full_name, logger_filler))
        elif self.test_case.status == TestCaseStatus.SKIPPED:
            pconsole.write_line("%s%s|SKIP|" % (self.test_case.full_name, logger_filler))

        after_method_executor = TestFixtureExecutor(self, self.test_case.after_method)
        after_method_executor.start_and_join()
        self.test_case.end_time = datetime.now()
        test_listeners.on_test_case_finish(self.test_case)


class TestFixtureExecutor(TestExecutor):
    def __init__(self, parent_test_executor, test_fixture):
        TestExecutor.__init__(self, parent_test_executor)
        self.test_fixture = test_fixture

    def _run(self):
        if self.test_fixture.is_empty: return

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

        # spread before's attributes
        if isinstance(self.test_fixture, BeforeSuite):
            before_suite_dict = self.test_fixture.test_fixture_ref.__self__.__dict__
            for test_class in self.test_fixture.test_suite.test_classes:
                test_class.test_class_ref.__dict__.update(before_suite_dict)
                for test_group in test_class.test_groups:
                    test_group.test_class_ref.__dict__.update(before_suite_dict)
                    for test_case in test_group.test_cases:
                        test_case.test_case_ref.__self__.__dict__.update(before_suite_dict)
        elif isinstance(self.test_fixture, BeforeClass):
            before_class_dict = self.test_fixture.test_fixture_ref.__self__.__dict__
            for test_group in self.test_fixture.test_class.test_groups:
                test_group.test_class_ref.__dict__.update(before_class_dict)
                for test_case in test_group.test_cases:
                    test_case.test_case_ref.__self__.__dict__.update(before_class_dict)
        elif isinstance(self.test_fixture, BeforeGroup):
            before_group_dict = self.test_fixture.test_fixture_ref.__self__.__dict__
            for test_case in self.test_fixture.test_group.test_cases:
                test_case.test_case_ref.__self__.__dict__.update(before_group_dict)

        self.update_properties({"running_test_fixture": None})
        self.test_fixture.end_time = datetime.now()

    def run_test_fixture(self):
        self.test_fixture.status = TestFixtureStatus.RUNNING
        test_fixture_sub_executor = TestFixtureSubExecutor(self)
        test_fixture_sub_executor.start()
        if self.test_fixture.timeout > 0:
            test_fixture_sub_executor.join(self.test_fixture.timeout)
            if test_fixture_sub_executor.isAlive():
                stack_trace = format_thread_stack(test_fixture_sub_executor)
                try:
                    kill_thread(test_fixture_sub_executor)
                except Exception as e:
                    pconsole_err.write_line(e)
                from .plogger import preporter
                self.test_fixture.status = TestFixtureStatus.FAILED
                self.test_fixture.failure_message = "Timed out executing this test fixture in %s seconds." % self.test_fixture.timeout
                self.test_fixture.failure_type = "TimeoutException"
                self.test_fixture.stack_trace = stack_trace
                preporter.error("Failed with following message:\n%s\n%s" % (self.test_fixture.failure_message, self.test_fixture.stack_trace), True)
        else:
            test_fixture_sub_executor.join()

    def skip_test_fixture(self, caused_test_fixture):
        from .plogger import preporter
        self.test_fixture.status = TestFixtureStatus.SKIPPED
        self.test_fixture.skip_message = "@%s failed, so skipped." % caused_test_fixture.fixture_type
        preporter.warn("@%s failed, so skipped." % caused_test_fixture.fixture_type)


class TestFixtureSubExecutor(TestExecutor):
    def __init__(self, test_fixture_executor):
        TestExecutor.__init__(self, test_fixture_executor)
        self.test_fixture = test_fixture_executor.test_fixture
        self.setDaemon(True)

    def _run(self):
        if isinstance(self.test_fixture, Test):
            self.run_test()
        else:
            self.run_test_configuration()

    def run_test(self):
        if self.test_fixture.expected_exceptions:
            expected_exceptions = self.test_fixture.expected_exceptions
            expected_exceptions_names = str(["%s.%s" % (e.__module__, e.__name__) for e in expected_exceptions.keys()])
            try:
                params = self.test_fixture.parameters or []
                call_function(self.test_fixture.test_fixture_ref, *params)
            except Exception as e:
                exception = e.__class__
                exception_name = "%s.%s" % (exception.__module__, exception.__name__)
                matched_exceptions = [expected_exception for expected_exception in expected_exceptions.keys() if
                                      issubclass(exception, expected_exception)]
                if matched_exceptions:
                    def cmp_matched_exception(exception_a, exception_b):
                        return -1 if issubclass(exception_a, exception_b) else 1

                    matched_exception = sorted(matched_exceptions, key=cmp_to_key(cmp_matched_exception))[0]
                    if not expected_exceptions[matched_exception] or expected_exceptions[matched_exception].search(str(e)):
                        self.test_fixture.status = TestFixtureStatus.PASSED
                    else:
                        self.test_fixture.status = TestFixtureStatus.FAILED
                        self.test_fixture.failure_message = "The exception <%s> was thrown with the wrong message: Expected message regex: <%s>, Actual message: <%s>." \
                                                            % (exception_name, expected_exceptions[matched_exception].pattern, str(e))
                        self.test_fixture.failure_type = "WrongExceptionMessageError"
                        self.test_fixture.stack_trace = traceback.format_exc()
                        preporter.error("Failed with following message:\n%s\n%s" % (self.test_fixture.failure_message, self.test_fixture.stack_trace), True)
                else:
                    self.test_fixture.status = TestFixtureStatus.FAILED
                    self.test_fixture.failure_message = "Expected exception: one of %s, Actual exception: <%s>." \
                                                        % (expected_exceptions_names, exception_name)
                    self.test_fixture.failure_type = "WrongExceptionThrownError"
                    self.test_fixture.stack_trace = traceback.format_exc()
                    preporter.error("Failed with following message:\n%s\n%s" % (self.test_fixture.failure_message, self.test_fixture.stack_trace), True)
            else:
                self.test_fixture.status = TestFixtureStatus.FAILED
                self.test_fixture.failure_message = "Expected exception: one of %s, Actual: NO exception was thrown." \
                                                    % expected_exceptions_names
                self.test_fixture.failure_type = "NoExceptionThrownError"
                self.test_fixture.stack_trace = self.test_fixture.failure_message
                preporter.error("Failed with following message:\n%s" % self.test_fixture.failure_message, True)
        else:
            try:
                params = self.test_fixture.parameters or []
                call_function(self.test_fixture.test_fixture_ref, *params)
            except Exception as e:
                self.test_fixture.status = TestFixtureStatus.FAILED
                self.test_fixture.failure_message = str(e).strip() or "\n".join([str(arg) for arg in e.args])
                self.test_fixture.failure_type = "%s.%s" % (e.__class__.__module__, e.__class__.__name__)
                self.test_fixture.stack_trace = traceback.format_exc()
                preporter.error("Failed with following message:\n%s" % self.test_fixture.stack_trace, True)
            else:
                self.test_fixture.status = TestFixtureStatus.PASSED

    def run_test_configuration(self):
        try:
            params = {1: [], 2: [self.test_fixture.context]}[self.test_fixture.parameters_count]
            call_function(self.test_fixture.test_fixture_ref, *params)
        except Exception as e:
            self.test_fixture.status = TestFixtureStatus.FAILED
            self.test_fixture.failure_message = str(e).strip() or "\n".join([str(arg) for arg in e.args])
            self.test_fixture.failure_type = "%s.%s" % (e.__class__.__module__, e.__class__.__name__)
            self.test_fixture.stack_trace = traceback.format_exc()
            preporter.error("Failed with following message:\n%s" % self.test_fixture.stack_trace, True)
        else:
            self.test_fixture.status = TestFixtureStatus.PASSED


def current_executor():
    return threading.currentThread()
