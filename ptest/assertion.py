__author__ = 'karl.gong'


def assert_true(actual, msg=""):
    if actual is not True:
        __raise_error("%s Expected: <True>, Actual: <%s>." % (msg, actual))


def assert_false(actual, msg=""):
    if actual is not False:
        __raise_error("%s Expected: <False>, Actual: <%s>." % (msg, actual))


def assert_none(actual, msg=""):
    if actual is not None:
        __raise_error("%s Expected: <None>, Actual: <%s>." % (msg, actual))


def assert_not_none(actual, msg=""):
    if actual is None:
        __raise_error("%s Expected: NOT <None>, Actual: <None>." % msg)


def assert_equals(actual, expected, msg=""):
    if not actual == expected:
        __raise_error("%s Expected: <%s>, Actual: <%s>." % (msg, expected, actual))


def assert_not_equals(actual, not_expected, msg=""):
    if actual == not_expected:
        __raise_error("%s Expected: NOT <%s>, Actual: <%s>." % (msg, not_expected, actual))


def assert_list_equals(actual_list, expected_list, msg=""):
    if cmp(actual_list, expected_list) != 0:
        __raise_error("%s Expected list: <%s>, Actual list: <%s>." % (msg, expected_list, actual_list))


def assert_list_elements_equal(actual_list, expected_list, msg=""):
    actual_sorted = sorted(actual_list)
    expected_sorted = sorted(expected_list)
    if cmp(actual_sorted, expected_sorted) != 0:
        __raise_error("%s Expected elements: <%s>, Actual elements: <%s>." % (msg, expected_list, actual_list))


def assert_set_contains(superset, subset, msg=""):
    for element in subset:
        if not element in superset:
            __raise_error(
                "%s Superset <%s> doesn't contain element <%s> from subset <%s>." % (msg, superset, element, subset))


def fail(msg=""):
    __raise_error(msg)


def __raise_error(msg):
    raise AssertionError(msg)