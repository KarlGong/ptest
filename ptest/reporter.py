import json
import os
import platform
import shutil
import traceback
from codecs import open
from datetime import datetime
from xml.dom import minidom

from . import config
from .plogger import pconsole
from .testsuite import default_test_suite
from .enumeration import TestCaseStatus, TestCaseCountItem
from .utils import make_dirs, remove_tree, escape

current_dir = os.path.dirname(os.path.abspath(__file__))


def generate_xunit_xml(xml_file_path):
    pconsole.write_line("Generating xunit report...")
    doc = minidom.Document()
    test_suite_ele = doc.createElement("testsuite")
    doc.appendChild(test_suite_ele)
    status_count = default_test_suite.status_count
    test_suite_ele.setAttribute("name", default_test_suite.name)
    test_suite_ele.setAttribute("tests", str(status_count[TestCaseCountItem.TOTAL]))
    test_suite_ele.setAttribute("failures", str(status_count[TestCaseCountItem.FAILED]))
    test_suite_ele.setAttribute("skips", str(status_count[TestCaseCountItem.SKIPPED]))
    test_suite_ele.setAttribute("errors", "0")
    test_suite_ele.setAttribute("time", "%.3f" % default_test_suite.elapsed_time)
    test_suite_ele.setAttribute("timestamp", str(default_test_suite.start_time))

    for test_case in default_test_suite.test_cases:
        test_case_ele = doc.createElement("testcase")
        test_suite_ele.appendChild(test_case_ele)
        test_case_ele.setAttribute("name", test_case.name)
        test_case_ele.setAttribute("classname", test_case.test_class.full_name)
        test_case_ele.setAttribute("time", "%.3f" % test_case.elapsed_time)
        if test_case.status == TestCaseStatus.SKIPPED:
            skipped_ele = doc.createElement("skipped")
            test_case_ele.appendChild(skipped_ele)
            skipped_ele.setAttribute("message", test_case.skip_message)
        elif test_case.status == TestCaseStatus.FAILED:
            failure_ele = doc.createElement("failure")
            test_case_ele.appendChild(failure_ele)
            failure_ele.setAttribute("message", test_case.failure_message)
            failure_ele.setAttribute("type", test_case.failure_type)
            failure_ele.appendChild(doc.createTextNode(test_case.stack_trace))

    if os.path.exists(xml_file_path):
        pconsole.write_line("Cleaning old xunit report...")
        os.remove(xml_file_path)
    else:
        make_dirs(os.path.dirname(xml_file_path))

    f = open(xml_file_path, mode="w", encoding="utf-8")
    try:
        doc.writexml(f, "\t", "\t", "\n", "utf-8")
        pconsole.write_line("xunit report is generated at %s" % xml_file_path)
    except Exception as e:
        pconsole.write_line("Failed to generate xunit report.\n%s" % traceback.format_exc())
    finally:
        f.close()


def generate_html_report(report_dir):
    pconsole.write_line("Generating html report...")

    if os.path.exists(report_dir):
        pconsole.write_line("Cleaning old html report...")
        remove_tree(report_dir, remove_root=False)
    else:
        make_dirs(report_dir)

    html_template_dir = os.path.join(current_dir, "htmltemplate")

    # copy js and css file to report dir
    for fn in os.listdir(html_template_dir):
        file_full_path = os.path.join(html_template_dir, fn)
        _, file_ext = os.path.splitext(fn)
        if os.path.isfile(file_full_path) and file_ext in [".js", ".css"]:
            shutil.copy(file_full_path, report_dir)

    # copy screenshot from temp dir
    temp_dir = config.get_option("temp")
    for fn in os.listdir(temp_dir):
        file_full_path = os.path.join(temp_dir, fn)
        _, file_ext = os.path.splitext(fn)
        if os.path.isfile(file_full_path) and file_ext == ".png":
            shutil.copy(file_full_path, report_dir)

    with open(os.path.join(html_template_dir, "index.html"), encoding="utf-8") as f:
        index_page_template = f.read()

    current_time = datetime.now()
    system_info = "%s / Python %s / %s" % (platform.node(), platform.python_version(), platform.platform())
    test_suite_json = json.dumps(_get_test_suite_dict(default_test_suite))
    index_page_content = index_page_template.format(current_time=current_time, system_info=system_info,
                                                    test_suite_json=test_suite_json)

    f = open(os.path.join(report_dir, "index.html"), mode="w", encoding="utf-8")
    try:
        f.write(index_page_content)
        pconsole.write_line("html report is generated at %s" % os.path.abspath(report_dir))
    except Exception as e:
        pconsole.write_line("Failed to generate html report.\n%s" % traceback.format_exc())
    finally:
        f.close()


def _get_test_suite_dict(test_suite):
    test_suite_dict = {
        "name": test_suite.name,
        "fullName": test_suite.full_name,
        "type": "suite",
        "testModules": _get_test_module_dicts(test_suite.test_classes),
        "startTime": str(test_suite.start_time),
        "endTime": str(test_suite.end_time),
        "elapsedTime": test_suite.elapsed_time,
        "total": test_suite.status_count[TestCaseCountItem.TOTAL],
        "passed": test_suite.status_count[TestCaseCountItem.PASSED],
        "failed": test_suite.status_count[TestCaseCountItem.FAILED],
        "skipped": test_suite.status_count[TestCaseCountItem.SKIPPED]
    }
    if not test_suite.before_suite.is_empty:
        test_suite_dict["beforeSuite"] = _get_test_fixture_dict(test_suite.before_suite)
    if not test_suite.after_suite.is_empty:
        test_suite_dict["afterSuite"] =_get_test_fixture_dict(test_suite.after_suite)
    return test_suite_dict


def _get_test_module_dicts(test_classes):
    root_test_module_dict = {
        "name": "root",
        "testModules": []
    }

    def get_or_new_module(modules, module_full_name):
        for module in modules:
            if module_full_name == module["fullName"]:
                return module
        new_module = {
            "name": module_full_name.split(".")[-1],
            "fullName": module_full_name,
            "type": "module",
            "testModules": [],
            "testClasses": [],
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
        modules.append(new_module)
        modules.sort(key=lambda m: m["name"])
        return new_module

    for test_class_dict in [_get_test_class_dict(test_class) for test_class in test_classes]:
        current_test_module_dict = root_test_module_dict
        splitted_full_name = test_class_dict["fullName"].split(".")[:-1]
        for i in range(len(splitted_full_name)):
            test_module_dict = get_or_new_module(current_test_module_dict["testModules"],
                                                 ".".join(splitted_full_name[:i + 1]))
            test_module_dict["total"] += test_class_dict["total"]
            test_module_dict["passed"] += test_class_dict["passed"]
            test_module_dict["failed"] += test_class_dict["failed"]
            test_module_dict["skipped"] += test_class_dict["skipped"]
            current_test_module_dict = test_module_dict
        current_test_module_dict["testClasses"].append(test_class_dict)
        current_test_module_dict["testClasses"].sort(key=lambda c: c["name"])
    return root_test_module_dict["testModules"]


def _get_test_class_dict(test_class):
    test_class_dict = {
        "name": test_class.name,
        "fullName": test_class.full_name,
        "type": "class",
        "runMode": test_class.run_mode,
        "runGroup": test_class.run_group,
        "description": test_class.description,
        "startTime": str(test_class.start_time),
        "endTime": str(test_class.end_time),
        "elapsedTime": test_class.elapsed_time,
        "total": test_class.status_count[TestCaseCountItem.TOTAL],
        "passed": test_class.status_count[TestCaseCountItem.PASSED],
        "failed": test_class.status_count[TestCaseCountItem.FAILED],
        "skipped": test_class.status_count[TestCaseCountItem.SKIPPED]
    }
    if test_class.is_group_feature_used:
        test_class_dict["testGroups"] = sorted([_get_test_group_dict(test_group) for test_group in test_class.test_groups], key=lambda g: g["name"])
    else:
        test_class_dict["testCases"] = sorted([_get_test_case_dict(test_case) for test_case in test_class.test_cases], key=lambda c: c["name"])

    if not test_class.before_class.is_empty:
        test_class_dict["beforeClass"] = _get_test_fixture_dict(test_class.before_class)
    if not test_class.after_class.is_empty:
        test_class_dict["afterClass"] =_get_test_fixture_dict(test_class.after_class)
    return test_class_dict


def _get_test_group_dict(test_group):
    test_group_dict = {
        "name": test_group.name,
        "fullName": test_group.full_name,
        "type": "group",
        "testCases": sorted([_get_test_case_dict(test_case) for test_case in test_group.test_cases], key=lambda c: c["name"]),
        "startTime": str(test_group.start_time),
        "endTime": str(test_group.end_time),
        "elapsedTime": test_group.elapsed_time,
        "total": test_group.status_count[TestCaseCountItem.TOTAL],
        "passed": test_group.status_count[TestCaseCountItem.PASSED],
        "failed": test_group.status_count[TestCaseCountItem.FAILED],
        "skipped": test_group.status_count[TestCaseCountItem.SKIPPED]
    }
    if not test_group.before_group.is_empty:
        test_group_dict["beforeGroup"] = _get_test_fixture_dict(test_group.before_group)
    if not test_group.after_group.is_empty:
        test_group_dict["afterGroup"] = _get_test_fixture_dict(test_group.after_group)
    return test_group_dict


def _get_test_case_dict(test_case):
    test_case_dict = {
        "name": test_case.name,
        "fullName": test_case.full_name,
        "type": "case",
        "startTime": str(test_case.start_time),
        "endTime": str(test_case.end_time),
        "elapsedTime": test_case.elapsed_time,
        "status": test_case.status,
        "tags": test_case.tags,
        "group": test_case.group,
        "description": test_case.description,
        "test": _get_test_fixture_dict(test_case.test),
    }
    if not test_case.before_method.is_empty:
        test_case_dict["beforeMethod"] = _get_test_fixture_dict(test_case.before_method)
    if not test_case.after_method.is_empty:
        test_case_dict["afterMethod"] = _get_test_fixture_dict(test_case.after_method)
    return test_case_dict


def _get_test_fixture_dict(test_fixture):
    test_fixture_dict = {
        "name": test_fixture.name,
        "fullName": test_fixture.full_name,
        "type": "fixture",
        "status": test_fixture.status,
        "fixtureType": test_fixture.fixture_type,
        "startTime": str(test_fixture.start_time),
        "endTime": str(test_fixture.end_time),
        "elapsedTime": test_fixture.elapsed_time,
        "logs": escape(test_fixture.logs),
        "screenshots": escape(test_fixture.screenshots),
        "description": test_fixture.description
    }
    return test_fixture_dict
