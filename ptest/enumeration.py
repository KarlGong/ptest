from enum import Enum


class TestClassRunMode(Enum):
    SingleLine = "singleline"
    Parallel = "parallel"


class PDecoratorType(Enum):
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


class TestFixtureStatus(Enum):
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"


class TestCaseStatus(Enum):
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    SKIPPED = "skipped"
    FAILED = "failed"
