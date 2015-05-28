from datetime import datetime
import os
import platform
import shutil
import traceback
from xml.dom import minidom

from plogger import pconsole
from testsuite import test_suite
from enumeration import TestCaseStatus, PDecoratorType


__author__ = 'karl.gong'


def clean_report_dir(report_path):
    if os.path.exists(report_path):
        pconsole.info("Cleaning old reports...")
        try:
            shutil.rmtree(report_path)
        except Exception as e:
            pconsole.error("Failed to clean old reports. %s\n%s" % (e.message, traceback.format_exc()))


def generate_xunit_xml(xml_file):
    pconsole.info("Generating xunit report...")
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
            pconsole.info("xunit report is generated at %s" % os.path.abspath(xml_file))
        except IOError as ioe1:
            pconsole.error("Failed to generate xunit report. %s\n%s" % (ioe1.message, traceback.format_exc()))
        finally:
            f.close()
    except IOError as ioe2:
        pconsole.error("Failed to generate xunit report. %s\n%s" % (ioe2.message, traceback.format_exc()))


def generate_html_report(report_dir):
    pconsole.info("Generating Html report...")
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
        pconsole.info("html report is generated at %s" % os.path.abspath(report_dir))
    except Exception as e:
        pconsole.error("Failed to generate Html report. %s\n%s" % (e.message, traceback.format_exc()))


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
    <tr class="test">
        <td class="test"><a href="test_class_results_{test_class.full_name}.html" target="_blank" title="{test_class.description}">{test_class.full_name}</a></td>
        <td class="duration">{test_class.elapsed_time}s</td>
        <td class="all number">{test_class.test_case_status_count[0]}</td>
        <td class="passed number">{test_class.test_case_status_count[1]}</td>
        <td class="failed number">{test_class.test_case_status_count[2]}</td>
        <td class="skipped number">{test_class.test_case_status_count[3]}</td>
        <td class="passRate">{test_class.pass_rate:.1f}%</td>
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
        <tr><td colspan="4" title="{test_case.description}" class="testcase {test_case_status}" onclick="javascript:toggleElements('{toggle_id}', 'table-row')">{test_case.name}&nbsp;&nbsp;&nbsp;&nbsp;{test_case.tags}</td></tr>
        {before_method_result}
        {test_result}
        {after_method_result}
    """
    test_case_fixture_template = """
    <tr class="test" name="{toggle_id}" style="display:none">
      <td title="{test_fixture.description}">@{test_fixture.fixture_type}</td>
      <td class="duration">{test_fixture.elapsed_time}s</td>
      <td class="logs">{test_fixture.html_format_logs}</td>
      <th class="screenshot">
        <a href="{test_fixtrue_screenshot_path}" target="_blank">
          <img src="{test_fixtrue_screenshot_path}" onload="javascript:if(this.width> 200){{this.height=this.height*200/this.width;this.width=200;}}">
        </a>
       </th></tr>
    """
    test_cases_content = ""
    for test_case in test_class.test_cases:
        before_method_content = ""
        after_method_content = ""

        if test_case.before_method:
            before_method_screen_shot_name = ""
            if test_case.before_method.screen_shot:
                before_method_screen_shot_name = test_case.full_name + "@" + PDecoratorType.BeforeMethod + ".png"
                _write_to_file(test_case.before_method.screen_shot,
                               os.path.join(report_path, before_method_screen_shot_name), mode="wb")
            before_method_content = test_case_fixture_template.format(toggle_id=test_case.name,
                                                                      test_fixture=test_case.before_method,
                                                                      test_fixtrue_screenshot_path=before_method_screen_shot_name)

        test_screen_shot_name = ""
        if test_case.test.screen_shot:
            test_screen_shot_name = test_case.full_name + "@" + PDecoratorType.Test + ".png"
            _write_to_file(test_case.test.screen_shot, os.path.join(report_path, test_screen_shot_name), mode="wb")
        test_content = test_case_fixture_template.format(toggle_id=test_case.name,
                                                         test_fixture=test_case.test,
                                                         test_fixtrue_screenshot_path=test_screen_shot_name)

        if test_case.after_method:
            after_method_screen_shot_name = ""
            if test_case.after_method.screen_shot:
                after_method_screen_shot_name = test_case.full_name + "@" + PDecoratorType.BeforeMethod + ".png"
                _write_to_file(test_case.after_method.screen_shot,
                               os.path.join(report_path, after_method_screen_shot_name), mode="wb")
            after_method_content = test_case_fixture_template.format(toggle_id=test_case.name,
                                                                     test_fixture=test_case.after_method,
                                                                     test_fixtrue_screenshot_path=after_method_screen_shot_name)

        test_case_content = test_case_template.format(toggle_id=test_case.name, test_case=test_case,
                                                      test_case_status=test_case.status.lower(),
                                                      before_method_result=before_method_content,
                                                      test_result=test_content,
                                                      after_method_result=after_method_content)
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


