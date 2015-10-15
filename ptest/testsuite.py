import os

try:
    from urlparse import urljoin
    from urllib import unquote, pathname2url
except ImportError:
    from urllib.parse import urljoin, unquote
    from urllib.request import pathname2url
import inspect
import threading

from .enumeration import TestCaseStatus, PDecoratorType, TestFixtureStatus

__author__ = 'karl.gong'

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class TestContainer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.is_finished = False
        self.test_cases = []

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR

    @property
    def status_count(self):
        status_count_dict = {
            "total": 0,
            TestCaseStatus.PASSED: 0,
            TestCaseStatus.FAILED: 0,
            TestCaseStatus.SKIPPED: 0,
            TestCaseStatus.NOT_RUN: 0
        }
        for test_case in self.test_cases:
            status_count_dict["total"] += 1
            status_count_dict[test_case.status] += 1
        return status_count_dict

    @property
    def pass_rate(self):
        status_count = self.status_count
        total = status_count["total"]
        if total == 0:
            return 0
        return float(status_count["passed"]) * 100 / total


class TestSuite(TestContainer):
    def __init__(self, name):
        TestContainer.__init__(self)
        self.test_classes = []
        self.name = name
        self.full_name = name
        self.before_suite = BeforeSuite(self, None)
        self.after_suite = AfterSuite(self, None)
        self.__lock = threading.Lock()

    def init_test_fixture(self):
        # reflect the before suite and after suite
        for test_class in self.test_classes:
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

    def add_test_case(self, test_class_ref, test_case_ref):
        test_class = self.get_test_class(test_class_ref.__full_name__)
        if test_class is None:
            test_class = TestClass(self, test_class_ref)
            self.test_classes.append(test_class)
        test_group = test_class.get_test_group(test_case_ref.__group__)
        if test_group is None:
            test_group = TestGroup(test_class, test_case_ref.__group__, test_class_ref)
            test_class.test_groups.append(test_group)
        test_case = test_group.get_test_case(test_case_ref.__name__)
        if test_case is None:
            test_case = TestCase(test_group, test_case_ref)
            test_group.test_cases.append(test_case)
            test_class.test_cases.append(test_case)
            self.test_cases.append(test_case)

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


class TestClass(TestContainer):
    def __init__(self, test_suite, test_class_ref):
        TestContainer.__init__(self)
        self.test_suite = test_suite
        self.test_class_ref = test_class_ref
        self.test_groups = []
        self.name = test_class_ref.__class__.__name__
        self.full_name = test_class_ref.__full_name__
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


class TestGroup(TestContainer):
    def __init__(self, test_class, name, test_class_ref):
        TestContainer.__init__(self)
        self.test_class = test_class
        self.test_suite = self.test_class.test_suite
        self.test_class_ref = test_class_ref
        self.test_cases = []
        self.name = name
        self.full_name = "%s(%s)" % (test_class.full_name, name)

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
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR


class TestFixture:
    def __init__(self, context, test_fixture_ref, fixture_type):
        self.context = context
        self.fixture_type = fixture_type
        self.status = TestFixtureStatus.NOT_RUN
        if test_fixture_ref is None:
            self.is_empty = True
            return
        self.is_empty = False
        self.test_fixture_ref = test_fixture_ref
        self.name = test_fixture_ref.__name__
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

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class BeforeSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.BeforeSuite)
        self.execution_priority = 8
        self.test_suite = self.context
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)


class BeforeClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.BeforeClass)
        self.execution_priority = 7
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)


class BeforeGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.BeforeGroup)
        self.execution_priority = 6
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
            self.group = test_fixture_ref.__group__


class BeforeMethod(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.BeforeMethod)
        self.execution_priority = 5
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
            self.group = test_fixture_ref.__group__


class Test(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.Test)
        self.execution_priority = 4
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.tags = test_fixture_ref.__tags__
        self.group = test_fixture_ref.__group__


class AfterMethod(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.AfterMethod)
        self.execution_priority = 3
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__
            self.group = test_fixture_ref.__group__


class AfterGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.AfterGroup)
        self.execution_priority = 2
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__
            self.group = test_fixture_ref.__group__


class AfterClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.AfterClass)
        self.execution_priority = 1
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


class AfterSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.AfterSuite)
        self.execution_priority = 0
        self.test_suite = self.context
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


default_test_suite = TestSuite("DefaultSuite")
