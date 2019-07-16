import re
import time
from datetime import datetime, date
from numbers import Number

from typing import Any, List, Set, Union, Iterable, Callable, Tuple, Dict, Type


# -------------------------------------------
# ------------ simple assertion -------------
# -------------------------------------------
def assert_true(actual: Any, msg: str = ""):
    if actual is not True:
        __raise_error(msg, "Expected: <True>, Actual: <%s>." % actual)


def assert_false(actual: Any, msg: str = ""):
    if actual is not False:
        __raise_error(msg, "Expected: <False>, Actual: <%s>." % actual)


def assert_none(actual: Any, msg: str = ""):
    if actual is not None:
        __raise_error(msg, "Expected: <None>, Actual: <%s>." % actual)


def assert_not_none(actual: Any, msg: str = ""):
    if actual is None:
        __raise_error(msg, "Expected: NOT <None>, Actual: <None>.")


def assert_equals(actual: Any, expected: Any, msg: str = ""):
    if not actual == expected:
        __raise_error(msg, "Expected: <%s>, Actual: <%s>." % (expected, actual))


def assert_not_equals(actual: Any, not_expected: Any, msg: str = ""):
    if actual == not_expected:
        __raise_error(msg, "Expected: NOT <%s>, Actual: <%s>." % (not_expected, actual))


def assert_list_equals(actual_list: List, expected_list: List, msg: str = ""):
    if len(actual_list) != len(expected_list):
        __raise_error(msg, "size of expected list <%s> is: <%s>, but size of actual list <%s> is: <%s>." %
                      (expected_list, len(expected_list), actual_list, len(actual_list)))
    for i, element in enumerate(actual_list):
        if not element == expected_list[i]:
            __raise_error(msg, "element <index: %s> of expected list <%s> is: <%s>, but element <index: %s> of actual list <%s> is: <%s>" %
                          (i, expected_list, expected_list[i], i, actual_list, actual_list[i]))


def assert_list_elements_equal(actual_list: List, expected_list: List, msg: str = ""):
    diff_elements = [element for element in actual_list if not element in expected_list]
    if len(diff_elements) != 0:
        __raise_error(msg, "expected list <%s> doesn't contain elements <%s> from actual list <%s>." % (
            expected_list, diff_elements, actual_list))
    diff_elements = [element for element in expected_list if not element in actual_list]
    if len(diff_elements) != 0:
        __raise_error(msg, "actual list <%s> doesn't contain elements <%s> from expected list <%s>." % (
            actual_list, diff_elements, expected_list))


def assert_set_contains(superset: Set, subset: Set, msg: str = ""):
    diff_elements = [element for element in subset if not element in superset]
    if len(diff_elements) != 0:
        __raise_error(msg, "Superset <%s> doesn't contain elements <%s> from subset <%s>." % (superset, diff_elements, subset))


def fail(msg: str = ""):
    __raise_error("", msg)


def __raise_error(msg: str, error_msg: str):
    if msg:
        raise_msg = "%s\n%s" % (msg, error_msg)
    else:
        raise_msg = "%s" % error_msg
    raise AssertionError(raise_msg)


# -------------------------------------------
# --------- "assert that" assertion ---------
# -------------------------------------------

SUBJECT_TYPE_MAP = {}

AllSubjects = Union["_Subject", "_ObjSubject", "_NoneSubject", "_StringSubject", "_BoolSubject", "_NumericSubject", "_ListOrTupleSubject",
                    "_SetSubject", "_DictSubject", "_DateTimeSubject", "_DateSubject", "_CallableSubject"]

IterableSubjects = Union["_Subject", "_ObjSubject", "_IterableSubject", "_StringSubject", "_ListOrTupleSubject", "_SetSubject",
                         "_DictSubject"]


def assert_that(subject: Any) -> AllSubjects:
    if subject is None:
        return _NoneSubject(subject)
    if isinstance(subject, str):
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
    if callable(subject):
        return _CallableSubject(subject)
    for subject_type, subject_class in SUBJECT_TYPE_MAP.items():
        if isinstance(subject, subject_type):
            return subject_class(subject)
    return _ObjSubject(subject)


# this method is used to format the obj
def _format(obj: Any) -> str:
    if isinstance(obj, str):
        return "\"%s\"" % obj
    if isinstance(obj, list):
        return ", ".join([_format(i) for i in obj])
    return str(obj)


# this method is used to get the type name of the object
def _type(obj: Any) -> str:
    return type(obj).__name__


class _Subject(object):
    def __init__(self, subject):
        self._subject = subject
        self._subject_name = None
        self._msg = None

    def named(self, name: str) -> AllSubjects:
        """
            Give a name to this subject.
        """
        self._subject_name = str(name)
        return self

    def with_message(self, message: str) -> AllSubjects:
        """
           Set custom message for this assertion.
        """
        self._msg = str(message)
        return self

    def _raise_error(self, partial_error_msg: str, error: Type[Exception] = AssertionError):
        error_msg = "Unexpectedly that the %s %s" % (self, partial_error_msg)
        if self._msg:
            error_msg = "%s\n%s" % (self._msg, error_msg)
        self._raise_raw_error(error_msg, error)

    def _raise_raw_error(self, error_msg: str, error: Type[Exception] = AssertionError):
        raise error(error_msg)

    def __str__(self):
        if self._subject_name is None:
            return "%s <%s>" % (_type(self._subject), self._subject)
        else:
            return "%s named \"%s\"" % (_type(self._subject), self._subject_name)


class _ObjSubject(_Subject):
    def __init__(self, subject):
        _Subject.__init__(self, subject)

    def is_instance_of(self, class_or_type_or_tuple) -> AllSubjects:
        """
            Fails unless this subject is an instance of given class or type or tuple of types.

            Assert whether an object is an instance of a class or of a subclass thereof.
            With a type as second argument, return whether that is the object's type.
            The form using a tuple, is_instance_of(x, (A, B, ...)), is a shortcut for
            is_instance_of(x, A) or is_instance_of(x, B) or ... (etc.).
        """
        if not isinstance(self._subject, class_or_type_or_tuple):
            self._raise_error("is not instance of <%s>." % _format(class_or_type_or_tuple))
        return self

    def is_type_of(self, type_) -> AllSubjects:
        """
           Fails unless this subject is of given type.
        """
        if type(self._subject) is not type_:
            self._raise_error("is not type of %s." % type_)
        return self

    def is_equal_to(self, other_obj: Any) -> AllSubjects:
        """
            Fails unless this subject is equal to other obj.
        """
        if not self._subject == other_obj:
            self._raise_error("is not equal to %s <%s>." % (_type(other_obj), other_obj))
        return self

    def is_not_equal_to(self, other_obj: Any) -> AllSubjects:
        """
            Fails unless this subject is not equal to other obj.
        """
        if self._subject == other_obj:
            self._raise_error("is equal to %s <%s>." % (_type(other_obj), other_obj))
        return self

    def is_same_as(self, other_obj: Any) -> AllSubjects:
        """
            Fails unless this subject is identical to other obj.
        """
        if self._subject is not other_obj:
            self._raise_error("is not identical to %s <%s>." % (_type(other_obj), other_obj))
        return self

    def is_not_same_as(self, other_obj: Any) -> AllSubjects:
        """
            Fails unless this subject is not identical to other obj.
        """
        if self._subject is other_obj:
            self._raise_error("is identical to %s <%s>." % (_type(other_obj), other_obj))
        return self

    def is_none(self: Any) -> AllSubjects:
        """
            Fails unless this subject is None.
        """
        if self._subject is not None:
            self._raise_error("is not <None>.")
        return self

    def is_not_none(self: Any) -> AllSubjects:
        """
            Fails unless this subject is not None.
        """
        if self._subject is None:
            self._raise_error("is <None>.")
        return self

    def is_in(self, iterable: Iterable) -> AllSubjects:
        """
           Fails unless this subject is equal to one element in the given iterable.
        """
        if self._subject not in iterable:
            self._raise_error("is not in %s <%s>." % (_type(iterable), iterable))
        return self

    def is_not_in(self, iterable: Iterable) -> AllSubjects:
        """
           Fails unless this subject is not equal to any element in the given iterable.
        """
        if self._subject in iterable:
            self._raise_error("is in %s <%s>." % (_type(iterable), iterable))
        return self

    def meets(self, func: Callable[[Any], Any]) -> AllSubjects:
        """
            Fails unless this subject meets the given function.
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

    def attr(self, attribute_name: str) -> AllSubjects:
        """
            Assert the attribute of this subject. If the attribute does not exist, raise AttributeError.
        """
        if not hasattr(self._subject, attribute_name):
            self._raise_error("doesn't have attribute <%s>." % attribute_name, error=AttributeError)
        return assert_that(getattr(self._subject, attribute_name))

    def has_attr(self, attribute_name: str) -> AllSubjects:
        """
            Fails unless this subject has the given attribute.
        """
        if not hasattr(self._subject, attribute_name):
            self._raise_error("doesn't have attribute <%s>." % attribute_name)
        return self

    def does_not_have_attr(self, attribute_name: str) -> AllSubjects:
        """
            Fails unless this subject doesn't have the given attribute.
        """
        if hasattr(self._subject, attribute_name):
            self._raise_error("has attribute <%s>." % attribute_name)
        return self

    def __getattr__(self, item):
        self._raise_raw_error("Cannot perform assertion \"%s\" for %s." % (item, self), error=AttributeError)


class _NoneSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)


class _BoolSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_true(self) -> "_BoolSubject":
        """
            Fails unless this subject is true.
        """
        if self._subject is not True:
            self._raise_error("is not <True>.")
        return self

    def is_false(self) -> "_BoolSubject":
        """
            Fails unless this subject is false.
        """
        if self._subject is not False:
            self._raise_error("is not <False>.")
        return self


class _NumericSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_less_than(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is less than other number.
        """
        if self._subject >= other_number:
            self._raise_error("is not less than %s <%s>." % (_type(other_number), other_number))
        return self

    def is_greater_than(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is greater than other number.
        """
        if self._subject <= other_number:
            self._raise_error("is not greater than %s <%s>." % (_type(other_number), other_number))
        return self

    def is_less_than_or_equal_to(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is less than or equal to other number.
        """
        if self._subject > other_number:
            self._raise_error("is greater than %s <%s>." % (_type(other_number), other_number))
        return self

    def is_at_most(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is less than or equal to other number.
        """
        return self.is_less_than_or_equal_to(other_number)

    def is_greater_than_or_equal_to(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is greater than or equal to other number.
        """
        if self._subject < other_number:
            self._raise_error("is less than %s <%s>." % (_type(other_number), other_number))
        return self

    def is_at_least(self, other_number: Number) -> "_NumericSubject":
        """
            Fails unless this subject is greater than or equal to other number.
        """
        return self.is_greater_than_or_equal_to(other_number)

    def is_zero(self) -> "_NumericSubject":
        """
            Fails unless this subject is zero (0).
        """
        if self._subject != 0:
            self._raise_error("is not <0>.")
        return self

    def is_not_zero(self) -> "_NumericSubject":
        """
            Fails unless this subject is not zero (0).
        """
        if self._subject == 0:
            self._raise_error("is <0>.")
        return self

    def is_positive(self) -> "_NumericSubject":
        """
            Fails unless this subject is positive.
        """
        if self._subject <= 0:
            self._raise_error("is not positive.")
        return self

    def is_negative(self) -> "_NumericSubject":
        """
            Fails unless this subject is negative.
        """
        if self._subject >= 0:
            self._raise_error("is not negative.")
        return self

    def is_between(self, low: Number, high: Number) -> "_NumericSubject":
        """
            Fails unless this subject is between low and high.

            Note: low and high are included
        """
        if self._subject < low or self._subject > high:
            self._raise_error("is not between low %s <%s> and high %s <%s>." % (_type(low), low, _type(high), high))
        return self


class _IterableSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_empty(self) -> IterableSubjects:
        """
            Fails unless this subject is empty.
        """
        if len(self._subject) != 0:
            self._raise_error("is not empty.")
        return self

    def is_not_empty(self) -> IterableSubjects:
        """
            Fails unless this subject is not empty.
        """
        if len(self._subject) == 0:
            self._raise_error("is empty.")
        return self

    def has_length(self, expected_length: int) -> IterableSubjects:
        """
            Fails unless this subject has the given length.
        """
        if not len(self._subject) == expected_length:
            self._raise_error("doesn't have a length of <%s>. It is <%s>." % (expected_length, len(self._subject)))
        return self

    def contains(self, obj: Any) -> IterableSubjects:
        """
            Fails unless this subject contains the given object.
        """
        if obj not in self._subject:
            self._raise_error("doesn't contain %s <%s>." % (_type(obj), obj))
        return self

    def does_not_contain(self, obj: Any) -> IterableSubjects:
        """
            Fails unless this subject doesn't contain the given object.
        """
        if obj in self._subject:
            self._raise_error("contains %s <%s>." % (_type(obj), obj))
        return self

    def contains_all_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless this subject contains all the elements in the given iterable.
        """
        uncontained_objs = [obj for obj in iterable if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." % (_format(uncontained_objs), _type(iterable), iterable))
        return self

    def is_all_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless all the elements in this subject are in the given iterable.
        """
        uncontained_objs = [obj for obj in self._subject if obj not in iterable]
        if uncontained_objs:
            self._raise_error("has elements <%s> not in %s <%s>." % (_format(uncontained_objs), _type(iterable), iterable))
        return self

    def contains_any_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless this subject contains any element in the given iterable.
        """
        contained_objs = [obj for obj in iterable if obj in self._subject]
        if not contained_objs:
            self._raise_error("doesn't contain any element in %s <%s>." % (_type(iterable), iterable))
        return self

    def is_any_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless any element in this subject is in given iterable.
        """
        contained_objs = [obj for obj in self._subject if obj in iterable]
        if not contained_objs:
            self._raise_error("doesn't have any element in %s <%s>." % (_type(iterable), iterable))
        return self

    def contains_none_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless this subject doesn't contain any element in the given iterable.
        """
        contained_objs = [obj for obj in iterable if obj in self._subject]
        if contained_objs:
            self._raise_error("contains elements <%s> in %s <%s>." % (_format(contained_objs), _type(iterable), iterable))
        return self

    def is_none_in(self, iterable: Iterable) -> IterableSubjects:
        """
            Fails unless any element in this subject is not in the given iterable.
        """
        contained_objs = [obj for obj in self._subject if obj in iterable]
        if contained_objs:
            self._raise_error("has elements <%s> in %s <%s>." % (_format(contained_objs), _type(iterable), iterable))
        return self

    def length(self) -> "_NumericSubject":
        """
            Assert the length of this subject.
        """
        return _NumericSubject(len(self._subject))

    def each(self) -> AllSubjects:
        """
            For each obj in this subject.
        """
        return _IterableEachSubject(self._subject)


class _IterableEachSubject(object):
    def __init__(self, iterable_subject):
        self._iterable_subject = iterable_subject

    def __getattr__(self, item):
        if item in ["length", "index", "key", "attr"]:
            def each_attr(*args, **kwargs):
                iterable_subject = []
                for subject in self._iterable_subject:
                    iterable_subject.append(getattr(assert_that(subject), item)(*args, **kwargs)._subject)
                return _IterableEachSubject(iterable_subject)

            return each_attr
        elif item in ["each", "each_key", "each_value"]:
            def each_each(*args, **kwargs):
                iterable_subject = []
                for iterable in self._iterable_subject:
                    for subject in getattr(assert_that(iterable), item)(*args, **kwargs)._iterable_subject:
                        iterable_subject.append(subject)
                return _IterableEachSubject(iterable_subject)

            return each_each
        else:
            def assert_each(*args, **kwargs):
                for subject in self._iterable_subject:
                    getattr(assert_that(subject), item)(*args, **kwargs)
                return self

            return assert_each


class _StringSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def is_equal_to_ignoring_case(self, string: str) -> "_StringSubject":
        """
            Fails unless this string is equal to other string ignoring case.
        """
        if not self._subject.lower() == string.lower():
            self._raise_error("is not equal to %s <%s> ignoring case." % (_type(string), string))
        return self

    def is_blank(self) -> "_StringSubject":
        """
            Fails unless this string is blank.
        """
        if len(self._subject.strip()) != 0:
            self._raise_error("is not blank.")
        return self

    def is_not_blank(self) -> "_StringSubject":
        """
            Fails unless this string is not blank.
        """
        if len(self._subject.strip()) == 0:
            self._raise_error("is blank.")
        return self

    def starts_with(self, prefix: str) -> "_StringSubject":
        """
            Fails unless this string starts with the given string.
        """
        if not self._subject.startswith(prefix):
            self._raise_error("doesn't start with %s <%s>." % (_type(prefix), prefix))
        return self

    def ends_with(self, suffix: str) -> "_StringSubject":
        """
            Fails unless this string ends with the given string.
        """
        if not self._subject.endswith(suffix):
            self._raise_error("doesn't end with %s <%s>." % (_type(suffix), suffix))
        return self

    def matches(self, regex: str) -> "_StringSubject":
        """
            Fails unless this string matches the given regex.

            Note: If you want to match the entire string, just include anchors in the regex pattern.
        """
        if not re.compile(regex).search(self._subject):
            self._raise_error("doesn't match regex <%s>." % regex)
        return self

    def does_not_match(self, regex: str) -> "_StringSubject":
        """
            Fails unless this string doesn't match the given regex.

            Note: If you want to match the entire string, just include anchors in the regex pattern.
        """
        if re.compile(regex).search(self._subject):
            self._raise_error("matches regex <%s>." % regex)
        return self

    def is_alpha(self) -> "_StringSubject":
        """
            Fails unless this string contains only alphabetic chars.
        """
        if not self._subject.isalpha():
            self._raise_error("doesn't contain only alphabetic chars.")
        return self

    def is_digit(self) -> "_StringSubject":
        """
            Fails unless this string contains only digits.
        """
        if not self._subject.isdigit():
            self._raise_error("doesn't contain only digits.")
        return self

    def is_lower(self) -> "_StringSubject":
        """
            Fails unless this string contains only lowercase chars.
        """
        if not self._subject == self._subject.lower():
            self._raise_error("doesn't contain only lowercase chars.")
        return self

    def is_upper(self) -> "_StringSubject":
        """
            Fails unless this string contains only uppercase chars.
        """
        if not self._subject == self._subject.upper():
            self._raise_error("doesn't contain only uppercase chars.")
        return self


class _ListOrTupleSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def has_same_elements_as(self, other_list_or_tuple: Union[List, Tuple]) -> "_ListOrTupleSubject":
        """
            Fails unless this list/tuple has the same elements as other list/tuple.
        """
        uncontained_objs = [obj for obj in other_list_or_tuple if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." %
                              (_format(uncontained_objs), _type(other_list_or_tuple), other_list_or_tuple))

        uncontained_objs = [obj for obj in self._subject if obj not in other_list_or_tuple]
        if uncontained_objs:
            self._raise_error("contains elements <%s> not in %s <%s>." %
                              (_format(uncontained_objs), _type(other_list_or_tuple), other_list_or_tuple))
        return self

    def contains_duplicates(self) -> "_ListOrTupleSubject":
        """
            Fails unless this list/tuple contains duplicate elements.
        """
        if len(self._subject) == len(set(self._subject)):
            self._raise_error("doesn't contain duplicate elements.")
        return self

    def does_not_contain_duplicates(self) -> "_ListOrTupleSubject":
        """
            Fails unless this list/tuple doesn't contain duplicate elements.
        """
        element_counter = {}
        for element in self._subject:
            if element in element_counter:
                element_counter[element] += 1
            else:
                element_counter[element] = 1
        duplicates = [element for element, count in element_counter.items() if count > 1]
        if duplicates:
            self._raise_error("contains duplicate elements <%s>." % _format(duplicates))
        return self

    def index(self, index: int) -> AllSubjects:
        """
            Assert the obj of this list/tuple by index. If index doesn't exist, raise IndexError.
        """
        if index >= len(self._subject) or index < 0:
            self._raise_error("has no object of index <%s>." % index, error=IndexError)
        return assert_that(self._subject[index])


class _SetSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def is_super_of(self, other_set: Set) -> "_SetSubject":
        """
            Fails unless this set is a superset of other set.
        """
        uncontained_objs = [obj for obj in other_set if obj not in self._subject]
        if uncontained_objs:
            self._raise_error("doesn't contain elements <%s> in %s <%s>." % (_format(uncontained_objs), _type(other_set), other_set))
        return self

    def is_sub_of(self, other_set: Set) -> "_SetSubject":
        """
            Fails unless this set is a subset of other set.
        """
        uncontained_objs = [obj for obj in self._subject if obj not in other_set]
        if uncontained_objs:
            self._raise_error("contains elements <%s> not in %s <%s>." % (_format(uncontained_objs), _type(other_set), other_set))
        return self


class _DictSubject(_IterableSubject):
    def __init__(self, subject):
        _IterableSubject.__init__(self, subject)

    def contains_key(self, key: Any) -> "_DictSubject":
        """
            Fails unless this dict contains the given key.
        """
        if key not in self._subject:
            self._raise_error("doesn't contain key %s <%s>." % (_type(key), key))
        return self

    def does_not_contain_key(self, key: Any) -> "_DictSubject":
        """
            Fails unless this dict doesn't contain the given key.
        """
        if key in self._subject:
            self._raise_error("contains key %s <%s>." % (_type(key), key))
        return self

    def contains_value(self, value: Any) -> "_DictSubject":
        """
            Fails unless this dict contains the given value.
        """
        if value not in self._subject.values():
            self._raise_error("doesn't contain value %s <%s>." % (_type(value), value))
        return self

    def does_not_contain_value(self, value: Any) -> "_DictSubject":
        """
            Fails unless this dict doesn't contain the given value.
        """
        if value in self._subject.values():
            self._raise_error("contains value %s <%s>." % (_type(value), value))
        return self

    def contains_entry(self, key: Any, value: Any) -> "_DictSubject":
        """
           Fails unless this dict contains the given entry.
        """
        if (key, value) not in self._subject.items():
            self._raise_error("doesn't contain entry, key: %s <%s>, value: %s <%s>." % (_type(key), key, _type(value), value))
        return self

    def does_not_contain_entry(self, key: Any, value: Any) -> "_DictSubject":
        """
            Fails unless this dict doesn't contain the given entry.
        """
        if (key, value) in self._subject.items():
            self._raise_error("contains entry, key: %s <%s>, value: %s <%s>." % (_type(key), key, _type(value), value))
        return self

    def is_super_of(self, other_dict: Dict) -> "_DictSubject":
        """
            Fails unless this dict contains all the entries in other dict.
        """
        uncontained_entries = [entry for entry in other_dict.items() if entry not in self._subject.items()]
        if uncontained_entries:
            self._raise_error("doesn't contain entries <%s> in %s <%s>." %
                              (_format(uncontained_entries), _type(other_dict), other_dict))
        return self

    def is_sub_of(self, other_dict: Dict) -> "_DictSubject":
        """
            Fails unless all the entries in this dict are in other dict.
        """
        uncontained_entries = [entry for entry in self._subject.items() if entry not in other_dict.items()]
        if uncontained_entries:
            self._raise_error("contains entries <%s> not in %s <%s>." %
                              (_format(uncontained_entries), _type(other_dict), other_dict))
        return self

    def key(self, key: Any) -> AllSubjects:
        """
            Assert the value of this dict by key. If key doesn't exist, raise KeyError
        """
        if key not in self._subject:
            self._raise_error("doesn't contain key %s <%s>." % (_type(key), key), error=KeyError)
        return assert_that(self._subject[key])

    def each(self) -> "_ListOrTupleSubject":
        """
            For each entry in this dict.
        """
        return _IterableEachSubject(self._subject.items())

    def each_key(self) -> AllSubjects:
        """
            For each key in this dict.
        """
        return _IterableEachSubject(self._subject.keys())

    def each_value(self) -> AllSubjects:
        """
            For each value in this dict.
        """
        return _IterableEachSubject(self._subject.values())


class _DateSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_before(self, other_date: date) -> "_DateSubject":
        """
            Fails unless this date is before other date.
        """
        if self._subject >= other_date:
            self._raise_error("is not before %s <%s>." % (_type(other_date), other_date))
        return self

    def is_after(self, other_date: date) -> "_DateSubject":
        """
            Fails unless this date is after other date.
        """
        if self._subject <= other_date:
            self._raise_error("is not after %s <%s>." % (_type(other_date), other_date))
        return self


class _DateTimeSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)

    def is_before(self, other_datetime: datetime) -> "_DateTimeSubject":
        """
            Fails unless this datetime is before other datetime.
        """
        if self._subject >= other_datetime:
            self._raise_error("is not before %s <%s>." % (_type(other_datetime), other_datetime))
        return self

    def is_after(self, other_datetime: datetime) -> "_DateTimeSubject":
        """
            Fails unless this datetime is after other datetime.
        """
        if self._subject <= other_datetime:
            self._raise_error("is not after %s <%s>." % (_type(other_datetime), other_datetime))
        return self


class _CallableSubject(_ObjSubject):
    def __init__(self, subject):
        _ObjSubject.__init__(self, subject)
        self._args = []
        self._kwargs = {}

    def with_args(self, *args, **kwargs) -> "_CallableSubject":
        self._args = args
        self._kwargs = kwargs
        return self

    def raises_exception(self, exception_class: Type[Exception]):
        """
            Fails unless this callable does't raise exception or raise wrong exception.
        """
        try:
            self._subject(*self._args, **self._kwargs)
        except Exception as e:
            if not issubclass(e.__class__, exception_class):
                self._raise_error("raises wrong exception <%s.%s>." % (e.__class__.__module__, e.__class__.__name__))
        else:
            self._raise_error("doesn't raise exception.")

    def will(self, interval: int = 1000, timeout: int = 30000) -> AllSubjects:
        """
            Failed if this callable's result doesn't match following assertions until timing out.

        :param interval: interval of asserting, in milliseconds
        :param timeout: timeout of asserting, in milliseconds
        """
        return _CallableWillSubject(self._subject, interval, timeout, self._args, self._kwargs)


class _CallableWillSubject(object):
    def __init__(self, subject, interval, timeout, args, kwargs):
        self._subject = subject
        self._interval = interval
        self._timeout = timeout
        self._args = args
        self._kwargs = kwargs

    def __getattr__(self, item):
        if item in ["length", "index", "key", "attr", "each", "each_key", "each_value"]:
            raise AttributeError("Cannot call \"%s\" in callable-will assertion." % item)

        def wrapper(*args, **kwargs):
            start_time = time.time() * 1000.0

            last_exception = {"value": None}

            try:
                getattr(assert_that(self._subject(*self._args, **self._kwargs)), item)(*args, **kwargs)
            except AssertionError as e:
                last_exception["value"] = e
            else:
                return self

            while (time.time() * 1000.0 - start_time) <= self._timeout:
                time.sleep(self._interval / 1000.0)
                try:
                    getattr(assert_that(self._subject(*self._args, **self._kwargs)), item)(*args, **kwargs)
                except AssertionError as e:
                    last_exception["value"] = e
                else:
                    return self

            raise AssertionError("Callable's result doesn't match expected until timing out, last assertion error is:\n%s" %
                                 last_exception["value"])

        return wrapper
