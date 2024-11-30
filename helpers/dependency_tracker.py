from ptest.plogger import preporter
from ptest.assertion import fail
from ptest.decorator import BeforeMethod, AfterMethod


class DependencyTracker:
    _passed_tests = set()
    _failed_tests = set()
    _skipped_tests = set()

    _passed_status = "passed"
    _failed_status = "failed"

    _dependency_arg_key_name = "depends_on"

    @BeforeMethod()
    def on_test_case_start(self, test_case):
        if self.is_dependent_test_case(test_case):
            if self.is_parent_test_passed(test_case):
                preporter.info("Parent test {} has passed. Starting execution of current test case."
                               .format(self.get_parent_test_case_name(test_case)))

            elif self.is_parent_test_failed(test_case):
                preporter.warn("Parent test {} has failed. Current test case will be skipped."
                               .format(self.get_parent_test_case_name(test_case)))
                self.add_skipped_test(test_case)
                fail("Skipping test case as parent test failed.")

            elif self.is_parent_test_skipped(test_case):
                preporter.warn("Parent test {} has been skipped. Current test case will be skipped."
                               .format(self.get_parent_test_case_name(test_case)))
                self.add_skipped_test(test_case)
                fail("Skipping test case as parent test has been skipped.")

            else:
                preporter.critical("Parent test {} has not been executed! Please check naming convention of test cases "
                                   "and ensure parent test is executed first."
                                   .format(self.get_parent_test_case_name(test_case)))
                self.add_skipped_test(test_case)
                fail("Skipping test case as parent test has NOT been executed yet.")
        else:
            preporter.info("Starting execution of current test case.")

    @AfterMethod()
    def on_test_case_finish(self, test_case):
        preporter.info("Test case complete. Status: " + test_case.status)
        if self.is_test_case_passed(test_case):
            self.add_passed_test(test_case)
        elif self.is_test_case_failed(test_case):
            self.add_failed_test(test_case)

    def add_passed_test(self, test_case):
        self._passed_tests.add(test_case.full_name)

    def add_failed_test(self, test_case):
        self._failed_tests.add(test_case.full_name)

    def add_skipped_test(self, test_case):
        self._skipped_tests.add(test_case.full_name)

    def is_test_case_passed(self, test_case):
        return test_case.status == self._passed_status

    def is_test_case_failed(self, test_case):
        return test_case.status == self._failed_status

    def is_dependent_test_case(self, test_case):
        return self._dependency_arg_key_name in test_case.custom_args

    def get_parent_test_case_name(self, test_case):
        return test_case.custom_args[self._dependency_arg_key_name]

    def get_test_package_name(self, test_case):
        test_name_start_index = test_case.full_name.rfind(".")
        return test_case.full_name[:test_name_start_index]

    def get_parent_test_status(self, test_case, test_set):
        parent_test_case_full_name = self.get_test_package_name(test_case) + "." + \
                                     self.get_parent_test_case_name(test_case)
        return parent_test_case_full_name in test_set

    def is_parent_test_passed(self, test_case):
        return self.get_parent_test_status(test_case, self._passed_tests)

    def is_parent_test_failed(self, test_case):
        return self.get_parent_test_status(test_case, self._failed_tests)

    def is_parent_test_skipped(self, test_case):
        return self.get_parent_test_status(test_case, self._skipped_tests)

