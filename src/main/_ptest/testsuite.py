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

    def add_test_class(self, test_class_ref):
        self.test_classes.append(TestClass(self, test_class_ref))

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
    def __init__(self, test_suite, inner_class):
        self.test_cases = []
        self.test_suite = test_suite
        self.run_thread = None
        self.run_mode = inner_class.__run_mode__
        self.description = inner_class.__description__
        self.full_name = "%s.%s" % (inner_class.__module__, inner_class.__name__)

    def get_test_case(self, name):
        for test_case in self.test_cases:
            if test_case.name == name:
                return test_case
        return None

    def add_test_case(self, test_case):
        test_case.test_class = self
        self.test_cases.append(test_case)

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
    def __init__(self, inner_func):
        self.test_class = None
        self.name = inner_func.__name__
        self.run_thread = None
        self.start_time = None
        self.end_time = None

        self.test = Test(inner_func)

        self.status = TestCaseStatus.NOT_RUN
        self.failure_message = ""
        self.failure_type = ""
        self.stack_trace = ""
        self.skip_message = ""
        self.tags = self.test.tags
        self.description = self.test.description

        self.before_method = None
        before_method_func = inner_func.__self__.__before_method__
        if before_method_func:
            self.before_method = BeforeMethod(before_method_func)

        self.after_method = None
        after_method_func = inner_func.__self__.__after_method__
        if after_method_func:
            self.after_method = AfterMethod(after_method_func)

    @property
    def full_name(self):
        return "%s.%s" % (self.test_class.full_name, self.name)

    @property
    def elapsed_time(self):
        time_delta = self.end_time - self.start_time
        seconds = time_delta.seconds + time_delta.microseconds / SECOND_MICROSECOND_CONVERSION_FACTOR
        return seconds


class TestCaseFixture:
    def __init__(self, inner_func, fixture_type):
        self.__inner_func = inner_func
        self.logs = []
        self.screen_shot = None
        self.start_time = None
        self.end_time = None
        self.description = inner_func.__description__
        self.fixture_type = fixture_type

    def run(self):
        self.__inner_func.__call__()

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
    def __init__(self, inner_func):
        TestCaseFixture.__init__(self, inner_func, NGDecoratorType.BeforeMethod)


class Test(TestCaseFixture):
    def __init__(self, inner_func):
        TestCaseFixture.__init__(self, inner_func, NGDecoratorType.Test)
        self.tags = inner_func.__tags__


class AfterMethod(TestCaseFixture):
    def __init__(self, inner_func):
        TestCaseFixture.__init__(self, inner_func, NGDecoratorType.AfterMethod)
        self.always_run = inner_func.__always_run__


test_suite = TestSuite()