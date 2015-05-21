__author__ = 'KarlGong'


class TestClassRunMode:
    SingleLine = "SingleLine"
    Parallel = "Parallel"


class NGDecoratorType:
    Test = "Test"
    BeforeMethod = "BeforeMethod"
    AfterMethod = "AfterMethod"
    TestClass = "TestClass"


class TestCaseStatus:
    NOT_RUN = "Not Run"
    RUNNING = "Running"
    PASSED = "Passed"
    SKIPPED = "Skipped"
    FAILED = "Failed"