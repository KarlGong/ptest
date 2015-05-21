from optparse import OptionParser, OptionGroup
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
        # todo: read properties from file
        self.__parse_properties(property_args)

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
        parser = OptionParser(usage="", version="%prog 1.0")
        parser.add_option("-w", "--workspace", action="store", dest="workspace", default=".", metavar="dir",
                          help="Specify the workspace")
        parser.add_option("-t", "--targets", action="store", dest="test_targets", default=None, metavar="targets",
                          help="")
        parser.add_option("-i", "--includetags", action="store", dest="include_tags", default=None, metavar="tags",
                          help="")
        parser.add_option("-e", "--excludetags", action="store", dest="exclude_tags", default=None, metavar="tags",
                          help="")
        parser.add_option("-n", "--testexecutornumber", action="store", dest="test_executor_number", metavar="int",
                          default=1, help="")
        parser.add_option("-R", "--runfailed", action="store", dest="run_failed", default=None, metavar="file", help="")
        parser.add_option("-o", "--outputdir", action="store", dest="output_dir", default="test-output", metavar="dir",
                          help="")
        parser.add_option("-x", "--xunitxml", action="store", dest="xunit_xml", default="xunit-results.xml",
                          metavar="file",
                          help="")
        parser.add_option("-r", "--reportdir", action="store", dest="report_dir", default="html-report", metavar="dir",
                          help="")
        parser.add_option("-l", "--listener", action="store", dest="listener", default=None, metavar="file", help="")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="")
        parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=False, help="")
        parser.add_option_group(
            OptionGroup(parser, "User defined properties", "Define properties via -D<key>=<value>."))
        options, unknown_args = parser.parse_args(option_args)
        if options.test_targets and options.run_failed:
            parser.error("options -t(--test_targets) and -R(--runfailed) are mutually exclusive.")
        self.__options = options


config = Config()