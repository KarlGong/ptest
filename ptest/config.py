from optparse import OptionParser, OptionGroup
import os
import re

__author__ = 'karl.gong'


class Config:
    def __init__(self):
        self.__properties = {}
        self.__options = None

    def get_option(self, option):
        return getattr(self.__options, option)

    def get_property(self, key):
        try:
            return self.__properties[key]
        except KeyError:
            return None

    def load(self, args):
        option_args, property_args = self.__load_args(args)
        self.__parse_options(option_args)
        self.__load_properties_from_file()
        self.__parse_properties(property_args)

    def __load_properties_from_file(self):
        property_file = self.get_option("propery_file")
        if property_file is not None:
            file_object = open(os.path.join(os.getcwd(), self.get_option("workspace"), property_file))
            try:
                property_regex_str = ur"^([^;#].*?)=(.*?)$"
                property_regex = re.compile(property_regex_str)
                for line in file_object:
                    property_match = property_regex.search(line)
                    if property_match:
                        self.__properties[property_match.group(1)] = property_match.group(2)
            finally:
                file_object.close()

    def __load_args(self, args):
        property_args = []
        option_args = []
        property_regex_str = ur"^-D(.*?)=(.*?)$"  # the format of property definition must be -D<key>=<value>
        property_regex = re.compile(property_regex_str)
        for arg in args:
            property_match = property_regex.search(arg)
            if property_match:
                property_args.append(arg)
            else:
                option_args.append(arg)
        return option_args, property_args

    def __parse_properties(self, property_args):
        property_regex_str = ur"^-D(.*?)=(.*?)$"  # the format of property definition must be -D<key>=<value>
        property_regex = re.compile(property_regex_str)
        for arg in property_args:
            property_match = property_regex.search(arg)
            self.__properties[property_match.group(1)] = property_match.group(2)

    def __parse_options(self, option_args):
        parser = OptionParser(usage="ptest [options] [properties]", version="ptest 1.0.0",
                              description="ptest is a light testing framework for Python.")
        parser.add_option("-w", "--workspace", action="store", dest="workspace", default=".", metavar="dir",
                          help="Specify the workspace dir. Default value is current dir.")
        parser.add_option("-t", "--targets", action="store", dest="test_targets", default=None, metavar="targets",
                          help="Specify the test targets, separated by comma. Test target can be package/module/class/method.")
        parser.add_option("-i", "--includetags", action="store", dest="include_tags", default=None, metavar="tags",
                          help="Select test cases to run by tag.")
        parser.add_option("-e", "--excludetags", action="store", dest="exclude_tags", default=None, metavar="tags",
                          help="Select test cases not to run by tag. These tests are not run even if included with --includetags.")
        parser.add_option("-n", "--testexecutornumber", action="store", dest="test_executor_number", metavar="int",
                          default=1, help="Specify the number of test executors. Default value is 1.")
        parser.add_option("-R", "--runfailed", action="store", dest="run_failed", default=None, metavar="file",
                          help="Specify the xunitxml path and run the failed test cases.")
        parser.add_option("-o", "--outputdir", action="store", dest="output_dir", default="test-output", metavar="dir",
                          help="Specify the output dir.")
        parser.add_option("-x", "--xunitxml", action="store", dest="xunit_xml", default="xunit-results.xml",
                          metavar="file", help="Specify the xunit_xm pathl")
        parser.add_option("-r", "--reportdir", action="store", dest="report_dir", default="html-report", metavar="dir",
                          help="Specify the report dir.")
        parser.add_option("-l", "--listener", action="store", dest="listener", default=None, metavar="file",
                          help="Specify the path of test listener. The listener class must implement ptest.TestListener")
        parser.add_option("-p", "--propertyfile", action="store", dest="propery_file", default=None, metavar="file",
                          help="Read properties from file. The properties in property file will be overwritten by user defined properties in cmd line. "
                               "Get property via config.get_property() in ptest.config.")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Set ptest console to verbose mode.")
        parser.add_option_group(
            OptionGroup(parser, "User defined properties",
                        "Define properties via -D<key>=<value>. Get defined property via config.get_property() in ptest.config."))
        options, unknown_args = parser.parse_args(option_args)
        if options.test_targets and options.run_failed:
            parser.error("Options -t(--test_targets) and -R(--runfailed) are mutually exclusive.")
        if (options.test_targets is None) and (options.run_failed is None):
            parser.error("You must specified one of the following options: -t(--test_target), -R(--run_failed).")
        self.__options = options


config = Config()