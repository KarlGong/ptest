import threading

from enumeration import TestClassRunMode, TestCaseStatus, NGDecoratorType


__author__ = 'karl.gong'

SECOND_MICROSECOND_CONVERSION_FACTOR = 1000000.0


class TestSuite:
    def __init__(self):
        self.test_classes = []
        self.start_time = None
        self.end_time = None
        self.__lock = threading.Lock()

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
        test_case = test_class.get_test_case(test_case_ref.__name__)
        if test_case is None:
            test_case = test_class.add_test_case(test_case_ref)
        return test_case

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
            for test_case in test_class.test_cases:
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

    def pop_test_case(self):
        self.__lock.acquire()
        current_thread_name = threading.currentThread().getName()
        try:
            for test_class in self.test_classes:
                # get the not run test cases count
                if test_class.test_case_status_count[4] == 0:
                    continue
                if test_class.run_mode == TestClassRunMode.SingleLine:
                    if test_class.run_thread == current_thread_name:
                        return test_class.pop_test_case()
                    elif test_class.run_thread is None:
                        test_class.run_thread = current_thread_name
                        return test_class.pop_test_case()
                else:
                    return test_class.pop_test_case()
            raise NoTestCaseAvailableForThisThread
        finally:
            self.__lock.release()


class NoTestCaseAvailableForThisThread(Exception):
    pass


class TestClass:
    def __init__(self, test_suite, test_class_ref):
        self.test_suite = test_suite
        self.test_cases = []
        self.name = test_class_ref.__name__
        self.full_name = test_class_ref.__full_name__
        self.run_thread = None
        self.run_mode = test_class_ref.__run_mode__
        self.description = test_class_ref.__description__


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
        return min([test_case.start_time for test_case in self.test_cases])

    @property
    def end_time(self):
        return max([test_case.start_time for test_case in self.test_cases])

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

    def pop_test_case(self):
        current_thread_name = threading.currentThread().getName()
        for test_case in self.test_cases:
            if test_case.status == TestCaseStatus.NOT_RUN:
                test_case.run_thread = current_thread_name
                test_case.status = TestCaseStatus.RUNNING
                return test_case
        return None


class TestCase:
    def __init__(self, test_class, test_case_ref):
        self.test_class = test_class
        self.name = test_case_ref.__name__
        self.full_name = "%s.%s" % (self.test_class.full_name, self.name)
        self.run_thread = None
        self.start_time = None
        self.end_time = None

        self.test = Test(self, test_case_ref)

        self.status = TestCaseStatus.NOT_RUN
        self.failure_message = ""
        self.failure_type = ""
        self.stack_trace = ""
        self.skip_message = ""
        self.tags = self.test.tags
        self.description = self.test.description

        self.before_method = None
        before_method_ref = test_case_ref.__self__.__before_method__
        if before_method_ref:
            self.before_method = BeforeMethod(self, before_method_ref)

        self.after_method = None
        after_method_ref = test_case_ref.__self__.__after_method__
        if after_method_ref:
            self.after_method = AfterMethod(self, after_method_ref)

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class TestCaseFixture:
    def __init__(self, test_case, test_fixture_ref, fixture_type):
        self.__test_fixture_ref = test_fixture_ref
        self.test_case = test_case
        self.logs = []
        self.screen_shot = None
        self.start_time = None
        self.end_time = None
        self.description = test_fixture_ref.__description__
        self.fixture_type = fixture_type

    def run(self):
        self.__test_fixture_ref.__call__()

    @property
    def html_format_logs(self):
        escaped_logs = []
        for log in self.logs:
            log = log.replace("&", "&amp;")
            log = log.replace("<", "&lt;")
            log = log.replace(">", "&gt;")
            log = log.replace(" ", "&nbsp;")
            log = log.replace('"', "&quot;")
            log = log.replace("\n", "<br/>")
            escaped_logs.append(log)
        return "<br/>".join(escaped_logs)

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class BeforeMethod(TestCaseFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestCaseFixture.__init__(self, test_case, test_fixture_ref, NGDecoratorType.BeforeMethod)


class Test(TestCaseFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestCaseFixture.__init__(self, test_case, test_fixture_ref, NGDecoratorType.Test)
        self.tags = test_fixture_ref.__tags__


class AfterMethod(TestCaseFixture):
    def __init__(self, test_case, test_fixture_ref):
        TestCaseFixture.__init__(self, test_case, test_fixture_ref, NGDecoratorType.AfterMethod)
        self.always_run = test_fixture_ref.__always_run__


test_suite = TestSuite()