import importlib
import os
import copy
from datetime import datetime
import traceback
import sys
from xml.dom import minidom

import testexecutor
import reporter
import config
from testsuite import test_suite
from enumeration import PDecoratorType
from plogger import pconsole
import plistener

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
            raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))
        try:
            # test target is class
            module_ref = importlib.import_module(".".join(splitted_test_target[:-1]))
            test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-1]))
            __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
        except ImportError:
            splitted_test_target = test_target.split(".")
            if len(splitted_test_target) < 3:
                raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))
            try:
                # test target is method
                module_ref = importlib.import_module(".".join(splitted_test_target[:-2]))
                test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-2]))
                test_case_filter_group.append_filter(TestCaseNameFilter(splitted_test_target[-1]))
                __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
            except ImportError:
                raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))


def __get_test_cases_in_package(package_ref, test_class_filter_group, test_case_filter_group):
    package_name = package_ref.__name__
    package_path, _ = os.path.split(package_ref.__file__)
    for fn in os.listdir(package_path):
        file_full_name = os.path.join(package_path, fn)
        if os.path.isdir(file_full_name) and "__init__.py" in os.listdir(file_full_name):
            __get_test_cases_in_package(importlib.import_module(package_name + "." + fn), test_class_filter_group,
                                        test_case_filter_group)
        elif os.path.isfile(file_full_name):
            file_name, file_ext = os.path.splitext(fn)
            if fn != "__init__.py" and file_ext == ".py":
                __get_test_cases_in_module(importlib.import_module(package_name + "." + file_name), test_class_filter_group,
                                           test_case_filter_group)


def __get_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group):
    test_class_refs = []
    for module_element in dir(module_ref):
        test_class_ref = getattr(module_ref, module_element)
        try:
            pd_type = test_class_ref.__pd_type__
            is_enabled = test_class_ref.__enabled__
        except AttributeError:
            continue
        if pd_type == PDecoratorType.TestClass and is_enabled and test_class_filter_group.filter(test_class_ref):
            test_class_refs.append(test_class_ref)
    if len(test_class_refs) != 0:
        for test_class_ref in test_class_refs:
            __get_test_cases_in_class(test_class_ref, test_case_filter_group)


def __get_test_cases_in_class(test_class_ref, test_case_filter_group):
    test_case_refs = []
    for class_element in dir(test_class_ref):
        test_case_ref = getattr(test_class_ref, class_element)
        try:
            pd_type = test_case_ref.__pd_type__
            is_enabled = test_case_ref.__enabled__
        except AttributeError:
            continue
        if pd_type == PDecoratorType.Test and is_enabled and test_case_filter_group.filter(test_case_ref):
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

    def filter(self, test_class_ref):
        return self._name is None or self._name == test_class_ref.__name__


class TestCaseNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, test_case_ref):
        return self._name is None or self._name == test_case_ref.__name__


class TestCaseIncludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return self._tags is None or len([val for val in self._tags if val in test_case_ref.__tags__]) != 0

    def __str__(self):
        return "Include Tags: %s" % self._tags


class TestCaseExcludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return self._tags is None or len([val for val in self._tags if val in test_case_ref.__tags__]) == 0

    def __str__(self):
        return "Exclude Tags: %s" % self._tags


def run_test_cases(test_executor_number):
    test_executors = []
    for _ in range(test_executor_number):
        test_executors.append(testexecutor.TestExecutor())

    # test suite start
    plistener.test_listener.on_test_suite_start(test_suite)
    test_suite.start_time = datetime.now()

    for test_executor in test_executors:
        test_executor.start()

    for test_executor in test_executors:
        test_executor.join()

    # test suite finish
    test_suite.end_time = datetime.now()
    plistener.test_listener.on_test_suite_finish(test_suite)


def get_rerun_targets(xml_file):
    test_targets = []
    doc = minidom.parse(xml_file)
    if doc.documentElement.nodeName == "testsuites":
        root = doc.documentElement
    else:
        root = doc
    for test_suite_node in root.getElementsByTagName("testsuite"):
        for test_case_node in test_suite_node.getElementsByTagName("testcase"):
            if test_case_node.getElementsByTagName("failure") or test_case_node.getElementsByTagName("skipped"):
                test_target = "%s.%s" % (test_case_node.getAttribute("classname"), test_case_node.getAttribute("name"))
                test_targets.append(test_target)
    return test_targets


def main(args=sys.argv):
    # load config
    config.load(args)

    pconsole.info("Starting ptest...")

    # add workspace to python path
    workspace = os.path.join(os.getcwd(), config.get_option("workspace"))
    sys.path.insert(0, workspace)
    pconsole.info("Workspace:")
    pconsole.info(" %s" % os.path.abspath(workspace))

    # get test targets
    test_targets_str = config.get_option("test_targets")
    if test_targets_str:
        test_targets = test_targets_str.split(",")
        pconsole.info("Test targets:")
        for test_target in test_targets:
            pconsole.info(" %s" % test_target)
    else:
        # rerun failed/skipped test cases
        xunit_xml = os.path.join(workspace, config.get_option("run_failed"))
        pconsole.info("Rerun failed/skipped test cases in xunit xml:")
        pconsole.info(" %s" % xunit_xml)
        test_targets = get_rerun_targets(xunit_xml)

    # test listener
    listener_path = config.get_option("listener")
    if listener_path:
        pconsole.info("Test listener:")
        pconsole.info(" %s" % listener_path)
        splitted_listener_path = listener_path.split(".")
        listener_module = importlib.import_module(".".join(splitted_listener_path[:-1]))
        listener_class = getattr(listener_module, splitted_listener_path[-1])
        plistener.test_listener = listener_class()

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
    for test_target in test_targets:
        get_test_cases(test_target, test_class_filter_group, test_case_filter_group)

    # add webdriver instance to test executor to support capturing screenshot for webdriver
    if "selenium" in sys.modules.keys():
        from selenium.webdriver.remote.webdriver import WebDriver
        def new_start_client(self):
            try:
                testexecutor.update_properties(browser=self)
            except AttributeError:
                pass
        def new_stop_client(self):
            try:
                testexecutor.update_properties(browser=None)
            except AttributeError:
                pass
        WebDriver.start_client = new_start_client
        WebDriver.stop_client = new_stop_client

    # sort the test groups for running
    test_suite.sort_test_classes_for_running()
    pconsole.info("=" * 100)
    pconsole.info("Start to run following tests:")
    pconsole.info("-" * 30)
    for test_name in test_suite.test_case_names:
        pconsole.info(" %s" % test_name)
    pconsole.info("=" * 100)

    # run test cases
    run_test_cases(int(config.get_option("test_executor_number")))

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
