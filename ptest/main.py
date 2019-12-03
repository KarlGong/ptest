import importlib
import os
import shlex
import traceback
from xml.dom import minidom

from .util import make_dirs, remove_tree


def get_rerun_targets(xml_file: str):
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


def merge_xunit_xmls(xml_files: str, to_file: str):
    from .plogger import pconsole
    from .test_suite import default_test_suite

    pconsole.write_line("Start to merge xunit result xmls...")

    test_case_results = {}

    for xml_file in xml_files:
        doc = minidom.parse(xml_file)
        if doc.documentElement.nodeName == "testsuites":
            root = doc.documentElement
        else:
            root = doc
        for test_suite_node in root.getElementsByTagName("testsuite"):
            for test_case_node in test_suite_node.getElementsByTagName("testcase"):
                test_case_name = "%s.%s" % (test_case_node.getAttribute("classname"), test_case_node.getAttribute("name"))
                test_case_status = 0  # passed
                if test_case_node.getElementsByTagName("failure"):
                    test_case_status = 1  # failed
                elif test_case_node.getElementsByTagName("skipped"):
                    test_case_status = 2  # skipped

                if test_case_name not in test_case_results or test_case_status < test_case_results[test_case_name]["status"]:
                    test_case_results[test_case_name] = {"status": test_case_status, "node": test_case_node}

    doc = minidom.Document()
    test_suite_ele = doc.createElement("testsuite")
    doc.appendChild(test_suite_ele)
    test_suite_ele.setAttribute("name", default_test_suite.name)
    test_suite_ele.setAttribute("tests", str(len(test_case_results)))
    test_suite_ele.setAttribute("failures", str(len([result for result in test_case_results.values() if result["status"] == 1])))
    test_suite_ele.setAttribute("skips", str(len([result for result in test_case_results.values() if result["status"] == 2])))
    test_suite_ele.setAttribute("errors", "0")

    for test_case_result in test_case_results.values():
        test_suite_ele.appendChild(test_case_result["node"])

    if os.path.exists(to_file):
        pconsole.write_line("Cleaning old merged xunit result xml...")
        os.remove(to_file)
    else:
        make_dirs(os.path.dirname(to_file))

    f = open(to_file, mode="w", encoding="utf-8")
    try:
        doc.writexml(f, "\t", "\t", "\n", "utf-8")
        pconsole.write_line("Merged xunit xml is generated at %s" % to_file)
    except Exception:
        pconsole.write_line("Failed to generate merged xunit xml.\n%s" % traceback.format_exc())
    finally:
        f.close()


def main(args=None):
    import sys
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

    # merge xunit result xmls
    xunit_xmls = config.get_option("merge_xunit_xmls")
    if xunit_xmls is not None:
        merge_xunit_xmls(xunit_xmls, config.get_option("to"))
        return

    # run test
    from .test_filter import TestFilterGroup, TestIncludeTagsFilter, TestExcludeTagsFilter, TestIncludeGroupsFilter
    from . import test_executor, reporter, plistener
    from .test_finder import TestFinder
    from .test_suite import default_test_suite
    from .plogger import pconsole

    pconsole.write_line("Starting ptest...")

    # add workspace to python path
    workspace = config.get_option("workspace")
    sys.path.insert(0, workspace)
    pconsole.write_line("Workspace:")
    pconsole.write_line(" %s" % workspace)

    # add python_paths to python path
    python_paths = config.get_option("python_paths")
    if python_paths is not None:
        pconsole.write_line("Python paths:")
        for python_path in python_paths:
            sys.path.append(python_path)
            pconsole.write_line(" %s" % python_path)

    # test filter group
    test_filter_group = TestFilterGroup()

    include_tags = config.get_option("include_tags")
    if include_tags is not None:
        test_filter_group.append_filter(TestIncludeTagsFilter(include_tags))

    exclude_tags = config.get_option("exclude_tags")
    if exclude_tags is not None:
        test_filter_group.append_filter(TestExcludeTagsFilter(exclude_tags))

    include_groups = config.get_option("include_groups")
    if include_groups is not None:
        test_filter_group.append_filter(TestIncludeGroupsFilter(include_groups))

    filter_path = config.get_option("test_filter")
    if filter_path is not None:
        splitted_filter_path = filter_path.split(".")
        filter_module = importlib.import_module(".".join(splitted_filter_path[:-1]))
        filter_class = getattr(filter_module, splitted_filter_path[-1])
        test_filter_group.append_filter(filter_class())

    if test_filter_group:
        pconsole.write_line("Test filters:")
        for test_filter in test_filter_group:
            pconsole.write_line(" %s" % test_filter)

    # get test targets
    test_targets = config.get_option("test_targets")
    if test_targets is not None:
        pconsole.write_line("Test targets:")
        for test_target in test_targets:
            test_finder = TestFinder(test_target, test_filter_group, default_test_suite)
            test_finder.find_tests()
            if test_finder.repeated_test_count:
                pconsole.write_line(
                    " %s (%s tests found, %s repeated)" % (test_target, test_finder.found_test_count, test_finder.repeated_test_count))
            else:
                pconsole.write_line(" %s (%s tests found)" % (test_target, test_finder.found_test_count))
    else:
        # rerun failed/skipped test cases
        pconsole.write_line("Run failed/skipped tests in xunit xml:")
        xunit_xml = config.get_option("run_failed")
        test_targets = get_rerun_targets(xunit_xml)
        found_test_count = 0
        for test_target in test_targets:
            test_finder = TestFinder(test_target, test_filter_group, default_test_suite)
            test_finder.find_tests()
            found_test_count += test_finder.found_test_count
        pconsole.write_line(" %s (%s tests found)" % (xunit_xml, found_test_count))

    # add test listeners
    listener_paths = config.get_option("test_listeners")
    if listener_paths is not None:
        pconsole.write_line("Test listeners:")
        for listener_path in listener_paths:
            pconsole.write_line(" %s" % listener_path)
            splitted_listener_path = listener_path.split(".")
            listener_module = importlib.import_module(".".join(splitted_listener_path[:-1]))
            listener_class = getattr(listener_module, splitted_listener_path[-1])
            plistener.test_listeners.append(listener_class())

    # init test suite
    default_test_suite.init()
    test_cases = default_test_suite.test_cases

    # exit if no tests found
    if len(test_cases) == 0:
        pconsole.write_line("=" * 100)
        pconsole.write_line("No tests found. Please check your command line options.")
        return

    # add webdriver instance to test executor to support capturing screenshot for webdriver
    try:
        from selenium.webdriver.remote.webdriver import WebDriver
    except ImportError as ie:
        pass
    else:
        def add_web_driver(executor, web_driver):
            web_drivers = executor.get_property("web_drivers")
            if web_drivers is None:
                web_drivers = []
                executor.update_properties({"web_drivers": web_drivers})
            web_drivers.append(web_driver)

        def new_start_client(self):
            try:
                current_executor = test_executor.current_executor()
                add_web_driver(current_executor, self)
                add_web_driver(current_executor.parent_test_executor, self)
                add_web_driver(current_executor.parent_test_executor.parent_test_executor, self)
            except AttributeError as ae:
                pass

        def remove_web_driver(executor, web_driver):
            web_drivers = executor.get_property("web_drivers")
            if web_drivers:
                web_drivers.remove(web_driver)

        def new_stop_client(self):
            try:
                current_executor = test_executor.current_executor()
                remove_web_driver(current_executor, self)
                remove_web_driver(current_executor.parent_test_executor, self)
                remove_web_driver(current_executor.parent_test_executor.parent_test_executor, self)
            except AttributeError as ae:
                pass

        WebDriver.start_client = new_start_client
        WebDriver.stop_client = new_stop_client

    # print test names
    pconsole.write_line("=" * 100)
    pconsole.write_line("Start to run following %s tests:" % len(test_cases))
    pconsole.write_line("-" * 30)
    for test_case in test_cases:
        pconsole.write_line(" %s" % test_case.full_name)
    pconsole.write_line("=" * 100)

    # clean and create temp dir
    temp_dir = config.get_option("temp")
    if os.path.exists(temp_dir):
        remove_tree(temp_dir, remove_root=False)
    else:
        make_dirs(temp_dir)

    # run test cases
    test_executor.TestSuiteExecutor(default_test_suite, int(config.get_option("test_executor_number"))).start_and_join()

    # log the test results
    status_count = default_test_suite.status_count
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    pconsole.write_line("Test finished in %.2fs." % default_test_suite.elapsed_time)
    pconsole.write_line("Total: %s, passed: %s, failed: %s, skipped: %s. Pass rate: %.1f%%." % (
        status_count.total, status_count.passed, status_count.failed, status_count.skipped, default_test_suite.pass_rate))

    # generate the test report
    pconsole.write_line("")
    pconsole.write_line("=" * 100)
    reporter.generate_xunit_xml(config.get_option("xunit_xml"))
    reporter.generate_html_report(config.get_option("report_dir"))

    # clean temp dir
    remove_tree(temp_dir)
