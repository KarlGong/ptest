from optparse import OptionParser, OptionGroup
import os
import platform
import re

__author__ = 'karl.gong'

_properties = {}
_options = {}


def get_option(option):
    try:
        return _options[option]
    except KeyError:
        return None


def get_property(key, default=None):
    try:
        return _properties[key]
    except KeyError:
        return default


def get_int_property(key, default=None):
    try:
        return int(_properties[key])
    except KeyError:
        return default


def get_float_property(key, default=None):
    try:
        return float(_properties[key])
    except KeyError:
        return default


def get_boolean_property(key, default=None):
    try:
        value = _properties[key]
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        raise ValueError("could not convert string to boolean: %s" % value)
    except KeyError:
        return default


def get_list_property(key, default=None, sep=","):
    try:
        return _properties[key].split(sep)
    except KeyError:
        return default


def load(args):
    option_args, property_args = __load_args(args)
    _parse_options(option_args)
    _load_properties_from_file()
    _parse_properties(property_args)


def _load_properties_from_file():
    property_file = get_option("property_file")
    if property_file is not None:
        file_object = open(property_file)
        try:
            property_regex_str = r"^([^;#].*?)=(.*?)$"
            property_regex = re.compile(property_regex_str)
            for line in file_object:
                property_match = property_regex.search(line)
                if property_match:
                    _properties[property_match.group(1)] = property_match.group(2)
        finally:
            file_object.close()


def __load_args(args):
    property_args = []
    option_args = []
    property_regex_str = r"^-D(.*?)=(.*?)$"  # the format of property definition must be -D<key>=<value>
    property_regex = re.compile(property_regex_str)
    for arg in args:
        property_match = property_regex.search(arg)
        if property_match:
            property_args.append(arg)
        else:
            option_args.append(arg)
    return option_args, property_args


def _parse_properties(property_args):
    property_regex_str = r"^-D(.*?)=(.*?)$"  # the format of property definition must be -D<key>=<value>
    property_regex = re.compile(property_regex_str)
    for arg in property_args:
        property_match = property_regex.search(arg)
        _properties[property_match.group(1)] = property_match.group(2)


def _parse_options(option_args):
    parser = OptionParser(usage="ptest [options] [properties]", version="ptest 1.3.2 for Python " + platform.python_version(),
                          description="ptest is a light test runner for Python.")
    parser.add_option("-w", "--workspace", action="store", dest="workspace", default=".", metavar="dir",
                      help="Specify the workspace dir (relative to working directory). Default value is current working directory.")
    parser.add_option("-t", "--targets", action="store", dest="test_targets", default=None, metavar="targets",
                      help="Specify the path of test targets, separated by comma. Test target can be package/module/class/method. "
                           "The target path format is: package[.module[.class[.method]]] "
                           "NOTE: ptest ONLY searches modules under workspace and sys.path")
    parser.add_option("-i", "--includetags", action="store", dest="include_tags", default=None, metavar="tags",
                      help="Select test cases to run by tags, separated by comma.")
    parser.add_option("-e", "--excludetags", action="store", dest="exclude_tags", default=None, metavar="tags",
                      help="Select test cases not to run by tags, separated by comma. These test cases are not run even if included with --includetags.")
    parser.add_option("-g", "--includegroups", action="store", dest="include_groups", default=None, metavar="groups",
                      help="Select test cases to run by groups, separated by comma.")
    parser.add_option("-n", "--testexecutornumber", action="store", dest="test_executor_number", metavar="int",
                      default=1, help="Specify the number of test executors. Default value is 1.")
    parser.add_option("-R", "--runfailed", action="store", dest="run_failed", default=None, metavar="file",
                      help="Specify the xunit xml path (relative to workspace) and run the failed test cases in it.")
    parser.add_option("-o", "--outputdir", action="store", dest="output_dir", default="test-output", metavar="dir",
                      help="Specify the output dir (relative to workspace).")
    parser.add_option("-x", "--xunitxml", action="store", dest="xunit_xml", default="xunit-results.xml",
                      metavar="file", help="Specify the xunit xml path (relative to output dir).")
    parser.add_option("-r", "--reportdir", action="store", dest="report_dir", default="html-report", metavar="dir",
                      help="Specify the html report dir (relative to output dir).")
    parser.add_option("-l", "--listeners", action="store", dest="test_listeners", default=None, metavar="class",
                      help="Specify the path of test listener classes, separated by comma. "
                           "The listener class should implement class TestListener in ptest.plistener "
                           "The listener path format is: package.module.class "
                           "NOTE: 1. ptest ONLY searches modules under workspace and sys.path "
                           "2. The listener class should be thread safe.")
    parser.add_option("-p", "--propertyfile", action="store", dest="property_file", default=None, metavar="file",
                      help="Read properties from file (relative to workspace). "
                           "The properties in property file will be overwritten by user defined properties in cmd line. "
                           "Get property via get_property() in module ptest.config.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Set ptest console to verbose mode.")
    parser.add_option("--temp", action="store", dest="temp", default="ptest-temp", metavar="dir",
                      help="Specify the temp dir (relative to workspace).")
    parser.add_option("--disablescreenshot", action="store_true", dest="disable_screenshot", default=False,
                      help="Disable taking screenshot for failed test fixtures.")
    parser.add_option_group(
        OptionGroup(parser, "User defined properties",
                    "Define properties via -D<key>=<value>. Get defined property via get_property() in module ptest.config."))
    options, unknown_args = parser.parse_args(option_args)
    if options.test_targets and options.run_failed:
        parser.error("Options -t(--targets) and -R(--runfailed) are mutually exclusive.")
    if (options.test_targets is None) and (options.run_failed is None):
        parser.error("You must specified one of the following options: -t(--targets), -R(--runfailed).")

    # convert to full path for options
    options.workspace = os.path.abspath(os.path.join(os.getcwd(), options.workspace))
    options.run_failed = None if options.run_failed is None else os.path.abspath(os.path.join(options.workspace, options.run_failed))
    options.output_dir = os.path.abspath(os.path.join(options.workspace, options.output_dir))
    options.xunit_xml = os.path.abspath(os.path.join(options.output_dir, options.xunit_xml))
    options.report_dir = os.path.abspath(os.path.join(options.output_dir, options.report_dir))
    options.property_file = None if options.property_file is None else os.path.abspath(os.path.join(options.workspace, options.property_file))
    options.temp = os.path.abspath(os.path.join(options.workspace, options.temp))

    _options.update(options.__dict__)
