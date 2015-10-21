import copy
import importlib
import os
import traceback

from .enumeration import PDecoratorType
from .testsuite import default_test_suite
from .testfilter import TestClassNameFilter, TestCaseNameFilter

__author__ = 'karl.gong'


class ImportTestTargetError(Exception):
    def __init__(self, message):
        self.message = message


def find_test_cases(test_target, test_class_filter_group, test_case_filter_group):
    # make deep copies for filter group
    test_class_filter_group = copy.deepcopy(test_class_filter_group)
    test_case_filter_group = copy.deepcopy(test_case_filter_group)
    try:
        module_ref = importlib.import_module(test_target)
        if "__init__.py" in module_ref.__file__:
            # test target is package
            find_test_cases_in_package(module_ref, test_class_filter_group, test_case_filter_group)
        else:
            # test target is module
            find_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
    except ImportError:
        splitted_test_target = test_target.split(".")
        if len(splitted_test_target) < 2:
            raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))
        try:
            # test target is class
            module_ref = importlib.import_module(".".join(splitted_test_target[:-1]))
            test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-1]))
            find_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
        except ImportError:
            splitted_test_target = test_target.split(".")
            if len(splitted_test_target) < 3:
                raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))
            try:
                # test target is method
                module_ref = importlib.import_module(".".join(splitted_test_target[:-2]))
                test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-2]))
                test_case_filter_group.append_filter(TestCaseNameFilter(splitted_test_target[-1]))
                find_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group)
            except ImportError:
                raise ImportTestTargetError("Cannot import test target: %s\n%s" % (test_target, traceback.format_exc()))


def find_test_cases_in_package(package_ref, test_class_filter_group, test_case_filter_group):
    package_name = package_ref.__name__
    package_path, _ = os.path.split(package_ref.__file__)
    for fn in os.listdir(package_path):
        file_full_path = os.path.join(package_path, fn)
        if os.path.isdir(file_full_path) and "__init__.py" in os.listdir(file_full_path):
            find_test_cases_in_package(importlib.import_module(package_name + "." + fn), test_class_filter_group,
                                         test_case_filter_group)
        elif os.path.isfile(file_full_path):
            file_name, file_ext = os.path.splitext(fn)
            if fn != "__init__.py" and file_ext == ".py":
                find_test_cases_in_module(importlib.import_module(package_name + "." + file_name),
                                            test_class_filter_group, test_case_filter_group)


def find_test_cases_in_module(module_ref, test_class_filter_group, test_case_filter_group):
    test_class_refs = []
    for module_element in dir(module_ref):
        test_class_ref = getattr(module_ref, module_element)
        try:
            pd_type = test_class_ref.__pd_type__
            is_enabled = test_class_ref.__enabled__
        except AttributeError:
            continue
        if pd_type == PDecoratorType.TestClass and is_enabled and test_class_filter_group.filter(test_class_ref):
            test_class_refs.append(test_class_ref)
    if len(test_class_refs) != 0:
        for test_class_ref in test_class_refs:
            find_test_cases_in_class(test_class_ref, test_case_filter_group)


def find_test_cases_in_class(test_class_ref, test_case_filter_group):
    test_case_refs = []
    for class_element in dir(test_class_ref):
        test_case_ref = getattr(test_class_ref, class_element)
        try:
            pd_type = test_case_ref.__pd_type__
            is_enabled = test_case_ref.__enabled__
        except AttributeError:
            continue
        if pd_type == PDecoratorType.Test and is_enabled and test_case_filter_group.filter(test_case_ref):
            test_case_refs.append(getattr(test_class_ref(), class_element))
    if len(test_case_refs) != 0:
        for test_case_ref in test_case_refs:
            default_test_suite.add_test_case(test_class_ref(), test_case_ref)
