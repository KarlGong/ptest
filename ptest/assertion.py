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
from numbers import Number
from datetime import datetime, date
try:
    StringTypes = (str, unicode)
except NameError:
    StringTypes = (str,)

SUBJECT_TYPE_MAP = {}

def assert_that(subject):
    if subject is None:
        return _NoneSubject(subject)
    if isinstance(subject, StringTypes):
        return _StringSubject(subject)
    if isinstance(subject, bool):
        return _BoolSubject(subject)
    if isinstance(subject, Number):
        return _NumericSubject(subject)
    if isinstance(subject, list):
        return _ListSubject(subject)
    if isinstance(subject, tuple):
        return _TupleSubject(subject)
    if isinstance(subject, set):
        return _SetSubject(subject)
    if isinstance(subject, dict):
        return _DictSubject(subject)
    if isinstance(subject, datetime):
        return _DateTimeSubject(subject)
    if isinstance(subject, date):
        return _DateSubject(subject)
    for subject_type, subject_class in SUBJECT_TYPE_MAP.items():
        if isinstance(subject, subject_type):
            return subject_class(subject)
    return _ObjSubject(subject)

# this method is used to format the obj without square brackets
def _rb(obj):
    return str(obj)[1:-1]

# this method is used to get the type name of the object
def _name(obj):
    return type(obj).__name__

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

    def _raise_error(self, partial_error_msg):
        if self._subject_name is None:
            error_msg = "Unexpectedly that the %s <%s> %s" % (_name(self._subject), self._subject, partial_error_msg)
        else:
            error_msg = "Unexpectedly that the %s named \"%s\" %s" % (_name(self._subject), self._subject_name, partial_error_msg)
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
            self._raise_error("is not equal to %s <%s>." % (_name(other_obj), other_obj))
        return self

    def is_not_equal_to(self, other_obj):
        """
            Fails if the subject is equal to other obj.
        """
        if self._subject == other_obj:
            self._raise_error("is equal to %s <%s>." % (_name(other_obj), other_obj))
        return self

    def is_none(self):
        """
            Fails if the subject is not None.
        """
        if self._subject is not None:
            self._raise_error("is not <None>.")
        return self

    def is_not_none(self):
        """
            Fails if the subject is None.
        """
        if self._subject is None:
            self._raise_error("is <None>.")
        return self

    def is_in(self, iterable):
        """
           Fails unless the subject is equal to any element in the given iterable.
        """
        if self._subject not in iterable:
            self._raise_error("is not in %s <%s>." % (_name(iterable), iterable))
        return self

    def is_not_in(self, iterable):
        """
           Fails if the subject is equal to any element in the given iterable.
        """
        if self._subject in iterable:
            self._raise_error("is in %s <%s>" % (_name(iterable), iterable))
        return self


class _NoneSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def __getattr__(self, item):
        self._raise_raw_error("Cannot perform assertion \"%s\" for <None>." % item)


class _BoolSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_true(self):
        """
            Fails if the subject is false.
        """
        if self._subject is not True:
            self._raise_error("is not <True>.")
        return self

    def is_false(self):
        """
            Fails if the subject is true.
        """
        if self._subject is not False:
            self._raise_error("is not <False>.")
        return self


class _NumericSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_greater_than(self, other_number):
        """
            Fails if the subject is not greater than other number.
        """
        if self._subject <= other_number:
            self._raise_error("is not greater than <%s>." % other_number)
        return self

    def is_less_than(self, other_number):
        """
            Fails if the subject is not less than other number.
        """
        if self._subject >= other_number:
            self._raise_error("is not less than <%s>." % other_number)
        return self

    def is_less_than_or_equal_to(self, other_number):
        """
            Fails if the subject is greater than other number.
        """
        if self._subject > other_number:
            self._raise_error("is greater than <%s>." % other_number)
        return self

    is_at_most = is_less_than_or_equal_to

    def is_greater_than_or_equal_to(self, other_number):
        """
            Fails if the subject is less than other number.
        """
        if self._subject < other_number:
            self._raise_error("is less than <%s>." % other_number)
        return self

    is_at_least = is_greater_than_or_equal_to

    def is_zero(self):
        """
            Fails if the subject is not zero (0).
        """
        if self._subject != 0:
            self._raise_error("is not <0>.")
        return self

    def is_not_zero(self):
        """
            Fails if the subject is zero (0).
        """
        if self._subject == 0:
            self._raise_error("is <0>.")
        return self

    def is_positive(self):
        """
            Fails if the subject is not positive.
        """
        if self._subject <= 0:
            self._raise_error("is not positive.")
        return self

    def is_negative(self):
        """
            Fails if the subject is not negative.
        """
        if self._subject >= 0:
            self._raise_error("is not negative.")
        return self

    def is_between(self, low, high):
        """
            Fails if the subject is not between low and high.

            Note: low and high are included
        """
        if self._subject < low or self._subject > high:
            self._raise_error("is not between low <%s> and high <%s>" % (low, high))
        return self


class _IterableSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_empty(self):
        """
            Fails if the subject is empty.
        """
        if len(self._subject) != 0:
            self._raise_error("is not empty.")
        return self

    def is_not_empty(self):
        """
            Fails if the subject is not empty.
        """
        if len(self._subject) == 0:
            self._raise_error("is empty.")
        return self

    def has_length(self, expected_length):
        """
            Fails if the subject does not have the given length.
        """
        if not len(self._subject) == expected_length:
            self._raise_error("doesn't have a length of <%s>. It is <%s>." % (expected_length, len(self._subject)))
        return self

    def contains(self, obj):
        """
            Fails if the subject doesn't contain the given object.
        """
        if obj not in self._subject:
            self._raise_error("doesn't contain %s <%s>." % (_name(obj), obj))
        return self

    def does_not_contain(self, obj):
        """
            Fails if the subject contain the given object.
        """
        if obj in self._subject:
            self._raise_error("contains %s <%s>." % (_name(obj), obj))
        return self

    def contains_all_of(self, *objs):
        """
            Fails unless the subject contains all of the given objects.
        """
        uncontained_objs = [obj for obj in objs if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in <%s>." % (_rb(uncontained_objs), _rb(list(objs))))
        return self

    def contains_all_in(self, iterable):
        """
            Fails unless the subject contains all in the given iterable.
        """
        uncontained_objs = [obj for obj in iterable if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." % (_rb(uncontained_objs), _name(iterable), iterable))
        return self

    def contains_any_of(self, *objs):
        """
            Fails unless the subject contains any of the given objects.
        """
        contained_objs = [obj for obj in objs if obj in self._subject]
        if not contained_objs:
            self._raise_error("doesn't contain any element in <%s>." % _rb(list(objs)))
        return self

    def contains_any_in(self, iterable):
        """
            Fails unless the subject contains any in the given iterable.
        """
        contained_objs = [obj for obj in iterable if obj in self._subject]
        if not contained_objs:
            self._raise_error("doesn't contain any element in %s <%s>." % (_name(iterable), iterable))
        return self

    def contains_none_of(self, *objs):
        """
            Fails if the subject contains any of the given objects.
        """
        contained_objs = [obj for obj in objs if obj in self._subject]
        if contained_objs:
            self._raise_error("contains elements <%s> in <%s>." % (_rb(contained_objs), _rb(list(objs))))
        return self

    def contains_none_in(self, iterable):
        """
            Fails if the subject contains any in the given iterable.
        """
        contained_objs = [obj for obj in iterable if obj in self._subject]
        if contained_objs:
            self._raise_error("contains elements <%s> in %s <%s>." % (_rb(contained_objs), _name(iterable), iterable))
        return self


class _CollectionSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def is_super_of(self, other_collection):
        """
            Fails unless the collection contains all elements in other collection.
        """
        uncontained_objs = [obj for obj in other_collection if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_collection), other_collection))

    def is_sub_of(self, other_collection):
        """
            Fails unless all elements in collection are in other collection.
        """
        uncontained_objs = [obj for obj in self._subject if obj not in other_collection]
        if uncontained_objs:
            self._raise_error("has elements <%s> not in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_collection), other_collection))


class _StringSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def is_blank(self):
        """
            Fails if the string is not blank.
        """
        if len(self._subject.strip()) != 0:
            self._raise_error("is not blank.")
        return self

    def is_not_blank(self):
        """
            Fails if the string is blank.
        """
        if len(self._subject.strip()) == 0:
            self._raise_error("is blank.")
        return self

    def starts_with(self, string):
        """
            Fails if the string does not start with the given string.
        """
        if not self._subject.startswith(string):
            self._raise_error("doesn't start with string <%s>." % string)
        return self

    def ends_with(self, string):
        """
            Fails if the string does not end with the given string.
        """
        if not self._subject.endswith(string):
            self._raise_error("doesn't end with string <%s>." % string)
        return self

    def matches(self, regex):
        """
            Fails if the string doesn't match the given regex.

            Note: If you want to match the entire string, just include anchors in the regex pattern.
        """
        if not re.compile(regex).search(self._subject):
            self._raise_error("doesn't match regex <%s>." % regex)
        return self

    def does_not_match(self, regex):
        """
            Fails if the string match the given regex.

            Note: If you want to match the entire string, just include anchors in the regex pattern.
        """
        if re.compile(regex).search(self._subject):
            self._raise_error("matches regex <%s>." % regex)
        return self


class _ListSubject(_CollectionSubject):
    def __init__(self, subject):
        _CollectionSubject.__init__(self, subject)

    def has_same_elements_as(self, other_list):
        """
            Fails unless the list has the same elements as other list.
        """
        self.is_super_of(other_list)
        self.is_sub_of(other_list)


class _TupleSubject(_CollectionSubject):
    def __init__(self, subject):
        _CollectionSubject.__init__(self, subject)

    def has_same_elements_as(self, other_tuple):
        """
            Fails unless the list has the same elements as other list.
        """
        self.is_super_of(other_tuple)
        self.is_sub_of(other_tuple)


class _SetSubject(_CollectionSubject):
    def __init__(self, subject):
        _CollectionSubject.__init__(self, subject)


class _DictSubject(_CollectionSubject):
    def __init__(self, subject):
        _CollectionSubject.__init__(self, subject)

    def contains_key(self, key):
        """
            Fails if the dict doesn't contain the given key.
        """
        if key not in self._subject:
            self._raise_error("doesn't contain key %s <%s>." % (_name(key), key))
        return self

    def does_not_contain_key(self, key):
        """
            Fails if the dict contains the given key.
        """
        if key in self._subject:
            self._raise_error("contains key %s <%s>." % (_name(key), key))
        return self

    def contains_entry(self, key, value):
        """
           Fails if the dict doesn't contain the given entry.
        """
        if (key, value) not in self._subject.items():
            self._raise_error("doesn't contain entry, key: %s <%s>, value: %s <%s>." % (_name(key), key, _name(value), value))
        return self

    def does_not_contain_entry(self, key, value):
        """
            Fails if the dict contain the given entry.
        """
        if (key, value) in self._subject.items():
            self._raise_error("contains entry, key: %s <%s>, value: %s <%s>." % (_name(key), key, _name(value), value))
        return self

    def is_super_of(self, other_dict):
        """
            Fails unless the collection contains all elements in other collection.
        """
        uncontained_entries = [entry for entry in other_dict.items() if entry not in self._subject.items()]
        if uncontained_entries:
            self._raise_error("doesn't contain entries <%s> in %s <%s>." %
                              (_rb(uncontained_entries), _name(other_dict), other_dict))


    def is_sub_of(self, other_dict):
        """
            Fails unless all elements in collection are in other collection.
        """
        uncontained_entries = [entry for entry in self._subject.items() if entry not in other_dict.items()]
        if uncontained_entries:
            self._raise_error("has entries <%s> not in %s <%s>." %
                              (_rb(uncontained_entries), _name(other_dict), other_dict))


class _DateSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_after(self, other_day):
        """
            Fails if the day is not after other day.
        """
        if self._subject <= other_day:
            self._raise_error("is not after <%s>." % other_day)
        return self

    def is_before(self, other_day):
        """
            Fails if the subject is not less than other number.
        """
        if self._subject >= other_day:
            self._raise_error("is not before <%s>." % other_day)
        return self


class _DateTimeSubject(_DateSubject):
    def __init__(self, subject):
        _DateSubject.__init__(self, subject)

