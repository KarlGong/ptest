__author__ = 'KarlGong'


class TestClassRunMode:
    SingleLine = "singleline"
    Parallel = "parallel"


class PDecoratorType:
    BeforeSuite = "BeforeSuite"
    AfterSuite = "AfterSuite"
    TestClass = "TestClass"
    BeforeClass = "BeforeClass"
    AfterClass = "AfterClass"
    Test = "Test"
    BeforeMethod = "BeforeMethod"
    AfterMethod = "AfterMethod"

class TestFixtureStatus:
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"

class TestCaseStatus:
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"