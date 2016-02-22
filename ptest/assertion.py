import re

__author__ = 'karl.gong'

# -------------------------------------------
# ------------ simple assertion -------------
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
    if isinstance(subject, (list, tuple)):
        return _ListOrTupleSubject(subject)
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

# this method is used to format the obj without brackets
def _rb(obj):
    return str(obj)[1:-1]

# this method is used to get the type name of the object
def _name(obj):
    return type(obj).__name__

class _Subject(object):
    def __init__(self, subject):
        self._subject = subject
        self._subject_name = None
        self._msg = None

    def named(self, name):
        """
            Give a name to the subject.
        """
        self._subject_name = str(name)
        return self

    def with_message(self, message):
        """
           Set custom message for this assertion.
        """
        self._msg = str(message)
        return self

    def _raise_error(self, partial_error_msg, error=AssertionError):
        if self._subject_name is None:
            error_msg = "Unexpectedly that the %s <%s> %s" % (_name(self._subject), self._subject, partial_error_msg)
        else:
            error_msg = "Unexpectedly that the %s named \"%s\" %s" % (_name(self._subject), self._subject_name, partial_error_msg)
        self._raise_raw_error(error_msg, error)

    def _raise_raw_error(self, error_msg, error=AssertionError):
        if self._msg:
            raise_msg = "%s\n%s" % (self._msg, error_msg)
        else:
            raise_msg = "%s" % error_msg
        raise error(raise_msg)


class _ObjSubject(_Subject):
    def __init__(self, subject):
        _Subject.__init__(self, subject)

    def is_instance_of(self, class_or_type_or_tuple):
        """
            Fails if the subject is not an instance of given class or type or tuple of types.

            Assert whether an object is an instance of a class or of a subclass thereof.
            With a type as second argument, return whether that is the object's type.
            The form using a tuple, is_instance_of(x, (A, B, ...)), is a shortcut for
            is_instance_of(x, A) or is_instance_of(x, B) or ... (etc.).
        """
        if not isinstance(self._subject, class_or_type_or_tuple):
            self._raise_error("is not instance of <%s>." % _rb(class_or_type_or_tuple))
        return self

    def is_type_of(self, type_):
        """
           Fails if the subject is not of given type.
        """
        if type(self._subject) is not type_:
            self._raise_error("is not type of %s." % type_)
        return self

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
            self._raise_error("is in %s <%s>." % (_name(iterable), iterable))
        return self

    def meets(self, func):
        """
            Fails if the subject doesn't meet the given function.
            Note: The function must accepts one argument.

            For Example:
                 assert_that(99).meets(lambda x: x > 0)

                 def is_positive(num):
                    return num > 0
                assert_that(99).meets(is_positive)
        """
        if not func(self._subject):
            self._raise_error("doesn't meet function <%s>." % func.__name__)
        return self

    def s(self, attribute_name):
        """
            Assert the attribute of this subject. If the attribute does not exist, raise AttributeError.
        """
        if not hasattr(self._subject, attribute_name):
            self._raise_error("doesn't have attribute <%s>." % attribute_name, error=AttributeError)
        return assert_that(getattr(self._subject, attribute_name))


class _NoneSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def __getattr__(self, item):
        self._raise_raw_error("Cannot perform assertion \"%s\" for <None>." % item, error=AttributeError)


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

    def length(self):
        """
            Assert the length of this subject.
        """
        return _NumericSubject(len(self._subject))

    def each(self):
        """
            For each obj in this subject.
        """
        return _IterableEachSubject(self._subject)


class _IterableEachSubject(object):
    def __init__(self, iterable_subject):
        self.__iterable_subject = iterable_subject

    def __getattr__(self, item):
        def each(*args, **kwargs):
            if item in ["length", "index", "key", "s"]:
                iterable_subject = []
                for subject in self.__iterable_subject:
                    iterable_subject.append(getattr(assert_that(subject), item)(*args, **kwargs)._subject)
                return _IterableEachSubject(iterable_subject)
            elif item in ["each"]:
                iterable_subject = []
                for iterable in self.__iterable_subject:
                    for subject in iterable:
                        iterable_subject.append(subject)
                return _IterableEachSubject(iterable_subject)
            else:
                for subject in self.__iterable_subject:
                    getattr(assert_that(subject), item)(*args, **kwargs)
                return self
        return each


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


class _ListOrTupleSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def has_same_elements_as(self, other_list_or_tuple):
        """
            Fails unless this list/tuple has the same elements as other list/tuple.
        """
        uncontained_objs = [obj for obj in other_list_or_tuple if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_list_or_tuple), other_list_or_tuple))
            
        uncontained_objs = [obj for obj in self._subject if obj not in other_list_or_tuple]
        if uncontained_objs:
            self._raise_error("contains elements <%s> not in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_list_or_tuple), other_list_or_tuple))
        return self

    def contains_duplicates(self):
        """
            Fails if this list/tuple does not contain duplicate elements.
        """
        if len(self._subject) == len(set(self._subject)):
            self._raise_error("doesn't contain duplicate elements.")
        return self

    def does_not_contain_duplicates(self):
        """
            Fails if this list/tuple contains duplicate elements.
        """
        element_counter = {}
        for element in self._subject:
            if element in element_counter:
                element_counter[element] += 1
            else:
                element_counter[element] = 1
        duplicates = [element for element, count in element_counter.items() if count > 1]
        if duplicates:
            self._raise_error("contains duplicate elements <%s>." % _rb(duplicates))
        return self

    def index(self, index):
        """
            Assert the obj of this list/tuple by index. If index doesn't exist, raise IndexError.
        """
        if index >= len(self._subject) or index < 0:
            self._raise_error("has no object of index <%s>." % index, error=IndexError)
        return assert_that(self._subject[index])


class _SetSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)
    
    def is_super_of(self, other_set):
        """
            Fails unless this set is a super set of other set.
        """
        uncontained_objs = [obj for obj in other_set if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_set), other_set))
        return self

    def is_sub_of(self, other_set):
        """
            Fails unless this set is a sub set of other set.
        """
        uncontained_objs = [obj for obj in self._subject if obj not in other_set]
        if uncontained_objs:
            self._raise_error("contains elements <%s> not in %s <%s>." %
                              (_rb(uncontained_objs), _name(other_set), other_set))
        return self


class _DictSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

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
            Fails unless this dict contains all entries in other dict.
        """
        uncontained_entries = [entry for entry in other_dict.items() if entry not in self._subject.items()]
        if uncontained_entries:
            self._raise_error("doesn't contain entries <%s> in %s <%s>." %
                              (_rb(uncontained_entries), _name(other_dict), other_dict))
        return self

    def is_sub_of(self, other_dict):
        """
            Fails unless all entries of this dict are in other dict.
        """
        uncontained_entries = [entry for entry in self._subject.items() if entry not in other_dict.items()]
        if uncontained_entries:
            self._raise_error("contains entries <%s> not in %s <%s>." %
                              (_rb(uncontained_entries), _name(other_dict), other_dict))
        return self

    def key(self, key):
        """
            Assert the value of this dict by key. If key doesn't exist, raise KeyError
        """
        if key not in self._subject:
            self._raise_error("doesn't contain key %s <%s>." % (_name(key), key), error=KeyError)
        return assert_that(self._subject[key])

    def each(self):
        """
            For each entry in this dict.
        """
        return _IterableEachSubject(self._subject.items())


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

