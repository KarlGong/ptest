__author__ = 'karl.gong'

from .enumeration import PDecoratorType, TestClassRunMode


def BeforeSuite(enabled=True, description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeSuite
        func.__enabled__ = enabled
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func


def AfterSuite(enabled=True, always_run=False, description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterSuite
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func


def TestClass(enabled=True, run_mode="parallel", description=""):
    def tracer(cls):
        cls.__full_name__ = "%s.%s" % (cls.__module__, cls.__name__)
        cls.__pd_type__ = PDecoratorType.TestClass
        cls.__enabled__ = enabled
        if run_mode.lower() in [TestClassRunMode.SingleLine, TestClassRunMode.Parallel]:
            cls.__run_mode__ = run_mode.lower()
        else:
            raise Exception("Run mode %s is not supported. Please use %s or %s." % (
                run_mode, TestClassRunMode.Parallel, TestClassRunMode.SingleLine))
        cls.__description__ = description
        return cls

    return tracer


def BeforeClass(enabled=True, group="DEFAULT", description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeClass
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func


def AfterClass(enabled=True, always_run=False, group="DEFAULT", description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterClass
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func


def Test(enabled=True, tags=[], group="DEFAULT", description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.Test
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        if isinstance(tags, str):
            tag_list = tags.split(",")
        elif isinstance(tags, list) or isinstance(tags, tuple):
            tag_list = tags
        else:
            raise Exception("Tags type %s is not supported. Please use string or list." % type(tags))
        func.__tags__ = sorted([str(tag.strip()) for tag in tag_list if tag.strip()])
        func.__timeout__ = timeout
        return func

    return handle_func


def BeforeMethod(enabled=True, group="DEFAULT", description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeMethod
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func


def AfterMethod(enabled=True, always_run=False, group="DEFAULT", description="", timeout=0):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterMethod
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        func.__timeout__ = timeout
        return func

    return handle_func
