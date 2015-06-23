__author__ = 'KarlGong'


class TestClassRunMode:
    SingleLine = "singleline"
    Parallel = "parallel"


class PDecoratorType:
    Test = "Test"
    BeforeMethod = "BeforeMethod"
    AfterMethod = "AfterMethod"
    TestClass = "TestClass"


class TestCaseStatus:
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"