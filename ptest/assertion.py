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
    if len(actual_list) != len(expected_list):
        __raise_error("%s size of expected list <%s> is: <%s>, but size of actual list <%s> is: <%s>." %
                      (msg, expected_list, len(expected_list), actual_list, len(actual_list)))
    for i, element in enumerate(actual_list):
        if not element == expected_list[i]:
            __raise_error("%s element <index: %s> of expected list <%s> is: <%s>, but element <index: %s> of actual list <%s> is: <%s>" %
                    (msg, i, expected_list, expected_list[i], i, actual_list, actual_list[i]))


def assert_list_elements_equal(actual_list, expected_list, msg=""):
    diff_elements = [element for element in actual_list if not element in expected_list]
    if len(diff_elements) != 0:
        __raise_error("%s expected list <%s> doesn't contain elements <%s> from actual list <%s>." % (msg, expected_list, diff_elements, actual_list))
    diff_elements = [element for element in expected_list if not element in actual_list]
    if len(diff_elements) != 0:
        __raise_error("%s actual list <%s> doesn't contain elements <%s> from expected list <%s>." % (msg, actual_list, diff_elements, expected_list))


def assert_set_contains(superset, subset, msg=""):
    diff_elements = [element for element in subset if not element in superset]
    if len(diff_elements) != 0:
        __raise_error(
                "%s Superset <%s> doesn't contain elements <%s> from subset <%s>." % (msg, superset, diff_elements, subset))


def fail(msg=""):
    __raise_error(msg)


def __raise_error(msg):
    raise AssertionError(msg)
