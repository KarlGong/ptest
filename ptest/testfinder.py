import copy
import importlib
import pkgutil

from .enumeration import PDecoratorType
from .testfilter import TestClassNameFilter, TestCaseNameFilter


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
                raise

        if module_ref is None:
            raise ImportError("Test target <%s> is invalid.\nNo module named <%s>."% (self.test_target, splitted_test_target[0]))

        test_target_len = len(splitted_test_target)
        if module_name_len == test_target_len:
            if hasattr(module_ref, "__path__"):
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
        else:
            raise ImportError("Test target <%s> is probably invalid.\nModule <%s> exists but module <%s> doesn't."% (
                self.test_target, ".".join(splitted_test_target[:module_name_len]), ".".join(splitted_test_target[:module_name_len + 1])))

    def find_test_cases_in_package(self, package_ref):
        for _, name, is_package in pkgutil.iter_modules(package_ref.__path__):
            if is_package:
                self.find_test_cases_in_package(importlib.import_module(package_ref.__name__ + "." + name))
            else:
                self.find_test_cases_in_module(importlib.import_module(package_ref.__name__ + "." + name))

    def find_test_cases_in_module(self, module_ref):
        for module_element in dir(module_ref):
            test_class_ref = getattr(module_ref, module_element)
            try:
                if test_class_ref.__pd_type__ == PDecoratorType.TestClass \
                        and test_class_ref.__enabled__ \
                        and test_class_ref.__module__ == module_ref.__name__ \
                        and self.test_class_filter_group.filter(test_class_ref):
                    self.find_test_cases_in_class(test_class_ref)
            except AttributeError:
                pass

    def find_test_cases_in_class(self, test_class_ref):
        for class_element in dir(test_class_ref):
            test_case_ref = getattr(test_class_ref(), class_element)
            try:
                if test_case_ref.__pd_type__ == PDecoratorType.Test \
                        and test_case_ref.__enabled__ \
                        and self.test_case_filter_group.filter(test_case_ref):
                    self.found_test_case_count += 1
                    if not self.target_test_suite.add_test_case(test_case_ref):
                        self.repeated_test_case_count += 1
            except AttributeError:
                pass