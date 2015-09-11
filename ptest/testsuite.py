from datetime import datetime
import os

try:
    from urlparse import urljoin
    from urllib import unquote, pathname2url
except ImportError:
    from urllib.parse import urljoin, unquote
    from urllib.request import pathname2url
import inspect
import threading

from .enumeration import TestClassRunMode, TestCaseStatus, PDecoratorType, TestFixtureStatus

__author__ = 'karl.gong'

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class TestSuite:
    def __init__(self, name):
        self.test_classes = []
        self.start_time = None
        self.end_time = None
        self.name = name
        self.before_suite = None
        self.after_suite = None
        self.__lock = threading.Lock()

    def init_test_fixture(self):
        for test_class in self.test_classes:
            # reflect the before class and after class
            for element in dir(test_class.test_class_ref):
                attr = getattr(test_class.test_class_ref, element)
                try:
                    pd_type = attr.__pd_type__
                    is_enabled = attr.__enabled__
                except AttributeError:
                    continue
                if is_enabled:
                    if pd_type == PDecoratorType.BeforeSuite:
                        self.before_suite = BeforeSuite(self, attr)
                    elif pd_type == PDecoratorType.AfterSuite:
                        self.after_suite = AfterSuite(self, attr)

    def get_test_class(self, full_name):
        for test_class in self.test_classes:
            if test_class.full_name == full_name:
                return test_class
        return None

    def add_test_class(self, test_class_ref):
        test_class = TestClass(self, test_class_ref)
        self.test_classes.append(test_class)
        return test_class

    def add_test_case(self, test_class_ref, test_case_ref):
        test_class = self.get_test_class(test_class_ref.__full_name__)
        if test_class is None:
            test_class = self.add_test_class(test_class_ref)
        test_group = test_class.get_test_group(test_case_ref.__group__)
        if test_group is None:
            test_group = test_class.add_test_group(test_case_ref.__group__, test_class_ref)
        test_case = test_group.get_test_case(test_case_ref.__name__)
        if test_case is None:
            test_group.add_test_case(test_case_ref)

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds

    @property
    def test_case_status_count(self):
        total, passed, failed, skipped, not_run = 0, 0, 0, 0, 0
        for test_class in self.test_classes:
            t, p, f, s, n = test_class.test_case_status_count
            total += t
            passed += p
            failed += f
            skipped += s
            not_run += n
        return total, passed, failed, skipped, not_run

    @property
    def pass_rate(self):
        total, passed, _, _, _ = self.test_case_status_count
        if total == 0:
            return 0
        return float(passed) * 100 / total

    @property
    def test_case_names(self):
        """
            The test case name list.
        """
        test_case_names = []
        for test_class in self.test_classes:
            for test_group in test_class.test_groups:
                for test_case in test_group.test_cases:
                    test_case_names.append(test_case.full_name)
        return test_case_names

    def sort_test_classes_for_running(self):
        """
            Sort the test classes by run_mode, put SingleLine classes to the top.
            Invoking this function before running test cases will increase the running efficiency.
        """
        self.test_classes = sorted(self.test_classes, key=lambda item: item.run_mode, reverse=True)

    def sort_test_classes_for_report(self):
        """
            Sort the test classes by test class's full name.
        """
        self.test_classes = sorted(self.test_classes, key=lambda item: item.full_name)

    def pop_test_fixture(self):
        from . import testexecutor
        current_thread_name = testexecutor.get_name()
        self.__lock.acquire()
        try:
            for test_class in self.test_classes:
                if test_class.popped:
                    continue
                if test_class.run_mode == TestClassRunMode.SingleLine:
                    if test_class.run_thread == current_thread_name:
                        return test_class.pop_test_fixture()
                    elif test_class.run_thread is None:
                        test_class.run_thread = current_thread_name
                        return test_class.pop_test_fixture()
                else:
                    return test_class.pop_test_fixture()
            raise NoTestFixtureAvailableForThisThread
        finally:
            self.__lock.release()


class NoTestFixtureAvailableForThisThread(Exception):
    pass


class TestClass:
    def __init__(self, test_suite, test_class_ref):
        self.test_suite = test_suite
        self.test_class_ref = test_class_ref
        self.test_groups = []
        self.name = test_class_ref.__class__.__name__
        self.full_name = test_class_ref.__full_name__
        self.popped = False
        self.run_thread = None
        self.run_mode = test_class_ref.__run_mode__
        self.description = test_class_ref.__description__

        self.before_class = None
        self.after_class = None
        # reflect the before class and after class
        for element in dir(test_class_ref):
            attr = getattr(test_class_ref, element)
            try:
                pd_type = attr.__pd_type__
                is_enabled = attr.__enabled__
            except AttributeError:
                continue
            if is_enabled:
                if pd_type == PDecoratorType.BeforeClass:
                    self.before_class = BeforeClass(self, attr)
                elif pd_type == PDecoratorType.AfterClass:
                    self.after_class = AfterClass(self, attr)

    def get_test_group(self, name):
        for test_group in self.test_groups:
            if test_group.name == name:
                return test_group
        return None

    def add_test_group(self, name, test_class_ref):
        test_group = TestGroup(name, self, test_class_ref)
        self.test_groups.append(test_group)
        return test_group

    @property
    def start_time(self):
        return min([test_group.start_time for test_group in self.test_groups])

    @property
    def end_time(self):
        return max([test_group.end_time for test_group in self.test_groups])

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds

    @property
    def test_case_status_count(self):
        total, passed, failed, skipped, not_run = 0, 0, 0, 0, 0
        for test_group in self.test_groups:
            t, p, f, s, n = test_group.test_case_status_count
            total += t
            passed += p
            failed += f
            skipped += s
            not_run += n
        return total, passed, failed, skipped, not_run

    @property
    def pass_rate(self):
        total, passed, _, _, _ = self.test_case_status_count
        if total == 0:
            return 0
        return float(passed) * 100 / total

    def pop_test_fixture(self):
        if self.before_class and not self.after_class.popped:
            self.before_class.popped = True
            return self.before_class
        for test_group in self.test_groups:
            if not test_group.popped:
                if not self.after_class and test_group is self.test_groups[-1]:
                    self.popped = True
                return test_group.pop_test_fixture()
        if self.after_class and not self.after_class.popped:
            self.after_class.popped = True
            self.popped = True
            return self.after_class


class TestGroup:
    def __init__(self, name, test_class, test_class_ref):
        self.test_class = test_class
        self.test_suite = self.test_class.test_suite
        self.test_class_ref = test_class_ref
        self.test_cases = []
        self.name = name
        self.full_name = "%s(%s)" % (test_class.full_name, name)
        self.popped = False

        self.before_group = None
        self.after_group = None
        # reflect the before group and after group
        for element in dir(test_class_ref):
            attr = getattr(test_class_ref, element)
            try:
                pd_type = attr.__pd_type__
                is_enabled = attr.__enabled__
                group = attr.__group__
            except AttributeError:
                continue
            if is_enabled and self.name == group:
                if pd_type == PDecoratorType.BeforeGroup:
                    self.before_group = BeforeGroup(self, attr)
                elif pd_type == PDecoratorType.AfterGroup:
                    self.after_group = AfterGroup(self, attr)

    def get_test_case(self, name):
        for test_case in self.test_cases:
            if test_case.name == name:
                return test_case
        return None

    def add_test_case(self, test_case_ref):
        test_case = TestCase(self, test_case_ref)
        self.test_cases.append(test_case)
        return test_case

    @property
    def start_time(self):
        if self.before_group:
            return self.before_group.start_time
        return min([test_case.start_time for test_case in self.test_cases])

    @property
    def end_time(self):
        if self.after_group:
            return self.after_group.end_time
        return max([test_case.end_time for test_case in self.test_cases])

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds

    @property
    def test_case_status_count(self):
        total, passed, failed, skipped, not_run = 0, 0, 0, 0, 0
        for test_case in self.test_cases:
            total += 1
            status = test_case.status
            if status == TestCaseStatus.PASSED:
                passed += 1
            elif status == TestCaseStatus.FAILED:
                failed += 1
            elif status == TestCaseStatus.SKIPPED:
                skipped += 1
            elif status == TestCaseStatus.NOT_RUN:
                not_run += 1
        return total, passed, failed, skipped, not_run

    @property
    def pass_rate(self):
        total, passed, _, _, _ = self.test_case_status_count
        if total == 0:
            return 0
        return float(passed) * 100 / total

    def pop_test_fixture(self):
        if self.before_group and not self.before_group.popped:
            self.before_group.popped = True
            return self.before_group
        for test_case in self.test_cases:
            if not test_case.popped:
                if not self.after_group and test_case is self.test_cases[-1]:
                    self.popped = True
                return test_case.pop_test_fixture()
        if self.after_group and not self.after_group.popped:
            self.after_group.popped = True
            self.popped = True
            return self.after_group


class TestCase:
    def __init__(self, test_group, test_case_ref):
        self.test_group = test_group
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_class.test_suite
        self.test_case_ref = test_case_ref
        self.name = test_case_ref.__name__
        self.full_name = "%s.%s" % (self.test_group.test_class.full_name, self.name)
        self.start_time = None
        self.end_time = None
        self.popped = False

        self.test = Test(self, test_case_ref)

        self.tags = self.test.tags
        self.group = self.test.group
        self.description = self.test.description
        self.location = self.test.location

        self.before_method = None
        self.after_method = None
        # reflect the before method and after method
        for element in dir(test_case_ref.__self__):
            attr = getattr(test_case_ref.__self__, element)
            try:
                pd_type = attr.__pd_type__
                is_enabled = attr.__enabled__
                group = attr.__group__
            except AttributeError:
                continue
            if is_enabled and self.group == group:
                if pd_type == PDecoratorType.BeforeMethod:
                    self.before_method = BeforeMethod(self, attr)
                elif pd_type == PDecoratorType.AfterMethod:
                    self.after_method = AfterMethod(self, attr)

    @property
    def failure_message(self):
        return self.test.failure_message

    @property
    def failure_type(self):
        return self.test.failure_type

    @property
    def stack_trace(self):
        return self.test.stack_trace

    @property
    def skip_message(self):
        return self.test.skip_message

    @property
    def status(self):
        return self.test.status

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds

    def pop_test_fixture(self):
        if self.before_method and not self.before_method.popped:
            self.before_method.popped = True
            return self.before_method
        elif not self.test.popped:
            self.test.popped = True
            if not self.after_method:
                self.popped = True
            return self.test
        elif self.after_method and not self.after_method.popped:
            self.after_method.popped = True
            self.popped = True
            return self.after_method


class TestFixture:
    def __init__(self, context, test_fixture_ref, fixture_type):
        self.context = context
        self.test_fixture_ref = test_fixture_ref
        self.fixture_type = fixture_type
        self.status = TestFixtureStatus.NOT_RUN
        self.popped = False
        self.failure_message = ""
        self.failure_type = ""
        self.stack_trace = ""
        self.skip_message = ""
        self.start_time = None
        self.end_time = None
        self.logs = []
        self.screenshot = None
        self.description = test_fixture_ref.__description__
        self.timeout = test_fixture_ref.__timeout__

        file_path = os.path.abspath(inspect.getfile(test_fixture_ref))
        _, line_no = inspect.getsourcelines(test_fixture_ref)
        self.location = urljoin("file:", "%s:%s" % (unquote(pathname2url(file_path)), line_no))

        self.arguments_count = len(inspect.getargspec(self.test_fixture_ref)[0])
        if self.arguments_count not in [1, 2]:
            raise TypeError(
                "arguments number of %s() is not acceptable. Please give 1 or 2 arguments." % self.test_fixture_ref.__name__)

    def run(self):
        from .testexecutor import TestFixtureExecutor, kill_thread
        test_fixture_executor = TestFixtureExecutor(self)
        self.start_time = datetime.now()
        test_fixture_executor.start()
        if self.timeout > 0:
            test_fixture_executor.join(self.timeout)
            if test_fixture_executor.isAlive():
                from .plogger import preporter
                from . import screencapturer
                self.status = TestFixtureStatus.FAILED
                self.failure_message = "Timed out executing this test fixture in %s seconds." % self.timeout
                self.failure_type = "TimeoutException"
                self.stack_trace = ""
                preporter.error(
                    "Failed with following message:\n" + self.failure_message)
                screencapturer.take_screenshot()
                kill_thread(test_fixture_executor)
        else:
            test_fixture_executor.join()
        self.end_time = datetime.now()

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class BeforeSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.BeforeSuite)
        self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)
        self.test_suite = self.context


class AfterSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.AfterSuite)
        self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)
        self.test_suite = self.context
        self.always_run = test_fixture_ref.__always_run__


class BeforeClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.BeforeClass)
        self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite


class AfterClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.AfterClass)
        self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        self.always_run = test_fixture_ref.__always_run__


class BeforeGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.BeforeClass)
        self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        self.group = test_fixture_ref.__group__


class AfterGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.AfterClass)
        self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        self.always_run = test_fixture_ref.__always_run__
        self.group = test_fixture_ref.__group__


class Test(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.Test)
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.tags = test_fixture_ref.__tags__
        self.group = test_fixture_ref.__group__


class BeforeMethod(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.BeforeMethod)
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.group = test_fixture_ref.__group__


class AfterMethod(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.AfterMethod)
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.always_run = test_fixture_ref.__always_run__
        self.group = test_fixture_ref.__group__


test_suite = TestSuite("DefaultSuite")
