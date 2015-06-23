__author__ = 'karl.gong'

from enumeration import PDecoratorType, TestClassRunMode


def Test(enabled=True, description="", tags=[]):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.Test
        func.__enabled__ = enabled
        func.__description__ = description
        func.__tags__ = sorted(tags)
        return func

    return handle_func


def BeforeMethod(enabled=True, description=""):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.BeforeMethod
        func.__enabled__ = enabled
        func.__description__ = description
        return func

    return handle_func


def AfterMethod(enabled=True, always_run=False, description=""):
    def handle_func(func):
        func.__pd_type__ = PDecoratorType.AfterMethod
        func.__enabled__ = enabled
        func.__always_run__ = always_run
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
        cls.__before_method__ = None
        cls.__after_method__ = None

        # reflect the before method and after method
        for element in dir(cls):
            attr = getattr(cls, element)
            try:
                pd_type = attr.__pd_type__
                is_enabled = attr.__enabled__
            except AttributeError:
                continue
            if is_enabled:
                if pd_type == PDecoratorType.BeforeMethod:
                    cls.__before_method__ = attr
                elif pd_type == PDecoratorType.AfterMethod:
                    cls.__after_method__ = attr
        return cls

    return tracer