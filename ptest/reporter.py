import os
import json
import platform
import shutil
import traceback
from xml.dom import minidom
from datetime import datetime

from . import config
from .plogger import pconsole
from .testsuite import test_suite
from .enumeration import TestCaseStatus

__author__ = 'karl.gong'

current_dir = os.path.dirname(os.path.abspath(__file__))


def clean_output_dir(output_dir):
    if os.path.exists(output_dir):
        pconsole.write_line("Cleaning old reports...")
        try:
            for root, dirs, files in os.walk(output_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        except Exception:
            pconsole.write_line("Failed to clean old reports.\n%s" % traceback.format_exc())


def generate_xunit_xml(xml_file_path):
    pconsole.write_line("Generating xunit report...")
    xml_file_dir = os.path.dirname(xml_file_path)
    if not os.path.exists(xml_file_dir):
        os.makedirs(xml_file_dir)
    doc = minidom.Document()
    test_suite_ele = doc.createElement("testsuite")
    doc.appendChild(test_suite_ele)
    status_count = test_suite.status_count
    test_suite_ele.setAttribute("name", test_suite.name)
    test_suite_ele.setAttribute("tests", str(status_count["total"]))
    test_suite_ele.setAttribute("failures", str(status_count["failed"]))
    test_suite_ele.setAttribute("skips", str(status_count["skipped"]))
    test_suite_ele.setAttribute("errors", "0")
    test_suite_ele.setAttribute("time", "%.3f" % test_suite.elapsed_time)
    test_suite_ele.setAttribute("timestamp", str(test_suite.start_time))

    for test_case in test_suite.test_cases:
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

    f = open(xml_file_path, "w")
    try:
        doc.writexml(f, "\t", "\t", "\n", "utf-8")
        pconsole.write_line("xunit report is generated at %s" % xml_file_path)
    except Exception:
        pconsole.write_line("Failed to generate xunit report.\n%s" % traceback.format_exc())
    finally:
        f.close()


def generate_html_report(report_dir):
    pconsole.write_line("Generating html report...")
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

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

    with open(os.path.join(html_template_dir, "index.html")) as f:
        index_page_template = f.read()

    current_time = datetime.now()
    system_info = "%s / Python %s / %s" % (platform.node(), platform.python_version(), platform.platform())
    test_suite_json = json.dumps(_get_test_suite_dict(test_suite))
    index_page_content = index_page_template.format(current_time=current_time, system_info=system_info,
                                                    test_suite_json=test_suite_json)

    f = open(os.path.join(report_dir, "index.html"), mode="w")
    try:
        f.write(index_page_content)
        pconsole.write_line("html report is generated at %s" % os.path.abspath(report_dir))
    except Exception:
        pconsole.write_line("Failed to generate html report.\n%s" % traceback.format_exc())
    finally:
        f.close()


def _get_test_suite_dict(suite):
    repr_dict = {
        "name": suite.name,
        "fullName": suite.full_name,
        "type": "testsuite",
        "beforeSuite": _get_test_fixture_dict(suite.before_suite),
        "testClasses": [_get_test_class_dict(test_class) for test_class in suite.test_classes],
        "afterSuite": _get_test_fixture_dict(suite.after_suite),
        "startTime": str(suite.start_time),
        "endTime": str(suite.end_time),
        "elapsedTime": suite.elapsed_time,
        "statusCount": suite.status_count,
        "passRate": suite.pass_rate
    }
    return repr_dict


def _get_test_class_dict(test_class):
    repr_dict = {
        "name": test_class.name,
        "fullName": test_class.full_name,
        "type": "testclass",
        "runThread": test_class.run_thread,
        "runMode": test_class.run_mode,
        "description": test_class.description,
        "beforeClass": _get_test_fixture_dict(test_class.before_class),
        "testGroups": [_get_test_group_dict(test_group) for test_group in test_class.test_groups],
        "afterClass": _get_test_fixture_dict(test_class.after_class),
        "startTime": str(test_class.start_time),
        "endTime": str(test_class.end_time),
        "elapsedTime": test_class.elapsed_time,
        "statusCount": test_class.status_count,
        "passRate": test_class.pass_rate
    }
    return repr_dict


def _get_test_group_dict(test_group):
    repr_dict = {
        "name": test_group.name,
        "fullName": test_group.full_name,
        "type": "testgroup",
        "beforeGroup": _get_test_fixture_dict(test_group.before_group),
        "testCases": [_get_test_case_dict(test_case) for test_case in test_group.test_cases],
        "afterGroup": _get_test_fixture_dict(test_group.after_group),
        "startTime": str(test_group.start_time),
        "endTime": str(test_group.end_time),
        "elapsedTime": test_group.elapsed_time,
        "statusCount": test_group.status_count,
        "passRate": test_group.pass_rate
    }
    return repr_dict


def _get_test_case_dict(test_case):
    repr_dict = {
        "name": test_case.name,
        "fullName": test_case.full_name,
        "type": "testcase",
        "startTime": str(test_case.start_time),
        "endTime": str(test_case.end_time),
        "elapsedTime": test_case.elapsed_time,
        "status": test_case.status,
        "tags": test_case.tags,
        "group": test_case.group,
        "description": test_case.description,
        "beforeMethod": _get_test_fixture_dict(test_case.before_method),
        "test": _get_test_fixture_dict(test_case.test),
        "afterMethod": _get_test_fixture_dict(test_case.after_method)
    }
    return repr_dict


def _get_test_fixture_dict(test_fixture):
    repr_dict = {
        "type": "testfixture",
        "isEmpty": test_fixture.is_empty,
        "status": test_fixture.status,
        "fixtureType": test_fixture.fixture_type
    }
    if not test_fixture.is_empty:
        escaped_logs = [{"level": log["level"], "message": log["message"].replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace(" ", "&nbsp;").replace('"', "&quot;").replace("\n", "<br/>")} for log in test_fixture.logs]
        repr_extra_dict = {
            "name": test_fixture.name,
            "fullName": test_fixture.full_name,
            "startTime": str(test_fixture.start_time),
            "endTime": str(test_fixture.end_time),
            "elapsedTime": test_fixture.elapsed_time,
            "logs": escaped_logs,
            "screenshot": test_fixture.screenshot,
            "description": test_fixture.description
        }
        repr_dict.update(repr_extra_dict)
    return repr_dict
