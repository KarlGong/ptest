import importlib
import os
import pkgutil
import re
import sys

from .enumeration import PDecoratorType
from .utils import mock_func


class TestFinder:
    def __init__(self, test_target, test_filter_group, target_test_suite):
        self.test_target = test_target
        self.test_filter_group = test_filter_group
        self.target_test_suite = target_test_suite
        self.found_test_count = 0
        self.repeated_test_count = 0
        # test class / test case name filter
        self.test_class_name = None
        self.test_name = None
        self.is_parametric_test = None

    def find_tests(self):
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
                self.find_tests_in_package(module_ref)
            else:
                # test target is module
                self.find_tests_in_module(module_ref)
        elif module_name_len == test_target_len - 1:
            # test target is class
            self.test_class_name = splitted_test_target[-1]
            if not hasattr(module_ref, "__path__"): # ignore test cases in package
                self.find_tests_in_module(module_ref)
        elif module_name_len == test_target_len - 2:
            # test target is method
            self.test_class_name = splitted_test_target[-2]
            self.test_name = splitted_test_target[-1]
            self.is_parametric_test = re.search(r"^.*#.*$", self.test_name)
            if not hasattr(module_ref, "__path__"): # ignore test cases in package
                self.find_tests_in_module(module_ref)
        else:
            raise ImportError("Test target <%s> is probably invalid.\nModule <%s> exists but module <%s> doesn't."% (
                self.test_target, ".".join(splitted_test_target[:module_name_len]), ".".join(splitted_test_target[:module_name_len + 1])))

    def find_tests_in_package(self, package_ref):
        if sys.version_info >= (3, 3): # support namespace packages
            package_name = package_ref.__name__
            if hasattr(package_ref.__path__, "_path"):
                package_path = package_ref.__path__._path[0] # namespace package
            else:
                package_path = package_ref.__path__[0] # __init__ package
            for fn in os.listdir(package_path):
                file_path = os.path.join(package_path, fn)
                if os.path.isdir(file_path) and "." not in fn:
                    self.find_tests_in_package(importlib.import_module(package_name + "." + fn))
                elif os.path.isfile(file_path):
                    file_name, file_ext = os.path.splitext(fn)
                    if file_ext == ".py":
                        self.find_tests_in_module(importlib.import_module(package_name + "." + file_name))
        else:
            for _, name, is_package in pkgutil.iter_modules(package_ref.__path__):
                if is_package:
                    self.find_tests_in_package(importlib.import_module(package_ref.__name__ + "." + name))
                else:
                    self.find_tests_in_module(importlib.import_module(package_ref.__name__ + "." + name))

    def find_tests_in_module(self, module_ref):
        for module_element in dir(module_ref):
            test_class_cls = getattr(module_ref, module_element)
            if hasattr(test_class_cls, "__pd_type__") and test_class_cls.__pd_type__ == PDecoratorType.TestClass \
                    and hasattr(test_class_cls, "__enabled__") and test_class_cls.__enabled__ \
                    and test_class_cls.__module__ == module_ref.__name__ \
                    and (not self.test_class_name or self.test_class_name == test_class_cls.__name__):
                self.find_tests_in_class(test_class_cls)

    def find_tests_in_class(self, test_class_cls):
        for class_element in dir(test_class_cls):
            test_func = getattr(test_class_cls, class_element)
            if hasattr(test_func, "__pd_type__") and test_func.__pd_type__ == PDecoratorType.Test \
                    and hasattr(test_func, "__enabled__") and test_func.__enabled__:
                if not self.test_name:
                    for func in unzip_func(test_class_cls, test_func):
                        if self.test_filter_group.filter(func):
                            self.__add_test(test_class_cls, func)
                else:
                    if self.is_parametric_test and test_func.__data_provider__:
                        if re.search(r"^%s#.*$" % test_func.__name__, self.test_name):
                            for func in unzip_func(test_class_cls, test_func):
                                if self.test_name == func.__name__ and self.test_filter_group.filter(func):
                                    self.__add_test(test_class_cls, func)
                    elif self.test_name == test_func.__name__:
                        for func in unzip_func(test_class_cls, test_func):
                            if self.test_filter_group.filter(func):
                                self.__add_test(test_class_cls, func)

    def __add_test(self, test_class_cls, func):
        self.found_test_count += 1
        if not self.target_test_suite.add_test_case(test_class_cls, func):
            self.repeated_test_count += 1


def unzip_func(test_class_cls, test_func):
    if not test_func.__funcs__: # zipped
        name_map = {}
        for index, data in enumerate(test_func.__data_provider__):
            if isinstance(data, (list, tuple)):
                parameters_number = len(data)
                parameters = data
            else:
                parameters_number = 1
                parameters = [data]
            if parameters_number == test_func.__arguments_count__ - 1:
                mock = mock_func(test_func)
                mock_name = ("%s#%s" % (test_func.__name__, test_func.__data_name__(index, parameters))) \
                    .replace(".", "_").replace(",", "_").replace(" ", "_")
                if mock_name in name_map:
                    name_map[mock_name] += 1
                    mock.__name__ = "%s(%s)" % (mock_name, name_map[mock_name] - 1)
                else:
                    name_map[mock_name] = 1
                    mock.__name__ = mock_name
                mock.__parameters__ = parameters
                mock.__data_index__ = index
                mock.__funcs__ = [mock]
                mock.__test_class__ = test_class_cls
                test_func.__funcs__.append(mock)
            else:
                raise TypeError("The data provider is trying to pass %s extra arguments but %s.%s() takes %s."
                                % (parameters_number, test_class_cls.__name__, test_func.__name__, test_func.__arguments_count__ - 1))
    elif not test_func.__data_provider__: # normal
        test_func.__funcs__[0].__test_class__ = test_class_cls
        if test_func.__arguments_count__ != 1:
            raise TypeError("Since data provider is not specified, %s.%s() cannot be declared with %s parameters. Please declare with only 1 parameter (self)."
                            % (test_class_cls.__name__, test_func.__name__, test_func.__arguments_count__))
    return test_func.__funcs__