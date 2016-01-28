import re

__author__ = 'karl.gong'

# -------------------------------------------
# ----------- standard assertion ------------
# -------------------------------------------
def assert_true(actual, msg=""):
    if actual is not True:
        __raise_error(msg, "Expected: <True>, Actual: <%s>." % actual)


def assert_false(actual, msg=""):
    if actual is not False:
        __raise_error(msg, "Expected: <False>, Actual: <%s>." % actual)


def assert_none(actual, msg=""):
    if actual is not None:
        __raise_error(msg, "Expected: <None>, Actual: <%s>." % actual)


def assert_not_none(actual, msg=""):
    if actual is None:
        __raise_error(msg, "Expected: NOT <None>, Actual: <None>.")


def assert_equals(actual, expected, msg=""):
    if not actual == expected:
        __raise_error(msg, "Expected: <%s>, Actual: <%s>." % (expected, actual))


def assert_not_equals(actual, not_expected, msg=""):
    if actual == not_expected:
        __raise_error(msg, "Expected: NOT <%s>, Actual: <%s>." % (not_expected, actual))


def assert_list_equals(actual_list, expected_list, msg=""):
    if len(actual_list) != len(expected_list):
        __raise_error(msg, "size of expected list <%s> is: <%s>, but size of actual list <%s> is: <%s>." %
                      (expected_list, len(expected_list), actual_list, len(actual_list)))
    for i, element in enumerate(actual_list):
        if not element == expected_list[i]:
            __raise_error(msg, "element <index: %s> of expected list <%s> is: <%s>, but element <index: %s> of actual list <%s> is: <%s>" %
                    (i, expected_list, expected_list[i], i, actual_list, actual_list[i]))


def assert_list_elements_equal(actual_list, expected_list, msg=""):
    diff_elements = [element for element in actual_list if not element in expected_list]
    if len(diff_elements) != 0:
        __raise_error(msg, "expected list <%s> doesn't contain elements <%s> from actual list <%s>." % (expected_list, diff_elements, actual_list))
    diff_elements = [element for element in expected_list if not element in actual_list]
    if len(diff_elements) != 0:
        __raise_error(msg, "actual list <%s> doesn't contain elements <%s> from expected list <%s>." % (actual_list, diff_elements, expected_list))


def assert_set_contains(superset, subset, msg=""):
    diff_elements = [element for element in subset if not element in superset]
    if len(diff_elements) != 0:
        __raise_error(msg, "Superset <%s> doesn't contain elements <%s> from subset <%s>." % (superset, diff_elements, subset))


def fail(msg=""):
    __raise_error("", msg)


def __raise_error(msg, error_msg):
    if msg:
        raise_msg = "%s\n%s" % (msg, error_msg)
    else:
        raise_msg = "%s" % error_msg
    raise AssertionError(raise_msg)

# -------------------------------------------
# --------- "assert that" assertion ---------
# -------------------------------------------
def assert_that(subject):
    if subject is None:
        return _NoneSubject(subject)
    if isinstance(subject, str):
        return _StrSubject(subject)
    if isinstance(subject, bool):
        return _BoolSubject(subject)
    if isinstance(subject, int):
        return _IntSubject(subject)
    if isinstance(subject, float):
        return _FloatSubject(subject)
    return _ObjSubject(subject)


class _Subject:
    def __init__(self, subject):
        self._subject = subject
        self._subject_name = None
        self._msg = None

    def named(self, name):
        """
            Give a name to the subject.
        """
        self._subject_name = name
        return self

    def with_message(self, message):
        """
           Set custom message for this assertion.
        """
        self._msg = message
        return self

    @property
    def subject_name(self):
        if self._subject_name is not None:
            return self._subject_name
        return str(self._subject)

    def _raise_error(self, partial_error_msg):
        error_msg = "The subject <%s> %s" % (self.subject_name, partial_error_msg)
        self._raise_raw_error(error_msg)

    def _raise_raw_error(self, error_msg):
        if self._msg:
            raise_msg = "%s\n%s" % (self._msg, error_msg)
        else:
            raise_msg = "%s" % error_msg
        raise AssertionError(raise_msg)


class _ObjSubject(_Subject):
    def __init__(self, subject):
        _Subject.__init__(self, subject)

    def is_equal_to(self, other_obj):
        """
            Fails if the subject is not equal to other obj.
        """
        if not self._subject == other_obj:
            self._raise_error("is not equal to <%s>." % other_obj)

    def is_not_equal_to(self, other_obj):
        """
            Fails if the subject is equal to other obj.
        """
        if self._subject == other_obj:
            self._raise_error("is equal to <%s>." % other_obj)

    def is_none(self):
        """
            Fails if the subject is not None.
        """
        if self._subject is not None:
            self._raise_error("is not <None>.")

    def is_not_none(self):
        """
            Fails if the subject is None.
        """
        if self._subject is None:
            self._raise_error("is <None>.")

class _NoneSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def __getattr__(self, item):
        self._raise_error("is <None>. Cannot perform assertion.")


class _StrSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_empty(self):
        """
            Fails if the string is not equal to the zero-length "".
        """
        if not self._subject == "":
            self._raise_error("is not empty.")

    def is_not_empty(self):
        """
            Fails if the string is equal to the zero-length "".
        """
        if self._subject == "":
            self._raise_error("is empty.")

    def is_blank(self):
        """
            Fails if the string is not blank.
        """
        if not self._subject.strip() == "":
            self._raise_error("is not blank.")

    def is_not_blank(self):
        """
            Fails if the string is blank.
        """
        if self._subject.strip() == "":
            self._raise_error("is blank.")

    def has_length(self, expected_length):
        """
            Fails if the string does not have the given length.
        """
        if not len(self._subject) == expected_length:
            self._raise_error("doesn't have a length of <%s>. It is <%s>." % (expected_length, len(self._subject)))

    def contains(self, string):
        """
           Fails if the string does not contain the given string.
        """
        if string not in self._subject:
            self._raise_error("doesn't contain string <%s>." % string)

    def does_not_contain(self, string):
        """
            Fails if the string contain the given string.
        """
        if string in self._subject:
            self._raise_error("contains string <%s>." % string)

    def starts_with(self, string):
        """
            Fails if the string does not start with the given string.
        """
        if not self._subject.startswith(string):
            self._raise_error("doesn't start with string <%s>." % string)

    def ends_with(self, string):
        """
            Fails if the string does not end with the given string.
        """
        if not self._subject.endswith(string):
            self._raise_error("doesn't end with string <%s>." % string)

    def matches(self, regex):
        """
            Fails if the string doesn't match the given regex.

            Note: If you want the regex to match the full string, please use "^" and "$"  in the regex.
        """
        if not re.compile(regex).search(self._subject):
            self._raise_error("doesn't match regex <%s>." % regex)

    def does_not_match(self, regex):
        """
            Fails if the string match the given regex.

            Note: If you want the regex to match the full string, please use "^" and "$"  in the regex.
        """
        if re.compile(regex).search(self._subject):
            self._raise_error("matches regex <%s>." % regex)


class _BoolSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_true(self):
        """
            Fails if the subject is false.
        """
        if self._subject is not True:
            self._raise_error("is not <True>.")

    def is_false(self):
        """
            Fails if the subject is true.
        """
        if self._subject is not False:
            self._raise_error("is not <False>.")


class _NumberSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_greater_than(self, other_number):
        """
            Fails if the subject is not greater than other number.
        """
        if self._subject <= other_number:
            self._raise_error("is not greater than <%s>." % other_number)

    def is_less_than(self, other_number):
        """
            Fails if the subject is not less than other number.
        """
        if self._subject >= other_number:
            self._raise_error("is not less than <%s>." % other_number)

    def is_at_most(self, other_number):
        """
            Fails if the subject is greater than other number.
        """
        if self._subject > other_number:
            self._raise_error("is greater than <%s>." % other_number)

    is_less_than_or_equal_to = is_at_most

    def is_at_least(self, other_number):
        """
            Fails if the subject is less than other number.
        """
        if self._subject < other_number:
            self._raise_error("is less than <%s>." % other_number)

    is_greater_than_or_equal_to = is_at_least


class _IntSubject(_NumberSubject):
    def __init__(self, subject):
        _NumberSubject.__init__(self, subject)


class _FloatSubject(_NumberSubject):
    def __init__(self, subject):
        _NumberSubject.__init__(self, subject)







