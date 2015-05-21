import importlib
import os
import copy
from datetime import datetime
import traceback
import threading
import sys

import reporter
from config import config
from testsuite import test_suite, TestCase, TestClass, NoTestCaseAvailableForThisThread
from enumeration import NGDecoratorType, TestCaseStatus
import plogger
import screencapturer
from plogger import pconsole


__author__ = 'karl.gong'


def get_test_cases(test_target, test_class_filter_group, test_case_filter_group):
    # make deep copies for filter group
    test_class_filter_group = copy.deepcopy(test_class_filter_group)
    test_case_filter_group = copy.deepcopy(test_case_filter_group)
    try:
        module_ref = importlib.import_module(test_target)
        if "__init__.py" in module_ref.__file__:
            # test target is package
            __get_test_cases_in_package(module_ref, test_class_filter_group, test_case_filter_group)
        else:
            # test target is module
            __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
    except ImportError:
        splitted_test_target = test_target.split(".")
        if len(splitted_test_target) < 2:
            raise ImportTestTargetError("Cannot import test target: %s" % test_target)
        try:
            # test target is class
            module_ref = importlib.import_module(".".join(splitted_test_target[:-1]))
            test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-1]))
            __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
        except ImportError:
            splitted_test_target = test_target.split(".")
            if len(splitted_test_target) < 3:
                raise ImportTestTargetError("Cannot import test target: %s" % test_target)
            try:
                # test target is method
                module_ref = importlib.import_module(".".join(splitted_test_target[:-2]))
                test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-2]))
                test_case_filter_group.append_filter(TestCaseNameFilter(splitted_test_target[-1]))
                __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
            except ImportError:
                raise ImportTestTargetError("Cannot import test target: %s" % test_target)


def __get_test_cases_in_package(package_ref, class_filter_group, method_filter_group):
    package_name = package_ref.__name__
    package_path, _ = os.path.split(package_ref.__file__)
    for fn in os.listdir(package_path):
        file_full_name = os.path.join(package_path, fn)
        if os.path.isdir(file_full_name) and "__init__.py" in os.listdir(file_full_name):
            __get_test_cases_in_package(importlib.import_module(package_name + "." + fn), class_filter_group,
                                        method_filter_group)
        elif os.path.isfile(file_full_name):
            file_name, file_ext = os.path.splitext(fn)
            if fn != "__init__.py" and file_ext == ".py":
                __get_test_cases_in_module(importlib.import_module(package_name + "." + file_name), class_filter_group,
                                           method_filter_group)


def __get_test_cases_in_module(module_ref, class_filter_group, method_filter_group):
    test_class_refs = []
    for module_element in dir(module_ref):
        test_class_ref = getattr(module_ref, module_element)
        try:
            ng_type = test_class_ref.__ng_type__
            is_enabled = test_class_ref.__enabled__
        except AttributeError:
            continue
        if ng_type == NGDecoratorType.TestClass and is_enabled and class_filter_group.filter(test_class_ref):
            test_class_refs.append(test_class_ref)
    if len(test_class_refs) != 0:
        for test_class_ref in test_class_refs:
            __get_test_cases_in_class(test_class_ref, method_filter_group)


def __get_test_cases_in_class(test_class_ref, method_filter_group):
    test_case_refs = []
    for class_element in dir(test_class_ref):
        test_case_ref = getattr(test_class_ref, class_element)
        try:
            ng_type = test_case_ref.__ng_type__
            is_enabled = test_case_ref.__enabled__
        except AttributeError:
            continue
        if ng_type == NGDecoratorType.Test and is_enabled and method_filter_group.filter(test_case_ref):
            test_case_refs.append(getattr(test_class_ref(), class_element))
    if len(test_case_refs) != 0:
        for test_case_ref in test_case_refs:
            test_suite.add_test_case(test_class_ref, test_case_ref)


class ImportTestTargetError(Exception):
    pass


class FilterGroup:
    def __init__(self):
        self.__filters = []

    def filter(self, attr_ref):
        if self.__filters is None or len(self.__filters) == 0:
            return True
        for ft in self.__filters:
            if not ft.filter(attr_ref):
                return False
        return True

    def append_filter(self, filter):
        self.__filters.append(filter)

    def __str__(self):
        filter_strs = []
        for ft in self.__filters:
            filter_strs.append(str(ft))
        return " ".join(filter_strs)


class TestClassNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, class_ref):
        if self._name is None or self._name == class_ref.__name__:
            return True
        return False


class TestCaseNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, method_ref):
        if self._name is None or self._name == method_ref.__name__:
            return True
        return False


class TestCaseIncludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, method_ref):
        return self._tags is None or len([val for val in self._tags if val in method_ref.__tags__]) != 0

    def __str__(self):
        return "Include Tags: %s" % self._tags


class TestCaseExcludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, method_ref):
        return self._tags is None or len([val for val in self._tags if val in method_ref.__tags__]) == 0

    def __str__(self):
        return "Exclude Tags: %s" % self._tags


class Test_Executor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__properties = {}

    def run(self):
        while True:
            try:
                test_case = test_suite.pop_test_case()
            except NoTestCaseAvailableForThisThread:
                break
            test_case_name = test_case.name
            test_class_full_name = test_case.test_class.full_name
            test_case_full_name = test_case.full_name
            logger_filler = "-" * (100 - len(test_case_full_name) - 6)

            before_method = test_case.before_method
            test = test_case.test
            after_method = test_case.after_method

            test_case.start_time = datetime.now()
            is_before_method_failed = False
            # before method
            if before_method is not None:
                self.update_properties(test_class=test_class_full_name, test_case=test_case_name,
                                       test_case_fixture=NGDecoratorType.BeforeMethod)
                before_method.start_time = datetime.now()
                try:
                    before_method.run()
                except Exception as e:
                    # before method failed
                    is_before_method_failed = True
                    plogger.warn("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                    screencapturer.take_screen_shot()
                before_method.end_time = datetime.now()

            # test  case
            self.update_properties(test_class=test_class_full_name, test_case=test_case_name,
                                   test_case_fixture=NGDecoratorType.Test)
            test.start_time = datetime.now()
            if is_before_method_failed:
                # skip test case
                plogger.warn("@%s failed, so skipped." % NGDecoratorType.BeforeMethod)
                pconsole.warning("%s%s|SKIP|" % (test_case_full_name, logger_filler))
                test_case.status = TestCaseStatus.SKIPPED
                test_case.skip_message = "@%s failed, so skipped." % NGDecoratorType.BeforeMethod
            else:
                # run test case
                try:
                    test.run()
                    pconsole.info("%s%s|PASS|" % (test_case_full_name, logger_filler))
                    test_case.status = TestCaseStatus.PASSED
                except Exception as e:
                    plogger.warn("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                    screencapturer.take_screen_shot()
                    pconsole.warning("%s%s|FAIL|" % (test_case_full_name, logger_filler))
                    test_case.status = TestCaseStatus.FAILED
                    test_case.failure_message = e.message
                    test_case.failure_type = e.__class__.__name__
                    test_case.stack_trace = traceback.format_exc()
            test.end_time = datetime.now()

            # after method
            if after_method is not None:
                self.update_properties(test_class=test_class_full_name, test_case=test_case_name,
                                       test_case_fixture=NGDecoratorType.AfterMethod)
                after_method.start_time = datetime.now()
                if not is_before_method_failed or after_method.always_run:
                    # run after method
                    try:
                        after_method.run()
                    except Exception as e:
                        plogger.warn("Failed with following message:\n%s\n%s" % (e.message, traceback.format_exc()))
                        screencapturer.take_screen_shot()
                else:
                    # skip after method
                    plogger.warn("@%s failed, so skipped." % NGDecoratorType.BeforeMethod)
                after_method.end_time = datetime.now()
            test_case.end_time = datetime.now()

    def update_properties(self, **kwargs):
        self.__properties.update(kwargs)

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None


def run_test_cases(test_executor_number):
    test_executors = []
    for _ in range(test_executor_number):
        test_executors.append(Test_Executor())

    # set start time
    test_suite.start_time = datetime.now()

    for test_executor in test_executors:
        test_executor.start()

    for test_executor in test_executors:
        test_executor.join()

    # set end time
    test_suite.end_time = datetime.now()


def main(args=sys.argv):
    # load config
    config.load(args)

    pconsole.info("Starting ptest...")

    # config nglogger
    plogger.pconsole_verbose = config.get_option("verbose")

    # add workspace to python path
    workspace = os.path.join(os.getcwd(), config.get_option("workspace"))
    sys.path.insert(0, workspace)
    pconsole.info("Workspace: %s" % workspace)

    # test targets
    test_targets = config.get_option("test_targets")
    if test_targets:
        pconsole.info("Test targets:")
        for test_target in test_targets.split(","):
            pconsole.info(" %s" % test_target)

    # todo:rerun failed

    # test class and test case filter
    include_tags = config.get_option("include_tags")
    exclude_tags = config.get_option("exclude_tags")
    test_class_filter_group = FilterGroup()
    test_case_filter_group = FilterGroup()
    if include_tags:
        test_case_filter_group.append_filter(TestCaseIncludeTagsFilter(include_tags.split(",")))
    if exclude_tags:
        test_case_filter_group.append_filter(TestCaseExcludeTagsFilter(exclude_tags.split(",")))
    if include_tags or exclude_tags:
        pconsole.info("=" * 100)
        pconsole.info(" %s" % test_case_filter_group)

    # get test cases
    for test_target in test_targets.split(","):
        get_test_cases(test_target, test_class_filter_group, test_case_filter_group)

    # sort the test groups for running
    test_suite.sort_test_classes_for_running()
    pconsole.info("=" * 100)
    pconsole.info("Start to run following tests:")
    pconsole.info("-" * 30)
    for test_name in test_suite.test_case_names:
        pconsole.info(" %s" % test_name)
    pconsole.info("=" * 100)

    # run test cases
    run_test_cases(config.get_option("test_executor_number"))

    # log the test results
    test_suite_total, test_suite_passed, test_suite_failed, test_suite_skipped, _ = test_suite.test_case_status_count
    pconsole.info("")
    pconsole.info("=" * 100)
    pconsole.info("Test finished in %.2fs." % test_suite.elapsed_time)
    pconsole.info("Total: %s, passed: %s, failed: %s, skipped: %s. Pass rate: %.1f%%." % (
        test_suite_total, test_suite_passed, test_suite_failed, test_suite_skipped, test_suite.pass_rate))

    # generate the test report
    output_path = os.path.join(workspace, config.get_option("output_dir"))
    pconsole.info("")
    pconsole.info("=" * 100)
    test_suite.sort_test_classes_for_report()
    reporter.clean_report_dir(output_path)
    reporter.generate_xunit_xml(os.path.join(output_path, config.get_option("xunit_xml")))
    reporter.generate_html_report(os.path.join(output_path, config.get_option("report_dir")))