import inspect
import os
import re
try:
    from urlparse import urljoin
    from urllib import unquote, pathname2url
except ImportError:
    from urllib.parse import urljoin, unquote
    from urllib.request import pathname2url

from .enumeration import PDecoratorType, TestClassRunMode


def TestClass(enabled=True, run_mode="singleline", run_group=None, description="", **custom_args):
    """
        The TestClass decorator, it is used to mark a class as TestClass.

    :param enabled: enable or disable this test class.
    :param run_mode: the run mode of all the test cases in this test class. If set to "parallel", all the test cases can be run by multiple threads. If set to "singleline", all the test cases will be only run by one thread.
    :param run_group: the run group of this test class. If run group is specified, all the test classes in the same run group will be run one by one. If not, this test class will be belong to it own run group.
    :param description: the description of this test class.
    :param custom_args: the custom arguments of this test class.
    """

    def tracer(cls):
        cls.__pd_type__ = PDecoratorType.TestClass
        cls.__enabled__ = enabled
        if run_mode.lower() in [TestClassRunMode.SingleLine, TestClassRunMode.Parallel]:
            cls.__run_mode__ = run_mode.lower()
        else:
            raise ValueError("Run mode <%s> is not supported. Please use <%s> or <%s>." % (
                run_mode, TestClassRunMode.Parallel, TestClassRunMode.SingleLine))
        cls.__run_group__ = None if run_group is None else str(run_group)
        cls.__description__ = description
        cls.__custom_args__ = custom_args
        return cls

    return tracer


def BeforeSuite(enabled=True, description="", timeout=0, **custom_args):
    """
        The BeforeSuite test fixture, it will be executed before test suite started.

    :param enabled: enable or disable this test fixture.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeSuite
        func.__enabled__ = enabled
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def BeforeClass(enabled=True, description="", timeout=0, **custom_args):
    """
        The BeforeClass test fixture, it will be executed before test class started.

    :param enabled: enable or disable this test fixture.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeClass
        func.__enabled__ = enabled
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def BeforeGroup(enabled=True, group="DEFAULT", description="", timeout=0, **custom_args):
    """
        The BeforeGroup test fixture, it will be executed before test group started.

    :param enabled: enable or disable this test fixture.
    :param group: the group that this test fixture belongs to.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeGroup
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def BeforeMethod(enabled=True, group="DEFAULT", description="", timeout=0, **custom_args):
    """
        The BeforeMethod test fixture, it will be executed before test started.

    :param enabled: enable or disable this test fixture.
    :param group: the group that this test fixture belongs to.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeMethod
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def Test(enabled=True, tags=[], expected_exceptions=None, data_provider=None, group="DEFAULT", description="", timeout=0, **custom_args):
    """
        The Test decorator, it is used to mark a test as Test.

    :param enabled: enable or disable this test.
    :param tags: the tags of this test. It can be string (separated by comma) or list or tuple.
    :param expected_exceptions: the expected exceptions of this test fixture.
        If no exception or a different one is thrown, this test will be marked as failed.
        The possible values of this parameter are::
            Exception Class:
                expected_exceptions=AttributeError
            Exception Class list or tuple:
                expected_exceptions=[AttributeError, IndexError]
                expected_exceptions=(AttributeError, IndexError)
            Exception Class and regular expression of expected message dict:
                expected_exceptions={AttributeError: '.*object has no attribute.*'}
        Note: If you want to match the entire exception message, just include anchors in the regex pattern.
    :param data_provider: the data provider for this test, the data provider must be iterable.
        Following test will be run four times with the test data supplied from data provider.
            @Test(data_provider=[(1, 1, 2), (2, 3, 5), (4, 5, 9), (9, 9, 18)])
            def test_add(self, number1, number2, sum_):
                assert_that(number1 + number2).is_equal_to(sum_)
    :param group: the group that this test belongs to.
    :param description: the description of this test.
    :param timeout: the timeout of this test (in seconds).
    :param custom_args: the custom arguments of this test.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.Test
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        # deal with tags
        if not tags:
            func.__tags__ = []
        else:
            if isinstance(tags, str):
                tag_list = tags.split(",")
            elif isinstance(tags, (list, tuple)):
                tag_list = tags
            else:
                raise ValueError(
                    "Tags type %s is not supported. Please use string (separated by comma) or list or tuple." % type(tags))
            func.__tags__ = sorted([str(tag).strip() for tag in tag_list if str(tag).strip()])
        # deal with expected exceptions
        if not expected_exceptions:
            func.__expected_exceptions__ = None
        else:
            exceptions = {}
            if inspect.isclass(expected_exceptions):
                if issubclass(expected_exceptions, Exception):
                    exceptions[expected_exceptions] = None
                else:
                    raise ValueError("Expected exception should be a sub class of Exception.")
            elif isinstance(expected_exceptions, (tuple, list)):
                for exception in expected_exceptions:
                    if issubclass(exception, Exception):
                        exceptions[exception] = None
                    else:
                        raise ValueError("Expected exception should be a sub class of Exception.")
            elif isinstance(expected_exceptions, dict):
                for exception, message in expected_exceptions.items():
                    if issubclass(exception, Exception):
                        exceptions[exception] = re.compile(message)
                    else:
                        raise ValueError("Expected exception should be a sub class of Exception.")
            else:
                raise ValueError("Expected exceptions type %s is not supported. Please use class or list or tuple or dict."
                                 % type(expected_exceptions))
            func.__expected_exceptions__ = exceptions

        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test(func)
        func.__parameters__ = None
        func.__data_provider__ = None
        func.__unzipped__ = True
        func.__mock_funcs__ = [func]
        if data_provider:
            func.__data_provider__ = data_provider
            func.__unzipped__ = False
            func.__mock_funcs__ = []
        elif func.__arguments_count__ != 1:
            raise TypeError("Since data provider is not specified, %s() cannot be declared with %s arguments. Please declare with only 1 argument."
                            % (func.__name__, func.__arguments_count__))
        return func

    return handle_func


def AfterMethod(enabled=True, always_run=True, group="DEFAULT", description="", timeout=0, **custom_args):
    """
        The AfterMethod test fixture, it will be executed after test finished.

    :param enabled: enable or disable this test fixture.
    :param always_run: if set to true, this test fixture will be run even if the @BeforeMethod is failed. Otherwise, this test fixture will be skipped.
    :param group: the group that this test fixture belongs to.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterMethod
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def AfterGroup(enabled=True, always_run=True, group="DEFAULT", description="", timeout=0, **custom_args):
    """
        The AfterGroup test fixture, it will be executed after test group finished.

    :param enabled: enable or disable this test fixture.
    :param always_run: if set to true, this test fixture will be run even if the @BeforeGroup is failed. Otherwise, this test fixture will be skipped.
    :param group: the group that this test fixture belongs to.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterGroup
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def AfterClass(enabled=True, always_run=True, description="", timeout=0, **custom_args):
    """
        The AfterClass test fixture, it will be executed after test class finished.

    :param enabled: enable or disable this test fixture.
    :param always_run: if set to true, this test fixture will be run even if the @BeforeClass is failed. Otherwise, this test fixture will be skipped.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterClass
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def AfterSuite(enabled=True, always_run=True, description="", timeout=0, **custom_args):
    """
        The AfterSuite test fixture, it will be executed after test suite finished.

    :param enabled: enable or disable this test fixture.
    :param always_run: if set to true, this test fixture will be run even if the @BeforeSuite is failed. Otherwise, this test fixture will be skipped.
    :param description: the description of this test fixture.
    :param timeout: the timeout of this test fixture (in seconds).
    :param custom_args: the custom arguments of this test fixture.
    """

    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterSuite
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__description__ = description
        func.__timeout__ = timeout
        func.__custom_args__ = custom_args
        func.__location__ = __get_location(func)
        func.__arguments_count__ = __get_arguments_count_of_test_configuration(func)
        return func

    return handle_func


def __get_location(func):
    file_path = os.path.abspath(inspect.getfile(func))
    _, line_no = inspect.getsourcelines(func)
    return urljoin("file:", "%s:%s" % (unquote(pathname2url(file_path)), line_no))


def __get_arguments_count_of_test_configuration(func):
    arguments_count = len(inspect.getargspec(func)[0])
    if arguments_count not in [1, 2]:
        raise TypeError("%s() cannot be declared with %s arguments. Please declare with 1 or 2 arguments." % (func.__name__, arguments_count))
    return arguments_count


def __get_arguments_count_of_test(func):
    return len(inspect.getargspec(func)[0])