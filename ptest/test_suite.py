import types
from functools import cmp_to_key

from .enumeration import PDecoratorType, TestFixtureStatus, TestClassRunMode, TestCaseStatus

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class StatusCount:
    def __init__(self):
        self.total = 0
        self.not_run = 0
        self.running = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0


class TestContainer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.test_cases = []

    @property
    def elapsed_time(self) -> float:
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR

    @property
    def status_count(self) -> StatusCount:
        count = StatusCount()
        for test_case in self.test_cases:
            count.total += 1
            if test_case.status == TestCaseStatus.NOT_RUN:
                count.not_run += 1
            elif test_case.status == TestCaseStatus.RUNNING:
                count.running += 1
            elif test_case.status == TestCaseStatus.PASSED:
                count.passed += 1
            elif test_case.status == TestCaseStatus.FAILED:
                count.failed += 1
            elif test_case.status == TestCaseStatus.SKIPPED:
                count.skipped += 1
        return count

    @property
    def pass_rate(self) -> float:
        status_count = self.status_count
        return float(status_count.passed) * 100 / status_count.total


class TestSuite(TestContainer):
    def __init__(self, name):
        TestContainer.__init__(self)
        self.test_classes = []
        self.test_class_run_groups = []
        self.name = name
        self.full_name = name
        self.before_suite = BeforeSuite(self, None)
        self.after_suite = AfterSuite(self, None)

    def init(self):
        self.init_test_fixtures()
        self.init_test_class_run_groups()
        self.sort_test_class_run_groups()

    def init_test_fixtures(self):
        # reflect the before suite and after suite
        for test_class in self.test_classes:
            test_class_ref = test_class.test_class_ref.__class__()
            for element in dir(test_class_ref):
                attr = getattr(test_class_ref, element)
                if hasattr(attr, "__enabled__") and attr.__enabled__ \
                        and hasattr(attr, "__pd_type__"):
                    if attr.__pd_type__ == PDecoratorType.BeforeSuite:
                        self.before_suite = BeforeSuite(self, attr)
                    elif attr.__pd_type__ == PDecoratorType.AfterSuite:
                        self.after_suite = AfterSuite(self, attr)

    def init_test_class_run_groups(self):
        run_groups = {}
        run_group_index = 0
        for test_class in self.test_classes:
            if test_class.run_group is None:
                run_groups[run_group_index] = [test_class]
                run_group_index += 1
            elif test_class.run_group in run_groups:
                run_groups[test_class.run_group].append(test_class)
            else:
                run_groups[test_class.run_group] = [test_class]
        self.test_class_run_groups = run_groups.values()

    def sort_test_class_run_groups(self):
        run_groups = []
        # sort the test classes in run group by its run mode
        for run_group in self.test_class_run_groups:
            run_groups.append(sorted(run_group, key=lambda test_class: test_class.run_mode.value, reverse=True))

        # sort the test class run groups by its number of singleline test cases
        def cmp_run_group(run_group_a, run_group_b):
            single_line_count_a = single_line_count_b = parallel_count_a = parallel_count_b = 0
            for test_class in run_group_a:
                if test_class.run_mode == TestClassRunMode.SingleLine:
                    single_line_count_a += len(test_class.test_cases)
                else:
                    parallel_count_a += len(test_class.test_cases)

            for test_class in run_group_b:
                if test_class.run_mode == TestClassRunMode.SingleLine:
                    single_line_count_b += len(test_class.test_cases)
                else:
                    parallel_count_b += len(test_class.test_cases)

            if single_line_count_a == single_line_count_b:
                return parallel_count_a - parallel_count_b
            else:
                return single_line_count_a - single_line_count_b

        self.test_class_run_groups = sorted(run_groups, key=cmp_to_key(cmp_run_group), reverse=True)

    def get_failed_setup_fixture(self):
        if self.before_suite.status == TestFixtureStatus.FAILED:
            return self.before_suite
        return None

    def get_test_class(self, full_name: str):
        for test_class in self.test_classes:
            if test_class.full_name == full_name:
                return test_class
        return None

    def add_test_case(self, test_class_cls, test_case_func):
        # for the @TestClass can be inherited, so set full name here
        test_class_cls.__full_name__ = "%s.%s" % (test_class_cls.__module__, test_class_cls.__name__)
        test_class = self.get_test_class(test_class_cls.__full_name__)
        if test_class is None:
            test_class = TestClass(self, test_class_cls())
            self.test_classes.append(test_class)

        test_group = test_class.get_test_group(test_case_func.__group__)
        if test_group is None:
            test_group = TestGroup(test_class, test_case_func.__group__, test_class_cls())
            test_class.test_groups.append(test_group)

        test_case = test_group.get_test_case(test_case_func.__name__)
        if test_case is None:
            if hasattr(test_class_cls, test_case_func.__name__):  # normal
                test_case = TestCase(test_group, getattr(test_class_cls(), test_case_func.__name__))
            else:  # mocked
                test_class_ref = test_class_cls()
                mock_method = types.MethodType(test_case_func, test_class_ref)
                setattr(test_class_ref, test_case_func.__name__, mock_method)
                test_case = TestCase(test_group, mock_method)
            test_group.test_cases.append(test_case)
            test_class.test_cases.append(test_case)
            self.test_cases.append(test_case)
            return True
        return False


class TestClass(TestContainer):
    def __init__(self, test_suite: TestSuite, test_class_ref):
        TestContainer.__init__(self)
        self.test_suite = test_suite
        self.test_class_ref = test_class_ref
        self.test_groups = []
        self.name = test_class_ref.__class__.__name__
        self.full_name = test_class_ref.__full_name__
        self.run_mode = test_class_ref.__run_mode__
        self.run_group = test_class_ref.__run_group__
        self.description = test_class_ref.__description__
        self.custom_args = test_class_ref.__custom_args__

        self.before_class = BeforeClass(self, None)
        self.after_class = AfterClass(self, None)
        # reflect the before class and after class
        for element in dir(test_class_ref):
            attr = getattr(test_class_ref, element)
            if hasattr(attr, "__enabled__") and attr.__enabled__ \
                    and hasattr(attr, "__pd_type__"):
                if attr.__pd_type__ == PDecoratorType.BeforeClass:
                    self.before_class = BeforeClass(self, attr)
                elif attr.__pd_type__ == PDecoratorType.AfterClass:
                    self.after_class = AfterClass(self, attr)

    def get_failed_setup_fixture(self) -> "TestFixture":
        setup_fixture = self.test_suite.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_class.status == TestFixtureStatus.FAILED:
            return self.before_class
        return None

    def get_test_group(self, name: str) -> "TestGroup":
        for test_group in self.test_groups:
            if test_group.name == name:
                return test_group
        return None

    @property
    def is_group_feature_used(self) -> bool:
        return not (len(self.test_groups) == 1 and self.test_groups[0].name == "DEFAULT" and self.test_groups[
            0].before_group.is_empty and self.test_groups[0].after_group.is_empty)


class TestGroup(TestContainer):
    def __init__(self, test_class: TestClass, name: str, test_class_ref):
        TestContainer.__init__(self)
        self.test_class = test_class
        self.test_suite = self.test_class.test_suite
        self.test_class_ref = test_class_ref
        self.test_cases = []
        self.name = name
        self.full_name = "%s<%s>" % (test_class.full_name, name)

        self.before_group = BeforeGroup(self, None)
        self.after_group = AfterGroup(self, None)
        # reflect the before group and after group
        for element in dir(test_class_ref):
            attr = getattr(test_class_ref, element)
            if hasattr(attr, "__enabled__") and attr.__enabled__ \
                    and hasattr(attr, "__group__") and attr.__group__ == self.name \
                    and hasattr(attr, "__pd_type__"):
                if attr.__pd_type__ == PDecoratorType.BeforeGroup:
                    self.before_group = BeforeGroup(self, attr)
                elif attr.__pd_type__ == PDecoratorType.AfterGroup:
                    self.after_group = AfterGroup(self, attr)

    def get_failed_setup_fixture(self) -> "TestFixture":
        setup_fixture = self.test_class.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_group.status == TestFixtureStatus.FAILED:
            return self.before_group
        return None

    def get_test_case(self, name: str) -> "TestCase":
        for test_case in self.test_cases:
            if test_case.name == name:
                return test_case
        return None


class TestCase:
    def __init__(self, test_group: TestGroup, test_case_ref):
        self.test_group = test_group
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_class.test_suite
        self.test_case_ref = test_case_ref
        self.name = test_case_ref.__name__
        self.full_name = "%s.%s" % (self.test_class.full_name, self.name)
        self.start_time = None
        self.end_time = None

        self.test = Test(self, test_case_ref)

        self.tags = self.test.tags
        self.expected_exceptions = self.test.expected_exceptions
        self.parameters = self.test.parameters
        self.data_index = self.test.data_index
        self.group = self.test.group
        self.description = self.test.description
        self.custom_args = self.test.custom_args
        self.location = self.test.location

        self.before_method = BeforeMethod(self, None)
        self.after_method = AfterMethod(self, None)
        # reflect the before method and after method
        for element in dir(test_case_ref.__self__):
            attr = getattr(test_case_ref.__self__, element)
            if hasattr(attr, "__enabled__") and attr.__enabled__ \
                    and hasattr(attr, "__group__") and attr.__group__ == self.group \
                    and hasattr(attr, "__pd_type__"):
                if attr.__pd_type__ == PDecoratorType.BeforeMethod:
                    self.before_method = BeforeMethod(self, attr)
                elif attr.__pd_type__ == PDecoratorType.AfterMethod:
                    self.after_method = AfterMethod(self, attr)

    def get_failed_setup_fixture(self) -> "TestFixture":
        setup_fixture = self.test_group.get_failed_setup_fixture()
        if setup_fixture:
            return setup_fixture
        if self.before_method.status == TestFixtureStatus.FAILED:
            return self.before_method
        return None

    @property
    def failure_message(self) -> str:
        return self.test.failure_message

    @property
    def failure_type(self) -> str:
        return self.test.failure_type

    @property
    def stack_trace(self) -> str:
        return self.test.stack_trace

    @property
    def skip_message(self) -> str:
        return self.test.skip_message

    @property
    def status(self) -> TestCaseStatus:
        status_map = {
            TestFixtureStatus.NOT_RUN: TestCaseStatus.NOT_RUN,
            TestFixtureStatus.RUNNING: TestCaseStatus.RUNNING,
            TestFixtureStatus.PASSED: TestCaseStatus.PASSED,
            TestFixtureStatus.SKIPPED: TestCaseStatus.SKIPPED,
            TestFixtureStatus.FAILED: TestCaseStatus.FAILED,
        }
        return status_map[self.test.status]

    @property
    def elapsed_time(self) -> float:
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR


class TestFixture:
    def __init__(self, context, test_fixture_ref, fixture_type: PDecoratorType):
        self.context = context
        self.fixture_type = fixture_type
        self.is_empty = False
        self.status = TestFixtureStatus.NOT_RUN
        if test_fixture_ref is None:
            self.is_empty = True
            return
        self.test_fixture_ref = test_fixture_ref
        self.name = test_fixture_ref.__name__
        self.full_name = ""
        self.failure_message = ""
        self.failure_type = ""
        self.stack_trace = ""
        self.skip_message = ""
        self.start_time = None
        self.end_time = None
        self.logs = []
        self.description = test_fixture_ref.__description__
        self.timeout = test_fixture_ref.__timeout__
        self.custom_args = test_fixture_ref.__custom_args__
        self.location = test_fixture_ref.__location__
        self.parameters_count = test_fixture_ref.__parameters_count__

    @property
    def elapsed_time(self) -> float:
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR


class BeforeSuite(TestFixture):
    def __init__(self, test_suite: TestSuite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.BeforeSuite)
        self.test_suite = self.context
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type.value)


class BeforeClass(TestFixture):
    def __init__(self, test_class: TestClass, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.BeforeClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type.value)


class BeforeGroup(TestFixture):
    def __init__(self, test_group: TestGroup, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.BeforeGroup)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type.value)
            self.group = test_fixture_ref.__group__


class BeforeMethod(TestFixture):
    def __init__(self, test_case: TestCase, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.BeforeMethod)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type.value)
            self.group = test_fixture_ref.__group__


class Test(TestFixture):
    def __init__(self, test_case: TestCase, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.Test)
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type.value)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.tags = test_fixture_ref.__tags__
        self.expected_exceptions = test_fixture_ref.__expected_exceptions__
        self.parameters = test_fixture_ref.__parameters__
        self.data_index = test_fixture_ref.__data_index__
        self.group = test_fixture_ref.__group__


class AfterMethod(TestFixture):
    def __init__(self, test_case: TestCase, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.AfterMethod)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type.value)
            self.always_run = test_fixture_ref.__always_run__
            self.group = test_fixture_ref.__group__


class AfterGroup(TestFixture):
    def __init__(self, test_group: TestGroup, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.AfterGroup)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type.value)
            self.always_run = test_fixture_ref.__always_run__
            self.group = test_fixture_ref.__group__


class AfterClass(TestFixture):
    def __init__(self, test_class: TestClass, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.AfterClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type.value)
            self.always_run = test_fixture_ref.__always_run__


class AfterSuite(TestFixture):
    def __init__(self, test_suite: TestSuite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.AfterSuite)
        self.test_suite = self.context
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type.value)
            self.always_run = test_fixture_ref.__always_run__


default_test_suite = TestSuite("DefaultSuite")
