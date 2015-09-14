import os

from datetime import datetime

try:
    from urlparse import urljoin
    from urllib import unquote, pathname2url
except ImportError:
    from urllib.parse import urljoin, unquote
    from urllib.request import pathname2url
import inspect
import threading

from .enumeration import TestClassRunMode, TestCaseStatus, PDecoratorType, TestFixtureStatus, PopStatus

__author__ = 'karl.gong'

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class TestSuite:
    def __init__(self, name):
        self.test_classes = []
        self.start_time = None
        self.end_time = None
        self.name = name
        self.before_suite = BeforeSuite(self, None)
        self.after_suite = AfterSuite(self, None)
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

    def get_failed_setup_fixture(self):
        if self.before_suite.status == TestFixtureStatus.FAILED:
            return self.before_suite
        return None

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
    def test_cases(self):
        """
            The test case list.
        """
        test_case_list = []
        for test_class in self.test_classes:
            test_case_list = test_case_list + test_class.test_cases
        return test_case_list

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

    @property
    def pop_status(self):
        if self.before_suite.pop_status == PopStatus.UNPOPPED:
            return PopStatus.UNPOPPED

        if self.before_suite.pop_status == PopStatus.RUNNING:
            return PopStatus.BLOCKING

        test_class_pop_statuses = set([test_class.pop_status for test_class in self.test_classes])

        if test_class_pop_statuses == {PopStatus.FINISHED, PopStatus.BLOCKING}:
            return PopStatus.BLOCKING

        if test_class_pop_statuses == {PopStatus.FINISHED}:
            if self.after_suite.pop_status == PopStatus.RUNNING:
                return PopStatus.BLOCKING
            if self.after_suite.pop_status == PopStatus.FINISHED:
                return PopStatus.FINISHED

        return PopStatus.RUNNING

    def pop_test_unit(self):
        from . import testexecutor
        current_thread_name = testexecutor.get_name()
        self.__lock.acquire()
        try:
            if self.before_suite.pop_status == PopStatus.UNPOPPED:
                self.before_suite.pop_status = PopStatus.RUNNING
                return self.before_suite

            if self.pop_status == PopStatus.BLOCKING:
                return None

            for test_class in self.test_classes:
                if test_class.pop_status in [PopStatus.UNPOPPED, PopStatus.RUNNING]:
                    if test_class.run_mode == TestClassRunMode.SingleLine:
                        if test_class.run_thread == current_thread_name:
                            return test_class.pop_test_unit()
                        elif test_class.run_thread is None:
                            test_class.run_thread = current_thread_name
                            return test_class.pop_test_unit()
                    else:
                        return test_class.pop_test_unit()

            if self.pop_status == PopStatus.BLOCKING:
                return None

            if self.after_suite.pop_status == PopStatus.UNPOPPED:
                self.after_suite.pop_status = PopStatus.RUNNING
                return self.after_suite

            raise NoTestUnitAvailableForThisThread
        finally:
            self.__lock.release()


class NoTestUnitAvailableForThisThread(Exception):
    pass


class TestClass:
    def __init__(self, test_suite, test_class_ref):
        self.test_suite = test_suite
        self.test_class_ref = test_class_ref
        self.test_groups = []
        self.name = test_class_ref.__class__.__name__
        self.full_name = test_class_ref.__full_name__
        self.start_time = None
        self.end_time = None
        self.run_thread = None
        self.run_mode = test_class_ref.__run_mode__
        self.description = test_class_ref.__description__

        self.before_class = BeforeClass(self, None)
        self.after_class = AfterClass(self, None)
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

    def get_failed_setup_fixture(self):
        setup_fixture = self.test_suite.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_class.status == TestFixtureStatus.FAILED:
            return self.before_class
        return None

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
    def test_cases(self):
        """
            The test case list.
        """
        test_case_list = []
        for test_group in self.test_groups:
            test_case_list = test_case_list + test_group.test_cases
        return test_case_list

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

    @property
    def pop_status(self):
        if self.before_class.pop_status == PopStatus.UNPOPPED:
            return PopStatus.UNPOPPED

        if self.before_class.pop_status == PopStatus.RUNNING:
            return PopStatus.BLOCKING

        test_group_pop_statuses = set([test_group.pop_status for test_group in self.test_groups])

        if test_group_pop_statuses == {PopStatus.FINISHED, PopStatus.BLOCKING}:
            return PopStatus.BLOCKING

        if test_group_pop_statuses == {PopStatus.FINISHED}:
            if self.after_class.pop_status == PopStatus.RUNNING:
                return PopStatus.BLOCKING
            if self.after_class.pop_status == PopStatus.FINISHED:
                return PopStatus.FINISHED

        return PopStatus.RUNNING

    def pop_test_unit(self):
        if self.before_class == PopStatus.UNPOPPED:
            self.before_class.pop_status = PopStatus.RUNNING
            return self.before_class

        for test_group in self.test_groups:
            if test_group.pop_status in [PopStatus.UNPOPPED, PopStatus.RUNNING]:
                return test_group.pop_test_unit()

        if self.after_class == PopStatus.UNPOPPED:
            self.after_class.pop_status = PopStatus.RUNNING
            return self.after_class


class TestGroup:
    def __init__(self, name, test_class, test_class_ref):
        self.test_class = test_class
        self.test_suite = self.test_class.test_suite
        self.test_class_ref = test_class_ref
        self.test_cases = []
        self.name = name
        self.full_name = "%s(%s)" % (test_class.full_name, name)
        self.start_time = None
        self.end_time = None

        self.before_group = BeforeGroup(self, None)
        self.after_group = AfterGroup(self, None)
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

    def get_failed_setup_fixture(self):
        setup_fixture = self.test_class.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_group.status == TestFixtureStatus.FAILED:
            return self.before_group
        return None

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

    @property
    def pop_status(self):
        if self.before_group.pop_status == PopStatus.UNPOPPED:
            return PopStatus.UNPOPPED

        if self.before_group.pop_status == PopStatus.RUNNING:
            return PopStatus.BLOCKING

        test_case_pop_statuses = set([test_case.pop_status for test_case in self.test_cases])

        if test_case_pop_statuses == {PopStatus.RUNNING, PopStatus.FINISHED}:
            return PopStatus.BLOCKING

        if test_case_pop_statuses == {PopStatus.FINISHED}:
            if self.after_group.pop_status == PopStatus.RUNNING:
                return PopStatus.BLOCKING
            if self.after_group.pop_status == PopStatus.FINISHED:
                return PopStatus.FINISHED

        return PopStatus.RUNNING

    def pop_test_unit(self):
        if self.before_group.pop_status == PopStatus.UNPOPPED:
            self.before_group.pop_status = PopStatus.RUNNING
            return self.before_group

        for test_case in self.test_cases:
            if test_case.pop_status == PopStatus.UNPOPPED:
                test_case.pop_status = PopStatus.RUNNING
                return test_case

        if self.after_group.pop_status == PopStatus.UNPOPPED:
            self.after_group.pop_status = PopStatus.RUNNING
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
        self.pop_status = PopStatus.UNPOPPED

        self.test = Test(self, test_case_ref)

        self.tags = self.test.tags
        self.group = self.test.group
        self.description = self.test.description
        self.location = self.test.location

        self.before_method = BeforeMethod(self, None)
        self.after_method = AfterMethod(self, None)
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

    def get_failed_setup_fixture(self):
        setup_fixture = self.test_group.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_method.status == TestFixtureStatus.FAILED:
            return self.before_method
        return None

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
        return self.test.elapsed_time


class TestFixture:
    def __init__(self, context, test_fixture_ref, fixture_type):
        if test_fixture_ref is None:
            self.context = context
            self.is_empty = True
            self.pop_status = PopStatus.UNPOPPED
            self.status = TestFixtureStatus.NOT_RUN
            return
        self.context = context
        self.test_fixture_ref = test_fixture_ref
        self.fixture_type = fixture_type
        self.status = TestFixtureStatus.NOT_RUN
        self.is_empty = False
        self.pop_status = PopStatus.UNPOPPED
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
        if self.is_empty:
            self.pop_status = PopStatus.FINISHED
            self.status = TestFixtureStatus.PASSED
            return

        from . import testexecutor
        test_fixture_executor = testexecutor.TestFixtureExecutor(self)
        self.start_time = datetime.now()
        self.status = TestFixtureStatus.RUNNING
        testexecutor.update_properties(running_test_fixture=self)
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
                testexecutor.kill_thread(test_fixture_executor)
        else:
            test_fixture_executor.join()
        testexecutor.clear_properties()
        self.pop_status = PopStatus.FINISHED
        self.end_time = datetime.now()

    def skip(self, caused_test_fixture):
        if self.is_empty:
            self.pop_status = PopStatus.FINISHED
            self.status = TestFixtureStatus.SKIPPED
            return

        from . import testexecutor
        from .plogger import preporter
        self.start_time = datetime.now()
        testexecutor.update_properties(running_test_fixture=self)
        self.status = TestFixtureStatus.SKIPPED
        self.skip_message = "%s failed, so skipped." % caused_test_fixture.fixture_type
        preporter.warn("%s failed, so skipped." % caused_test_fixture.fixture_type)
        testexecutor.clear_properties()
        self.pop_status = PopStatus.FINISHED
        self.end_time = datetime.now()

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class BeforeSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.BeforeSuite)
        self.test_suite = self.context
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)


class AfterSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.AfterSuite)
        self.test_suite = self.context
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


class BeforeClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.BeforeClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)


class AfterClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.AfterClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


class BeforeGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.BeforeGroup)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
            self.group = test_fixture_ref.__group__


class AfterGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.AfterGroup)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
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
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
            self.group = test_fixture_ref.__group__


class AfterMethod(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.AfterMethod)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__
            self.group = test_fixture_ref.__group__


test_suite = TestSuite("DefaultSuite")
