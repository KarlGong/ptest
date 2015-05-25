import threading
import traceback

import plogger


__author__ = 'karl.gong'


def take_screen_shot():
    current_thread = threading.currentThread()
    active_browser = current_thread.get_property("browser")
    # todo: support capturing multiple browsers

    if active_browser is not None:
        # todo: Dismiss alert if it is present, so the alert will not block screen capture.

        try:
            screen_shot = active_browser.get_screenshot_as_png()
        except Exception as e:
            plogger.warn("Failed to take the screenshot: \n%s\n%s" % (e.message, traceback.format_exc()))
            return

        current_thread.get_property("running_test_case_fixture").screen_shot = screen_shot

    else:
        pass  # todo: take screen shot for desktop