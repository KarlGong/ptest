__author__ = 'KarlGong'


class FilterGroup:
    def __init__(self):
        self.__filters = []

    def filter(self, attr_ref):
        if self.__filters is None or len(self.__filters) == 0:
            return True
        for ft in self.__filters:
            if not ft.filter(attr_ref):
                return False
        return True

    def append_filter(self, filter):
        self.__filters.append(filter)

    def __str__(self):
        filter_strs = []
        for ft in self.__filters:
            filter_strs.append(str(ft))
        return "\n ".join(filter_strs)


class TestClassNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, test_class_ref):
        return self._name is None or self._name == test_class_ref.__name__


class TestCaseNameFilter:
    def __init__(self, name):
        self._name = name

    def filter(self, test_case_ref):
        return self._name is None or self._name == test_case_ref.__name__


class TestCaseIncludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return self._tags is None or len([val for val in self._tags if val in test_case_ref.__tags__]) != 0

    def __str__(self):
        return "Include Tags: %s" % self._tags


class TestCaseExcludeTagsFilter:
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_case_ref):
        return self._tags is None or len([val for val in self._tags if val in test_case_ref.__tags__]) == 0

    def __str__(self):
        return "Exclude Tags: %s" % self._tags


class TestCaseIncludeGroupsFilter:
    def __init__(self, groups):
        self._groups = groups

    def filter(self, test_case_ref):
        return self._groups is None or test_case_ref.__group__ in self._groups

    def __str__(self):
        return "Include Groups: %s" % self._groups
