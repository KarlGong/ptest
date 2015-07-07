import traceback
import StringIO

import testexecutor
import plogger
import config

try:
    from PIL import ImageGrab
except ImportError:
    PIL_installed = False
else:
    PIL_installed = True

try:
    import wx
except ImportError:
    wxpython_installed = False
else:
    wxpython_installed = True

__author__ = 'karl.gong'


def take_screen_shot():
    if config.get_option("disable_screenshot"):
        return

    active_browser = testexecutor.get_property("browser")

    if active_browser is not None:
        while True:
            try:
                active_browser.switch_to.alert.dismiss()
            except Exception:
                break

        def capture_screen():
            return active_browser.get_screenshot_as_png()
    elif PIL_installed:
        def capture_screen():
            output = StringIO.StringIO()
            ImageGrab.grab().save(output, format="png")
            return output.getvalue()
    elif wxpython_installed:
        def capture_screen():
            app = wx.App(False)
            screen = wx.ScreenDC()
            width, height = screen.GetSize()
            bmp = wx.EmptyBitmap(width, height)
            mem = wx.MemoryDC(bmp)
            mem.Blit(0, 0, width, height, screen, 0, 0)
            output = StringIO.StringIO()
            bmp.ConvertToImage().SaveStream(output, wx.BITMAP_TYPE_PNG)
            return output.getvalue()
    else:
        plogger.warn("The package PIL or wxpython is necessary for taking screenshot, please install it.")
        return

    try:
        testexecutor.get_property("running_test_case_fixture").screen_shot = capture_screen()
    except Exception as e:
        plogger.warn("Failed to take the screenshot:\n%s\n%s" % (e.message, traceback.format_exc()))
