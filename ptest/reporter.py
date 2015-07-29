from datetime import datetime
import os
import platform
import shutil
import traceback
from xml.dom import minidom

from plogger import pconsole
from testsuite import test_suite
from enumeration import TestCaseStatus


__author__ = 'karl.gong'


def clean_report_dir(report_path):
    if os.path.exists(report_path):
        pconsole.write_line("Cleaning old reports...")
        try:
            shutil.rmtree(report_path)
        except Exception as e:
            pconsole.write_line("Failed to clean old reports. %s\n%s" % (e.message, traceback.format_exc()))


def generate_xunit_xml(xml_file):
    pconsole.write_line("Generating xunit report...")
    os.makedirs(os.path.dirname(xml_file))
    doc = minidom.Document()
    test_suite_ele = doc.createElement("testsuite")
    doc.appendChild(test_suite_ele)
    test_suite_total, test_suite_passed, test_suite_failed, test_suite_skipped, _ = test_suite.test_case_status_count
    test_suite_ele.setAttribute("name", "TestNG")
    test_suite_ele.setAttribute("tests", str(test_suite_total))
    test_suite_ele.setAttribute("failures", str(test_suite_failed))
    test_suite_ele.setAttribute("skips", str(test_suite_skipped))
    test_suite_ele.setAttribute("errors", "0")
    test_suite_ele.setAttribute("time", "%.3f" % test_suite.elapsed_time)
    test_suite_ele.setAttribute("timestamp", str(test_suite.start_time))

    for test_class in test_suite.test_classes:
        for test_case in test_class.test_cases:
            test_case_ele = doc.createElement("testcase")
            test_suite_ele.appendChild(test_case_ele)
            test_case_ele.setAttribute("name", test_case.name)
            test_case_ele.setAttribute("classname", test_class.full_name)
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

    try:
        f = open(xml_file, "w")
        try:
            doc.writexml(f, "\t", "\t", "\n", "utf-8")
            pconsole.write_line("xunit report is generated at %s" % os.path.abspath(xml_file))
        except IOError as ioe1:
            pconsole.write_line("Failed to generate xunit report. %s\n%s" % (ioe1.message, traceback.format_exc()))
        finally:
            f.close()
    except IOError as ioe2:
        pconsole.write_line("Failed to generate xunit report. %s\n%s" % (ioe2.message, traceback.format_exc()))


def generate_html_report(report_dir):
    pconsole.write_line("Generating Html report...")
    os.makedirs(report_dir)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_file = os.path.join(current_dir, "htmltemplate", "report.css")
    js_file = os.path.join(current_dir, "htmltemplate", "amcharts.js")
    shutil.copy(css_file, report_dir)
    shutil.copy(js_file, report_dir)
    try:
        _generate_index_page(report_dir)
        for test_class in test_suite.test_classes:
            _generate_test_class_page(test_class, report_dir)
        pconsole.write_line("html report is generated at %s" % os.path.abspath(report_dir))
    except Exception as e:
        pconsole.write_line("Failed to generate Html report. %s\n%s" % (e.message, traceback.format_exc()))


def _generate_index_page(report_dir):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = open(os.path.join(current_dir, "htmltemplate", "index.html"))
    try:
        index_page_template = template_file.read()
    finally:
        template_file.close()
    current_time = datetime.now()
    system_info = "%s / Python %s / %s" % (platform.node(), platform.python_version(), platform.platform())
    test_class_summaries_content = ""
    test_class_summary_template = """
    <tr class="test-class">
        <td class="name" onclick="javascript: window.open('test_class_results_{test_class.full_name}.html')" title="{test_class.description}">{test_class.full_name}</td>
        <td class="number">{test_class.elapsed_time}s</td>
        <td class="all number" onclick="javascript: window.open('test_class_results_{test_class.full_name}.html#all')">{test_class.test_case_status_count[0]}</td>
        <td class="passed number" onclick="javascript: window.open('test_class_results_{test_class.full_name}.html#passed')">{test_class.test_case_status_count[1]}</td>
        <td class="failed number" onclick="javascript: window.open('test_class_results_{test_class.full_name}.html#failed')">{test_class.test_case_status_count[2]}</td>
        <td class="skipped number" onclick="javascript: window.open('test_class_results_{test_class.full_name}.html#skipped')">{test_class.test_case_status_count[3]}</td>
        <td class="pass-rate number">{test_class.pass_rate:.1f}%</td>
    </tr>
    """
    for test_class in test_suite.test_classes:
        test_class_summaries_content += test_class_summary_template.format(test_class=test_class)
    index_page_content = index_page_template.format(current_time=current_time, system_info=system_info,
                                                    test_suite=test_suite,
                                                    test_class_summaries=test_class_summaries_content)
    _write_to_file(index_page_content, os.path.join(report_dir, "index.html"))


def _generate_test_class_page(test_class, report_path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = open(os.path.join(current_dir, "htmltemplate", "test_class_results.html"))
    try:
        test_class_page_template = template_file.read()
    finally:
        template_file.close()

    test_case_template = """
        <tr title="{test_case.description}" class="testcase {test_case.status}" onclick="javascript:toggleElements('toggle-{toggle_id}', 'table-row')"><td colspan="4">
        <span class="name">{test_case.name}</span>
        {test_case_tags}
        <span class="group" title="group">{test_case.group}</span>
        </td></tr>
        {before_method_result}
        {test_result}
        {after_method_result}
    """
    test_case_tag_template ="""
        <span class="tag" title="tag">{tag}</span>
    """
    test_case_fixture_template = """
    <tr class="test-fixture toggle-{toggle_id}" style="display:none">
      <td title="{test_case_fixture.description}">@{test_case_fixture.fixture_type}</td>
      <td class="duration">{test_case_fixture.elapsed_time}s</td>
      <td class="logs">{test_case_fixture_logs}</td>
      <th class="screenshot">
        <a href="{test_case_fixtrue_screenshot_path}" target="_blank">
          <img src="{test_case_fixtrue_screenshot_path}" style="width:200px;border:0;">
        </a>
       </th></tr>
    """
    test_case_fixture_log_template = """
        <span class="log-level">[{level_name}]</span>
        <span class="{level_name}">{msg}</span>
    """
    test_cases_content = ""

    # test fixture
    def make_test_case_fixture_content(test_case_fixture):
        if test_case_fixture:
            # screenshot
            test_case_fixture_screen_shot_name = ""
            if test_case_fixture.screen_shot:
                test_case_fixture_screen_shot_name = test_case_fixture.full_name + ".png"
                _write_to_file(test_case_fixture.screen_shot,
                               os.path.join(report_path, test_case_fixture_screen_shot_name), mode="wb")
            # logs
            test_case_fixture_log_content_list = []
            for level_name, msg in test_case_fixture.logs:
                html_msg = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")\
                                            .replace('"', "&quot;").replace("\n", "<br/>")
                test_case_fixture_log_content_list.append(test_case_fixture_log_template.format(level_name=level_name, msg=html_msg))
            test_case_fixture_logs_content = "<br/>".join(test_case_fixture_log_content_list)
            return test_case_fixture_template.format(toggle_id=test_case_fixture.test_case.name,
                                                                     test_case_fixture=test_case_fixture,
                                                                     test_case_fixture_logs=test_case_fixture_logs_content,
                                                                     test_case_fixtrue_screenshot_path=test_case_fixture_screen_shot_name)
        return ""

    # test cases
    for test_case in test_class.test_cases:
        # tags
        test_case_tags_content = ""
        for tag in test_case.tags:
            test_case_tags_content += test_case_tag_template.format(tag=tag)
        # test case
        test_case_content = test_case_template.format(toggle_id=test_case.name, test_case=test_case,
                                                      test_case_tags=test_case_tags_content,
                                                      before_method_result=make_test_case_fixture_content(test_case.before_method),
                                                      test_result=make_test_case_fixture_content(test_case.test),
                                                      after_method_result=make_test_case_fixture_content(test_case.after_method))
        test_cases_content += test_case_content

    test_class_page_content = test_class_page_template.format(test_class=test_class,
                                                              test_cases_results=test_cases_content)
    _write_to_file(test_class_page_content,
                   os.path.join(report_path, "test_class_results_" + test_class.full_name + ".html"))


def _write_to_file(file_content, file_name, mode="w"):
    f = open(file_name, mode)
    try:
        f.write(file_content)
    finally:
        f.close()


