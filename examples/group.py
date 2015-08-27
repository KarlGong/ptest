from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
from ptest.assertion import assert_equals
from ptest.plogger import preporter

CN_GROUP = "CN"
US_GROUP = "US"


@TestClass()
class PTestClass:
    @BeforeMethod(group=CN_GROUP)
    def before_cn(self):
        self.expected = "cn"

    @BeforeMethod(group=US_GROUP)
    def before_us(self):
        self.expected = "us"

    @Test(group=CN_GROUP)
    def test_cn(self):
        assert_equals("cn", self.expected)

    @Test(group=US_GROUP)
    def test_us(self):
        assert_equals("us", self.expected)

    @AfterMethod(group=CN_GROUP)
    def after_cn(self):
        preporter.info("cleaning up")

    @AfterMethod(group=US_GROUP)
    def after_us(self):
        preporter.info("cleaning up")
