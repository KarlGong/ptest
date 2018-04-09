class TestFilter:
    def filter(self, test_ref):
        return True

    def __str__(self):
        return "Filter Class: %s.%s" % (self.__module__, self.__class__.__name__)


class TestIncludeTagsFilter(TestFilter):
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_ref):
        return hasattr(test_ref, "__tags__") and len([val for val in self._tags if val in test_ref.__tags__]) != 0

    def __str__(self):
        return "Include Tags: %s" % ",".join(self._tags)


class TestExcludeTagsFilter(TestFilter):
    def __init__(self, tags):
        self._tags = tags

    def filter(self, test_ref):
        return hasattr(test_ref, "__tags__") and len([val for val in self._tags if val in test_ref.__tags__]) == 0

    def __str__(self):
        return "Exclude Tags: %s" % ",".join(self._tags)


class TestIncludeGroupsFilter(TestFilter):
    def __init__(self, groups):
        self._groups = groups

    def filter(self, test_ref):
        return hasattr(test_ref, "__group__") and test_ref.__group__ in self._groups

    def __str__(self):
        return "Include Groups: %s" % ",".join(self._groups)


class TestFilterGroup:
    def __init__(self):
        self.__filters = []

    def filter(self, test_ref):
        if not self.__filters:
            return True
        for ft in self.__filters:
            if not ft.filter(test_ref):
                return False
        return True

    def append_filter(self, test_filter):
        self.__filters.append(test_filter)

    def __len__(self):
        return len(self.__filters)

    def __getitem__(self, item):
        return self.__filters[item]
