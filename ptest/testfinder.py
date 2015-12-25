import copy
import importlib
import os

from .enumeration import PDecoratorType
from .testfilter import TestClassNameFilter, TestCaseNameFilter

__author__ = 'karl.gong'

class TestFinder:
    def __init__(self, test_target, test_class_filter_group, test_case_filter_group, target_test_suite):
        self.test_target = test_target
        self.test_class_filter_group = copy.deepcopy(test_class_filter_group)
        self.test_case_filter_group = copy.deepcopy(test_case_filter_group)
        self.target_test_suite = target_test_suite
        self.found_test_case_count = 0
        self.repeated_test_case_count = 0

    def find_test_case(self):
        splitted_test_target = self.test_target.split(".")
        module_ref = None
        module_name_len = 0
        for i in range(len(splitted_test_target)):
            try:
                module_ref = importlib.import_module(".".join(splitted_test_target[:i + 1]))
                module_name_len = i + 1
            except ImportError as e:
                if splitted_test_target[i] in str(e):
                    break
                raise e

        if module_ref is None:
            raise ImportError("Test target <%s> is invalid.\nNo module named <%s>."% (self.test_target, splitted_test_target[0]))

        test_target_len = len(splitted_test_target)
        if module_name_len == test_target_len:
            if "__init__.py" in module_ref.__file__:
                # test target is package
                self.find_test_cases_in_package(module_ref)
            else:
                # test target is module
                self.find_test_cases_in_module(module_ref)
        elif module_name_len == test_target_len - 1:
            # test target is class
            self.test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-1]))
            self.find_test_cases_in_module(module_ref)
        elif module_name_len == test_target_len - 2:
            # test target is method
            self.test_class_filter_group.append_filter(TestClassNameFilter(splitted_test_target[-2]))
            self.test_case_filter_group.append_filter(TestCaseNameFilter(splitted_test_target[-1]))
            self.find_test_cases_in_module(module_ref)
        raise ImportError("Test target <%s> is probably invalid.\nModule <%s> exists but module <%s> doesn't."% (
            self.test_target, ".".join(splitted_test_target[:module_name_len]), ".".join(splitted_test_target[:module_name_len + 1])))

    def find_test_cases_in_package(self, package_ref):
        package_name = package_ref.__name__
        package_path, _ = os.path.split(package_ref.__file__)
        for fn in os.listdir(package_path):
            file_path = os.path.join(package_path, fn)
            if os.path.isdir(file_path) and "__init__.py" in os.listdir(file_path):
                self.find_test_cases_in_package(importlib.import_module(package_name + "." + fn))
            elif os.path.isfile(file_path):
                file_name, file_ext = os.path.splitext(fn)
                if fn != "__init__.py" and file_ext == ".py":
                    self.find_test_cases_in_module(importlib.import_module(package_name + "." + file_name))

    def find_test_cases_in_module(self, module_ref):
        test_class_refs = []
        for module_element in dir(module_ref):
            test_class_ref = getattr(module_ref, module_element)
            try:
                pd_type = test_class_ref.__pd_type__
                is_enabled = test_class_ref.__enabled__
            except AttributeError:
                continue
            if pd_type == PDecoratorType.TestClass and is_enabled and self.test_class_filter_group.filter(
                    test_class_ref):
                test_class_refs.append(test_class_ref)
        if len(test_class_refs) != 0:
            for test_class_ref in test_class_refs:
                self.find_test_cases_in_class(test_class_ref)

    def find_test_cases_in_class(self, test_class_ref):
        test_case_refs = []
        for class_element in dir(test_class_ref):
            test_case_ref = getattr(test_class_ref, class_element)
            try:
                pd_type = test_case_ref.__pd_type__
                is_enabled = test_case_ref.__enabled__
            except AttributeError:
                continue
            if pd_type == PDecoratorType.Test and is_enabled and self.test_case_filter_group.filter(test_case_ref):
                test_case_refs.append(getattr(test_class_ref(), class_element))
        if len(test_case_refs) != 0:
            for test_case_ref in test_case_refs:
                self.found_test_case_count += 1
                if not self.target_test_suite.add_test_case(test_class_ref(), test_case_ref):
                    self.repeated_test_case_count += 1
