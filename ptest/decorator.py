__author__ = 'karl.gong'

from ptest.enumeration import PDecoratorType, TestClassRunMode


def Test(enabled=True, always_run=False, tags=[], group="DEFAULT", description=""):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.Test
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        if isinstance(tags, str):
            tag_list = tags.split(",")
        elif isinstance(tags, list) or isinstance(tags, tuple):
            tag_list = tags
        else:
            raise Exception("Tags type %s is not supported. Please use string or list." % type(tags))
        func.__tags__ = sorted([str(tag.strip()) for tag in tag_list if tag.strip()])
        return func

    return handle_func


def BeforeMethod(enabled=True, group="DEFAULT", description=""):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeMethod
        func.__enabled__ = enabled
        func.__group__ = group
        func.__description__ = description
        return func

    return handle_func


def AfterMethod(enabled=True, always_run=False, group="DEFAULT", description=""):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterMethod
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__group__ = group
        func.__description__ = description
        return func

    return handle_func


def TestClass(enabled=True, run_mode="parallel", description=""):
    def tracer(cls):
        cls.__full_name__ = str(cls)
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
