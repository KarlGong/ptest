from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod, BeforeSuite, BeforeClass, BeforeGroup, \
    AfterGroup, AfterClass, AfterSuite
from ptest.assertion import assert_equals, fail, assert_not_none
from ptest.plogger import preporter
from ptest import config


# the test cases in this class will be executed by multiple threads
@TestClass(run_mode="parallel")
class PTestClass:
    @BeforeSuite()
    def before_suite(self):
        preporter.info("before suite")

    @BeforeClass()
    def before_class(self):
        preporter.info("before class")

    @BeforeGroup()
    def before_group(self):
        preporter.info("before group")

    @BeforeMethod(description="Prepare test data.")
    def before(self):
        preporter.info("setting expected result.")
        self.expected = 10

    @Test(tags=["regression", "smoke"])
    def test1(self):
        assert_equals(10, self.expected)  # pass

    @Test(tags="smoke, nightly")
    def test2(self):
        # assert the property defined via -D<key>=<value> in cmd line
        assert_not_none(config.get_property("key"))

    @Test(enabled=False)  # won't be run
    def test3(self):
        fail("failed")

    # always_run means that the @AfterMethod will be run even the @BeforeMethod failed
    @AfterMethod(always_run=True, description="Clean up")
    def after(self):
        preporter.info("cleaning up")

    @AfterGroup()
    def after_group(self):
        preporter.info("after group")

    @AfterClass()
    def after_class(self):
        preporter.info("after class")

    @AfterSuite()
    def after_suite(self):
        preporter.info("after suite")
