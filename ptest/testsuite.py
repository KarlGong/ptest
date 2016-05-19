from functools import cmp_to_key

from .enumeration import PDecoratorType, TestFixtureStatus, TestCaseCountItem, TestClassRunMode

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class TestContainer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.test_cases = []

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        return time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR

    @property
    def status_count(self):
        status_count_dict = {
            TestCaseCountItem.TOTAL: 0,
            TestCaseCountItem.PASSED: 0,
            TestCaseCountItem.FAILED: 0,
            TestCaseCountItem.SKIPPED: 0,
            TestCaseCountItem.NOT_RUN: 0
        }
        for test_case in self.test_cases:
            status_count_dict[TestCaseCountItem.TOTAL] += 1
            status_count_dict[test_case.status] += 1
        return status_count_dict

    @property
    def pass_rate(self):
        status_count = self.status_count
        return float(status_count[TestCaseCountItem.PASSED]) * 100 / status_count[TestCaseCountItem.TOTAL]


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
                try:
                    if attr.__enabled__:
                        if attr.__pd_type__ == PDecoratorType.BeforeSuite:
                            self.before_suite = BeforeSuite(self, attr)
                        elif attr.__pd_type__ == PDecoratorType.AfterSuite:
                            self.after_suite = AfterSuite(self, attr)
                except AttributeError as e:
                    pass

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
            run_groups.append(sorted(run_group, key=lambda test_class: test_class.run_mode, reverse=True))

        # sort the test class run groups by its size and number of singleline test classes
        def cmp_run_group(run_group_a, run_group_b):
            if not len(run_group_a) == len(run_group_b):
                return len(run_group_a) - len(run_group_b)
            else:
                return len([test_class for test_class in run_group_a if test_class.run_mode == TestClassRunMode.SingleLine]) - \
                       len([test_class for test_class in run_group_b if test_class.run_mode == TestClassRunMode.SingleLine])

        self.test_class_run_groups = sorted(run_groups, key=cmp_to_key(cmp_run_group), reverse=True)

    def get_failed_setup_fixture(self):
        if self.before_suite.status == TestFixtureStatus.FAILED:
            return self.before_suite
        return None

    def get_test_class(self, full_name):
        for test_class in self.test_classes:
            if test_class.full_name == full_name:
                return test_class
        return None

    def add_test_case(self, test_case_ref):
        test_class_ref = test_case_ref.__self__.__class__
        # for the @TestClass can be inherited, so set full name here
        test_class_ref.__full_name__ = "%s.%s" % (test_class_ref.__module__, test_class_ref.__name__)
        test_class = self.get_test_class(test_class_ref.__full_name__)
        if test_class is None:
            test_class = TestClass(self, test_class_ref())
            self.test_classes.append(test_class)

        test_group = test_class.get_test_group(test_case_ref.__group__)
        if test_group is None:
            test_group = TestGroup(test_class, test_case_ref.__group__, test_class_ref())
            test_class.test_groups.append(test_group)

        test_case = test_group.get_test_case(test_case_ref.__name__)
        if test_case is None:
            test_case = TestCase(test_group, test_case_ref)
            test_group.test_cases.append(test_case)
            test_class.test_cases.append(test_case)
            self.test_cases.append(test_case)
            return True
        return False


class TestClass(TestContainer):
    def __init__(self, test_suite, test_class_ref):
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
            try:
                if attr.__enabled__:
                    if attr.__pd_type__ == PDecoratorType.BeforeClass:
                        self.before_class = BeforeClass(self, attr)
                    elif attr.__pd_type__ == PDecoratorType.AfterClass:
                        self.after_class = AfterClass(self, attr)
            except AttributeError as e:
                pass

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

    @property
    def is_group_feature_used(self):
        return not (len(self.test_groups) == 1 and self.test_groups[0].name == "DEFAULT" and self.test_groups[
            0].before_group.is_empty and self.test_groups[0].after_group.is_empty)


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
                if attr.__enabled__ and attr.__group__ == self.name:
                    if attr.__pd_type__ == PDecoratorType.BeforeGroup:
                        self.before_group = BeforeGroup(self, attr)
                    elif attr.__pd_type__ == PDecoratorType.AfterGroup:
                        self.after_group = AfterGroup(self, attr)
            except AttributeError as e:
                pass

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
        self.full_name = "%s.%s" % (self.test_class.full_name, self.name)
        self.start_time = None
        self.end_time = None

        self.test = Test(self, test_case_ref)

        self.tags = self.test.tags
        self.expected_exceptions = self.test.expected_exceptions
        self.data = self.test.data
        self.group = self.test.group
        self.description = self.test.description
        self.custom_args = self.test.custom_args
        self.location = self.test.location

        self.before_method = BeforeMethod(self, None)
        self.after_method = AfterMethod(self, None)
        # reflect the before method and after method
        for element in dir(test_case_ref.__self__):
            attr = getattr(test_case_ref.__self__, element)
            try:
                if attr.__enabled__ and attr.__group__ == self.group:
                    if attr.__pd_type__ == PDecoratorType.BeforeMethod:
                        self.before_method = BeforeMethod(self, attr)
                    elif attr.__pd_type__ == PDecoratorType.AfterMethod:
                        self.after_method = AfterMethod(self, attr)
            except AttributeError as e:
                pass

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
        self.screenshots = []
        self.description = test_fixture_ref.__description__
        self.timeout = test_fixture_ref.__timeout__
        self.custom_args = test_fixture_ref.__custom_args__
        self.location = test_fixture_ref.__location__
        self.arguments_count = test_fixture_ref.__arguments_count__

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


class BeforeClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.BeforeClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)


class BeforeGroup(TestFixture):
    def __init__(self, test_group, test_fixture_ref):
        TestFixture.__init__(self, test_group, test_fixture_ref, PDecoratorType.BeforeGroup)
        self.test_group = self.context
        self.test_class = self.test_group.test_class
        self.test_suite = self.test_group.test_suite
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_group.full_name, self.fixture_type)
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


class Test(TestFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestFixture.__init__(self, test_case, test_fixture_ref, PDecoratorType.Test)
        self.full_name = "%s@%s" % (test_case.full_name, self.fixture_type)
        self.test_case = self.context
        self.test_group = self.test_case.test_group
        self.test_class = self.test_case.test_class
        self.test_suite = self.test_case.test_suite
        self.tags = test_fixture_ref.__tags__
        self.expected_exceptions = test_fixture_ref.__expected_exceptions__
        self.data = test_fixture_ref.__data__
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


class AfterClass(TestFixture):
    def __init__(self, test_class, test_fixture_ref):
        TestFixture.__init__(self, test_class, test_fixture_ref, PDecoratorType.AfterClass)
        self.test_class = self.context
        self.test_suite = self.test_class.test_suite
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_class.full_name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


class AfterSuite(TestFixture):
    def __init__(self, test_suite, test_fixture_ref):
        TestFixture.__init__(self, test_suite, test_fixture_ref, PDecoratorType.AfterSuite)
        self.test_suite = self.context
        self.always_run = False
        if not self.is_empty:
            self.full_name = "%s@%s" % (test_suite.name, self.fixture_type)
            self.always_run = test_fixture_ref.__always_run__


default_test_suite = TestSuite("DefaultSuite")
