import importlib
import os
import shlex
import sys
from xml.dom import minidom
import shutil

__author__ = 'karl.gong'


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
    from . import config
    # load arguments
    if args is None:
        args = sys.argv[1:]
    elif not isinstance(args, (tuple, list)):
        if not isinstance(args, str):
            sys.stderr.write("ERROR: args <%s> is not a string or argument list." % args)
            return
        args = shlex.split(args)
    config.load(args)

    from .testfilter import FilterGroup, TestCaseIncludeTagsFilter, TestCaseExcludeTagsFilter, \
        TestCaseIncludeGroupsFilter
    from . import testexecutor, reporter, plistener
    from .testsuite import default_test_suite
    from .plogger import pconsole
    from .testfinder import find_test_cases, ImportTestTargetError

    pconsole.write_line("Starting ptest...")

    # add workspace to python path
    workspace = config.get_option("workspace")
    sys.path.insert(0, workspace)
    pconsole.write_line("Workspace:")
    pconsole.write_line(" %s" % workspace)

    # add python_paths to python path
    python_paths = config.get_option("python_paths")
    if python_paths:
        pconsole.write_line("Python paths:")
        for python_path in python_paths:
            sys.path.append(python_path)
            pconsole.write_line(" %s" % python_path)

    # get test targets
    test_targets_str = config.get_option("test_targets")
    if test_targets_str:
        test_targets = test_targets_str.split(",")
        pconsole.write_line("Test targets:")
        for test_target in test_targets:
            pconsole.write_line(" %s" % test_target)
    else:
        # rerun failed/skipped test cases
        xunit_xml = config.get_option("run_failed")
        pconsole.write_line("Run failed/skipped test cases in xunit xml:")
        pconsole.write_line(" %s" % xunit_xml)
        test_targets = get_rerun_targets(xunit_xml)

    # add test listeners
    listener_paths = config.get_option("test_listeners")
    if listener_paths:
        pconsole.write_line("Test listeners:")
        for listener_path in listener_paths.split(","):
            pconsole.write_line(" %s" % listener_path)
            splitted_listener_path = listener_path.split(".")
            listener_module = importlib.import_module(".".join(splitted_listener_path[:-1]))
            listener_class = getattr(listener_module, splitted_listener_path[-1])
            plistener.test_listeners.append(listener_class())

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

    # find test cases
    try:
        for test_target in test_targets:
            find_test_cases(test_target, test_class_filter_group, test_case_filter_group)
    except ImportTestTargetError as e:
        pconsole.write_line(e.message)
        return
    else:
        test_cases = default_test_suite.test_cases
        default_test_suite.init_test_fixture()

    # exit if no tests found
    if len(test_cases) == 0:
        pconsole.write_line("=" * 100)
        pconsole.write_line("No tests found. Please check your command line options.")
        return

    # add webdriver instance to test executor to support capturing screenshot for webdriver
    try:
        from selenium.webdriver.remote.webdriver import WebDriver
    except ImportError:
        pass
    else:
        def new_start_client(self):
            try:
                current_executor = testexecutor.current_executor()
                current_executor.update_properties({"web_driver": self})
                current_executor.parent_test_executor.update_properties({"web_driver": self})
                current_executor.parent_test_executor.parent_test_executor.update_properties({"web_driver": self})
            except AttributeError:
                pass
        def new_stop_client(self):
            try:
                current_executor = testexecutor.current_executor()
                current_executor.update_properties({"web_driver": None})
                current_executor.parent_test_executor.update_properties({"web_driver": None})
                current_executor.parent_test_executor.parent_test_executor.update_properties({"web_driver": None})
            except AttributeError:
                pass
        WebDriver.start_client = new_start_client
        WebDriver.stop_client = new_stop_client

    # sort the test groups for running
    default_test_suite.sort_test_classes_for_running()
    pconsole.write_line("=" * 100)
    pconsole.write_line("Start to run following %s test(s):" % len(test_cases))
    pconsole.write_line("-" * 30)
    for test_case in test_cases:
        pconsole.write_line(" %s" % test_case.full_name)
    pconsole.write_line("=" * 100)

    # clean and create temp dir
    temp_dir = config.get_option("temp")
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(temp_dir)

    # run test cases
    testexecutor.TestSuiteExecutor(default_test_suite, int(config.get_option("test_executor_number"))).start_and_join()

    # log the test results
    status_count = default_test_suite.status_count
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    pconsole.write_line("Test finished in %.2fs." % default_test_suite.elapsed_time)
    pconsole.write_line("Total: %s, passed: %s, failed: %s, skipped: %s. Pass rate: %.1f%%." % (
        status_count["total"], status_count["passed"], status_count["failed"], status_count["skipped"],
        default_test_suite.pass_rate))

    # generate the test report
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    default_test_suite.sort_test_classes_for_report()
    reporter.clean_output_dir(config.get_option("output_dir"))
    reporter.generate_xunit_xml(config.get_option("xunit_xml"))
    reporter.generate_html_report(config.get_option("report_dir"))

    # clean temp dir
    shutil.rmtree(temp_dir)
