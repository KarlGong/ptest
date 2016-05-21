import re

class FilterGroup:
    def __init__(self):
        self.__filters = []

    def filter(self, attr_ref):
        if not self.__filters:
            return True
        for ft in self.__filters:
            if not ft.filter(attr_ref):
                return False
        return True

    def append_filter(self, filter):
        self.__filters.append(filter)

    def __len__(self):
        return len(self.__filters)

    def __getitem__(self, item):
        return self.__filters[item]


class TestClassNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, test_class_ref):
        return self._name == test_class_ref.__name__


class TestCaseNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, test_case_ref):
        return self._name == test_case_ref.__name__ \
            or re.search(r"^%s__p\d+$" % test_case_ref.__name__, self._name) \
            or re.search(r"^%s__p\d+$" % self._name, test_case_ref.__name__)


class TestCaseIncludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return len([val for val in self._tags if val in test_case_ref.__tags__]) != 0

    def __str__(self):
        return "Include Tags: %s" % ",".join(self._tags)


class TestCaseExcludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return len([val for val in self._tags if val in test_case_ref.__tags__]) == 0

    def __str__(self):
        return "Exclude Tags: %s" % ",".join(self._tags)


class TestCaseIncludeGroupsFilter:
    def __init__(self, groups):
        self._groups = groups

    def filter(self, test_case_ref):
        return test_case_ref.__group__ in self._groups

    def __str__(self):
        return "Include Groups: %s" % ",".join(self._groups)
