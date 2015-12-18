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
    BeforeGroup = "BeforeGroup"
    AfterGroup = "AfterGroup"
    Test = "Test"
    BeforeMethod = "BeforeMethod"
    AfterMethod = "AfterMethod"

class TestFixtureStatus:
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"

TestCaseStatus = TestFixtureStatus


class TestCaseCountItem:
    PASSED = TestFixtureStatus.PASSED
    FAILED = TestFixtureStatus.FAILED
    SKIPPED = TestFixtureStatus.SKIPPED
    NOT_RUN = TestFixtureStatus.NOT_RUN
    TOTAL = "total"
