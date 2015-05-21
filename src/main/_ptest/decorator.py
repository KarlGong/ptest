__author__ = 'karl.gong'

from enumeration import NGDecoratorType, TestClassRunMode


def Test(enabled=True, description="", tags=[]):
    def handle_func(func):
        func.__ng_type__ = NGDecoratorType.Test
        func.__enabled__ = enabled
        func.__description__ = description
        func.__tags__ = sorted(tags)
        return func

    return handle_func


def BeforeMethod(enabled=True, description=""):
    def handle_func(func):
        func.__ng_type__ = NGDecoratorType.BeforeMethod
        func.__enabled__ = enabled
        func.__description__ = description
        return func

    return handle_func


def AfterMethod(enabled=True, always_run=False, description=""):
    def handle_func(func):
        func.__ng_type__ = NGDecoratorType.AfterMethod
        func.__enabled__ = enabled
        func.__always_run__ = always_run
        func.__description__ = description
        return func

    return handle_func


def TestClass(enabled=True, run_mode=TestClassRunMode.Parallel, description=""):
    def tracer(cls):
        cls.__full_name__ = str(cls)
        cls.__ng_type__ = NGDecoratorType.TestClass
        cls.__enabled__ = enabled
        cls.__run_mode__ = run_mode
        cls.__description__ = description
        cls.__before_method__ = None
        cls.__after_method__ = None

        # reflect the before method and after method
        for element in dir(cls):
            attr = getattr(cls, element)
            try:
                ng_type = attr.__ng_type__
                is_enabled = attr.__enabled__
            except AttributeError:
                continue
            if is_enabled:
                if ng_type == NGDecoratorType.BeforeMethod:
                    cls.__before_method__ = attr
                elif ng_type == NGDecoratorType.AfterMethod:
                    cls.__after_method__ = attr
        return cls

    return tracer