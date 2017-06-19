import os
import platform
import re
from codecs import open
from optparse import OptionParser, OptionGroup

from . import __version__

_properties = {}
_options = {}


def get_option(option):
    try:
        return _options[option]
    except KeyError:
        return None


def get_property(key, default=None):
    """
        Get property value.
        If no property found, default value will be returned.
    """
    try:
        return _properties[key]
    except KeyError:
        return default


def get_int_property(key, default=None):
    """
        Get property value and convert it to int.
        If no property found, default value will be returned.
    """
    try:
        return int(_properties[key])
    except KeyError:
        return default


def get_float_property(key, default=None):
    """
        Get property value and convert it to float.
        If no property found, default value will be returned.
    """
    try:
        return float(_properties[key])
    except KeyError:
        return default


def get_boolean_property(key, default=None):
    """
        Get property value and convert it to boolean.
        If no property found, default value will be returned.
    """
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
    """
        Get property value and convert it to list.
        If no property found, default value will be returned.
    """
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
        file_object = open(property_file, encoding="utf-8")
        try:
            property_regex_str = r"^([^;#].*?)=(.*?)$"
            property_regex = re.compile(property_regex_str)
            for line in file_object:
                property_match = property_regex.search(line.strip())
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
    parser = OptionParser(usage="ptest [options] [properties]", version="ptest %s for Python %s" % (__version__, platform.python_version()),
                          description="ptest is a light test runner for Python.")

    # path and property
    parser.add_option("-w", "--workspace", action="store", dest="workspace", default=".", metavar="dir",
                      help="Specify the workspace dir (relative to working directory). Default is current working directory.")
    parser.add_option("-P", "--pythonpaths", action="store", dest="python_paths", default=None, metavar="paths",
                      help="Specify the additional locations (relative to workspace) where to search test libraries from when they are imported. "
                           "Multiple paths can be given by separating them with a comma.")
    parser.add_option("-p", "--propertyfile", action="store", dest="property_file", default=None, metavar="file",
                      help="Specify the property file (relative to workspace). "
                           "The properties in property file will be overwritten by user defined properties in cmd line. "
                           "Get property via get_property() in module ptest.config.")

    # running
    parser.add_option("-R", "--runfailed", action="store", dest="run_failed", default=None, metavar="file",
                      help="Specify the xunit result xml path (relative to workspace) and run the failed test cases in it.")
    parser.add_option("-t", "--targets", action="store", dest="test_targets", default=None, metavar="targets",
                      help="Specify the path of test targets, separated by comma. Test target can be package/module/class/method. "
                           "The target path format is: package[.module[.class[.method]]] "
                           "NOTE: ptest ONLY searches modules under --workspace, --pythonpaths and sys.path")
    parser.add_option("-f", "--filter", action="store", dest="test_filter", default=None, metavar="class",
                      help="Specify the path of test filter class, select test cases to run by the specified filter. "
                           "The test filter class should implement class TestFilter in ptest.testfilter "
                           "The filter path format is: package.module.class "
                           "NOTE: ptest ONLY searches modules under --workspace, --pythonpaths and sys.path")
    parser.add_option("-i", "--includetags", action="store", dest="include_tags", default=None, metavar="tags",
                      help="Select test cases to run by tags, separated by comma.")
    parser.add_option("-e", "--excludetags", action="store", dest="exclude_tags", default=None, metavar="tags",
                      help="Select test cases not to run by tags, separated by comma. These test cases are not run even if included with --includetags.")
    parser.add_option("-g", "--includegroups", action="store", dest="include_groups", default=None, metavar="groups",
                      help="Select test cases to run by groups, separated by comma.")
    parser.add_option("-n", "--testexecutornumber", action="store", dest="test_executor_number", metavar="int",
                      default=1, help="Specify the number of test executors. Default value is 1.")

    # output
    parser.add_option("-o", "--outputdir", action="store", dest="output_dir", default="test-output", metavar="dir",
                      help="Specify the output dir (relative to workspace).")
    parser.add_option("-r", "--reportdir", action="store", dest="report_dir", default="html-report", metavar="dir",
                      help="Specify the html report dir (relative to output dir).")
    parser.add_option("-x", "--xunitxml", action="store", dest="xunit_xml", default="xunit-results.xml",
                      metavar="file", help="Specify the xunit result xml path (relative to output dir).")

    # miscellaneous
    parser.add_option("-l", "--listeners", action="store", dest="test_listeners", default=None, metavar="class",
                      help="Specify the path of test listener classes, separated by comma. "
                           "The listener class should implement class TestListener in ptest.plistener "
                           "The listener path format is: package.module.class "
                           "NOTE: 1. ptest ONLY searches modules under --workspace, --pythonpaths and sys.path "
                           "2. The listener class must be thread safe if you set -n(--testexecutornumber) greater than 1.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Set ptest console to verbose mode.")
    parser.add_option("--temp", action="store", dest="temp", default="ptest-temp", metavar="dir",
                      help="Specify the temp dir (relative to workspace).")
    parser.add_option("--disablescreenshot", action="store_true", dest="disable_screenshot", default=False,
                      help="Disable taking screenshot for preporter.")

    # tool
    parser.add_option("-m", "--mergexunitxmls", action="store", dest="merge_xunit_xmls", default=None, metavar="files",
                      help="Merge the xunit result xmls (relative to workspace). Multiple files can be given by separating them with a comma."
                            "Use --to to specify the path of merged xunit result xml.")
    parser.add_option("--to", action="store", dest="to", default=None, metavar='path',
                      help="Specify the 'to' destination (relative to workspace).")

    # user defined properties
    parser.add_option_group(
        OptionGroup(parser, "User defined properties",
                    "Define properties via -D<key>=<value>. Get defined property via get_property() in module ptest.config."))

    options, unknown_args = parser.parse_args(option_args)

    # only one of the main options can be specified
    main_options = [options.test_targets, options.run_failed, options.merge_xunit_xmls]
    specified_options_count = len([option for option in main_options if option is not None])
    if specified_options_count == 0:
        parser.error("You must specify one of the following options: -t(--targets), -R(--runfailed), -m(--mergexunitxmls).")
    elif specified_options_count > 1:
        parser.error("You can ONLY specify one of the following options: -t(--targets), -R(--runfailed), -m(--mergexunitxmls).")

    # check '--to'
    if options.merge_xunit_xmls is not None and options.to is None:
        parser.error("You must use --to to specify the path of merged xunit result xml (--mergexunitxmls).")

    # spilt multiple values by comma
    def split(option_value):
        return None if option_value is None else option_value.split(",")

    options.python_paths = split(options.python_paths)
    options.test_targets = split(options.test_targets)
    options.include_tags = split(options.include_tags)
    options.exclude_tags = split(options.exclude_tags)
    options.include_groups = split(options.include_groups)
    options.test_listeners = split(options.test_listeners)
    options.merge_xunit_xmls = split(options.merge_xunit_xmls)

    # convert to full path for options
    def join_path(base_path, sub_path):
        return os.path.abspath(os.path.join(base_path, sub_path))

    options.workspace = join_path(os.getcwd(), options.workspace)
    options.python_paths = None if options.python_paths is None else [join_path(options.workspace, path) for path in options.python_paths]
    options.property_file = None if options.property_file is None else join_path(options.workspace, options.property_file)

    options.run_failed = None if options.run_failed is None else join_path(options.workspace, options.run_failed)
    options.output_dir = join_path(options.workspace, options.output_dir)
    options.report_dir = join_path(options.output_dir, options.report_dir)
    options.xunit_xml = join_path(options.output_dir, options.xunit_xml)
    options.temp = join_path(options.workspace, options.temp)

    options.merge_xunit_xmls = None if options.merge_xunit_xmls is None else [join_path(options.workspace, path) for path in options.merge_xunit_xmls]
    options.to = None if options.to is None else join_path(options.workspace, options.to)

    _options.update(options.__dict__)
