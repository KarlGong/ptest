__author__ = 'karl.gong'

class TestListener(object):

    def on_test_suite_start(self, test_suite):
        pass

    def on_test_suite_finish(self, test_suite):
        pass

    def on_test_case_start(self, test_case):
        pass

    def on_test_case_finish(self, test_case):
        pass

test_listener  = TestListener()