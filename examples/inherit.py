from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
from ptest.assertion import assert_equals
from ptest.plogger import preporter


class TestBase:
    @BeforeMethod()
    def before(self):
        preporter.info("setting expected result.")
        self.expected = 10

    @AfterMethod(always_run=True)
    def after(self):
        preporter.info("cleaning up")


@TestClass()
class PTestClass(TestBase):
    @Test()
    def test1(self):
        assert_equals(10, self.expected)  # pass

    @Test()
    def test2(self):
        assert_equals(20, self.expected)  # failed
