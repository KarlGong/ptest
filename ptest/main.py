import importlib
import os
import copy
from datetime import datetime
import shlex
import traceback
import sys
from xml.dom import minidom

from testfilter import FilterGroup, TestClassNameFilter, TestCaseNameFilter, TestCaseIncludeTagsFilter, \
    TestCaseExcludeTagsFilter, TestCaseIncludeGroupsFilter
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


class ImportTestTargetError(Exception):
    pass


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


def main(args=None):
    # load arguments
    if args is None:
        args = sys.argv[1:]
    elif not isinstance(args, (tuple, list)):
        if not isinstance(args, str):
            sys.stderr.write("ERROR: args <%s> is not a string or argument list." % (args,))
            return
        args = shlex.split(args)
    config.load(args)

    pconsole.write_line("Starting ptest...")

    # add workspace to python path
    workspace = os.path.join(os.getcwd(), config.get_option("workspace"))
    sys.path.insert(0, workspace)
    pconsole.write_line("Workspace:")
    pconsole.write_line(" %s" % os.path.abspath(workspace))

    # get test targets
    test_targets_str = config.get_option("test_targets")
    if test_targets_str:
        test_targets = test_targets_str.split(",")
        pconsole.write_line("Test targets:")
        for test_target in test_targets:
            pconsole.write_line(" %s" % test_target)
    else:
        # rerun failed/skipped test cases
        xunit_xml = os.path.join(workspace, config.get_option("run_failed"))
        pconsole.write_line("Run failed/skipped test cases in xunit xml:")
        pconsole.write_line(" %s" % os.path.abspath(xunit_xml))
        test_targets = get_rerun_targets(xunit_xml)

    # test listener
    listener_path = config.get_option("listener")
    if listener_path:
        pconsole.write_line("Test listener:")
        pconsole.write_line(" %s" % listener_path)
        splitted_listener_path = listener_path.split(".")
        listener_module = importlib.import_module(".".join(splitted_listener_path[:-1]))
        listener_class = getattr(listener_module, splitted_listener_path[-1])
        plistener.test_listener = listener_class()

    # test class and test case filter
    include_tags = config.get_option("include_tags")
    exclude_tags = config.get_option("exclude_tags")
    include_groups = config.get_option("include_groups")
    test_class_filter_group = FilterGroup()
    test_case_filter_group = FilterGroup()
    if include_tags:
        test_case_filter_group.append_filter(TestCaseIncludeTagsFilter(include_tags.split(",")))
    if exclude_tags:
        test_case_filter_group.append_filter(TestCaseExcludeTagsFilter(exclude_tags.split(",")))
    if include_groups:
        test_case_filter_group.append_filter(TestCaseIncludeGroupsFilter(include_groups.split(",")))
    if include_tags or exclude_tags or include_groups:
        pconsole.write_line("=" * 100)
        pconsole.write_line(" %s" % test_case_filter_group)

    # get test cases
    try:
        for test_target in test_targets:
            get_test_cases(test_target, test_class_filter_group, test_case_filter_group)
    except ImportTestTargetError as e:
        pconsole.write_line(e.message)
        return

    # exit if no tests found
    if len(test_suite.test_case_names) == 0:
        pconsole.write_line("=" * 100)
        pconsole.write_line("No tests found. Please check your command line options.")
        return

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
    pconsole.write_line("=" * 100)
    pconsole.write_line("Start to run following %s test(s):" % len(test_suite.test_case_names))
    pconsole.write_line("-" * 30)
    for test_name in test_suite.test_case_names:
        pconsole.write_line(" %s" % test_name)
    pconsole.write_line("=" * 100)

    # run test cases
    run_test_cases(int(config.get_option("test_executor_number")))

    # log the test results
    test_suite_total, test_suite_passed, test_suite_failed, test_suite_skipped, _ = test_suite.test_case_status_count
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    pconsole.write_line("Test finished in %.2fs." % test_suite.elapsed_time)
    pconsole.write_line("Total: %s, passed: %s, failed: %s, skipped: %s. Pass rate: %.1f%%." % (
        test_suite_total, test_suite_passed, test_suite_failed, test_suite_skipped, test_suite.pass_rate))

    # generate the test report
    output_path = os.path.join(workspace, config.get_option("output_dir"))
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    test_suite.sort_test_classes_for_report()
    reporter.clean_report_dir(output_path)
    reporter.generate_xunit_xml(os.path.join(output_path, config.get_option("xunit_xml")))
    reporter.generate_html_report(os.path.join(output_path, config.get_option("report_dir")))
