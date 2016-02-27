import traceback


class TestListener(object):
    def on_test_suite_start(self, test_suite):
        pass

    def on_test_suite_finish(self, test_suite):
        pass

    def on_test_class_start(self, test_class):
        pass

    def on_test_class_finish(self, test_class):
        pass

    def on_test_group_start(self, test_group):
        pass

    def on_test_group_finish(self, test_group):
        pass

    def on_test_case_start(self, test_case):
        pass

    def on_test_case_finish(self, test_case):
        pass


class TestListenerGroup(object):
    def __init__(self):
        self.__test_listeners = []
        self.__teamcity_test_listener = None

    def append(self, test_listener):
        if test_listener.__class__.__name__ == "TeamcityTestListener" and test_listener.__class__.__module__ == "__main__":
            self.__teamcity_test_listener = test_listener
        else:
            self.__test_listeners.append(test_listener)

    def on_test_suite_start(self, test_suite):
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_suite_start(test_suite)
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_suite_start(test_suite)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))

    def on_test_suite_finish(self, test_suite):
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_suite_finish(test_suite)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_suite_finish(test_suite)

    def on_test_class_start(self, test_class):
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_class_start(test_class)
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_class_start(test_class)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))

    def on_test_class_finish(self, test_class):
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_class_finish(test_class)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_class_finish(test_class)

    def on_test_group_start(self, test_group):
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_group_start(test_group)
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_group_start(test_group)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))

    def on_test_group_finish(self, test_group):
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_group_finish(test_group)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_group_finish(test_group)

    def on_test_case_start(self, test_case):
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_case_start(test_case)
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_case_start(test_case)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))

    def on_test_case_finish(self, test_case):
        for test_listener in self.__test_listeners:
            try:
                test_listener.on_test_case_finish(test_case)
            except Exception:
                from .plogger import pconsole
                pconsole.write_line("The test listener %s.%s raised exception:\n%s"
                                    % (test_listener.__class__.__module__, test_listener.__class__.__name__, traceback.format_exc()))
        if self.__teamcity_test_listener:
            self.__teamcity_test_listener.on_test_case_finish(test_case)


test_listeners = TestListenerGroup()
