import os
import traceback
from io import BytesIO

from . import config
from .exceptions import ScreenshotError
from .plogger import preporter

# ----------------------------------------------------------------------
# -------- [ cross-platform multiple screenshots module ] --------------
# ----------------------------------------------------------------------
'''
    Copyright (c) 2013-2015, Mickael 'Tiger-222' Schoentgen

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby
    granted, provided that the above copyright notice appear in all copies
    and that both that copyright notice and this permission notice appear
    in supporting documentation or portions thereof, including
    modifications, that you make.
'''
from struct import pack
from platform import system
from zlib import compress, crc32

if system() == 'Darwin':
    try:
        import Quartz
        from LaunchServices import kUTTypePNG
        pyobjc_installed = True
    except ImportError:
        pyobjc_installed = False
elif system() == 'Windows':
    from ctypes import c_void_p, create_string_buffer, sizeof, \
        windll, Structure, POINTER, WINFUNCTYPE
    from ctypes.wintypes import BOOL, DOUBLE, DWORD, HBITMAP, HDC, \
        HGDIOBJ, HWND, INT, LPARAM, LONG, RECT, UINT, WORD


    class BITMAPINFOHEADER(Structure):
        _fields_ = [('biSize', DWORD), ('biWidth', LONG), ('biHeight', LONG),
                    ('biPlanes', WORD), ('biBitCount', WORD),
                    ('biCompression', DWORD), ('biSizeImage', DWORD),
                    ('biXPelsPerMeter', LONG), ('biYPelsPerMeter', LONG),
                    ('biClrUsed', DWORD), ('biClrImportant', DWORD)]


    class BITMAPINFO(Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', DWORD * 3)]


class MSS(object):
    def enum_display_monitors(self, screen=0):
        raise NotImplementedError('MSS: subclasses need to implement this!')

    def get_pixels(self, monitor):
        raise NotImplementedError('MSS: subclasses need to implement this!')

    def save(self, output, screen=0):
        for i, monitor in enumerate(self.enum_display_monitors(screen)):
            if screen <= 0 or (screen > 0 and i + 1 == screen):
                self.save_img(data=self.get_pixels(monitor),
                              width=monitor[b'width'],
                              height=monitor[b'height'],
                              output=output)

    def save_img(self, data, width, height, output):
        zcrc32 = crc32
        zcompr = compress
        len_sl = width * 3
        scanlines = b''.join(
            [b'0' + data[y * len_sl:y * len_sl + len_sl]
             for y in range(height)])

        magic = pack(b'>8B', 137, 80, 78, 71, 13, 10, 26, 10)

        # Header: size, marker, data, CRC32
        ihdr = [b'', b'IHDR', b'', b'']
        ihdr[2] = pack(b'>2I5B', width, height, 8, 2, 0, 0, 0)
        ihdr[3] = pack(b'>I', zcrc32(b''.join(ihdr[1:3])) & 0xffffffff)
        ihdr[0] = pack(b'>I', len(ihdr[2]))

        # Data: size, marker, data, CRC32
        idat = [b'', b'IDAT', b'', b'']
        idat[2] = zcompr(scanlines, 9)
        idat[3] = pack(b'>I', zcrc32(b''.join(idat[1:3])) & 0xffffffff)
        idat[0] = pack(b'>I', len(idat[2]))

        # Footer: size, marker, None, CRC32
        iend = [b'', b'IEND', b'', b'']
        iend[3] = pack(b'>I', zcrc32(iend[1]) & 0xffffffff)
        iend[0] = pack(b'>I', len(iend[2]))

        try:
            output.write(magic + b''.join(ihdr) + b''.join(idat) + b''.join(iend))
        except:
            err = 'MSS: error writing data to "{0}".'.format(output)
            raise ScreenshotError(err)


class MSSMac(MSS):
    def enum_display_monitors(self, screen=0):
        if screen == -1:
            rect = Quartz.CGRectInfinite
            yield ({
                b'left': int(rect.origin.x),
                b'top': int(rect.origin.y),
                b'width': int(rect.size.width),
                b'height': int(rect.size.height)
            })
        else:
            max_displays = 32  # Could be augmented, if needed ...
            rotations = {0.0: 'normal', 90.0: 'right', -90.0: 'left'}
            _, ids, _ = Quartz.CGGetActiveDisplayList(max_displays, None, None)
            for display in ids:
                rect = Quartz.CGRectStandardize(Quartz.CGDisplayBounds(display))
                left, top = rect.origin.x, rect.origin.y
                width, height = rect.size.width, rect.size.height
                rot = Quartz.CGDisplayRotation(display)
                if rotations[rot] in ['left', 'right']:
                    width, height = height, width
                yield ({
                    b'left': int(left),
                    b'top': int(top),
                    b'width': int(width),
                    b'height': int(height)
                })

    def get_pixels(self, monitor):
        width, height = monitor[b'width'], monitor[b'height']
        left, top = monitor[b'left'], monitor[b'top']
        rect = Quartz.CGRect((left, top), (width, height))
        options = Quartz.kCGWindowListOptionOnScreenOnly
        winid = Quartz.kCGNullWindowID
        default = Quartz.kCGWindowImageDefault
        self.image = Quartz.CGWindowListCreateImage(rect, options, winid, default)
        if not self.image:
            raise ScreenshotError('MSS: CGWindowListCreateImage() failed.')
        return self.image

    def save_img(self, data, width, height, output):
        cf_data = Quartz.CFDataCreateMutable(Quartz.kCFAllocatorDefault, 0)
        dest = Quartz.CGImageDestinationCreateWithData(cf_data, kUTTypePNG, 1, None)
        if not dest:
            err = 'MSS: CGImageDestinationCreateWithURL() failed.'
            raise ScreenshotError(err)

        Quartz.CGImageDestinationAddImage(dest, data, None)
        if not Quartz.CGImageDestinationFinalize(dest):
            raise ScreenshotError('MSS: CGImageDestinationFinalize() failed.')

        cf_data_bytes = Quartz.CFDataGetBytes(cf_data, Quartz.CFRangeMake(0, Quartz.CFDataGetLength(cf_data)), None)
        output.write(cf_data_bytes)


class MSSWindows(MSS):
    def __init__(self):
        self._set_argtypes()
        self._set_restypes()

    def _set_argtypes(self):
        self.MONITORENUMPROC = WINFUNCTYPE(INT, DWORD, DWORD, POINTER(RECT),
                                           DOUBLE)
        windll.user32.GetSystemMetrics.argtypes = [INT]
        windll.user32.EnumDisplayMonitors.argtypes = [HDC, c_void_p,
                                                      self.MONITORENUMPROC,
                                                      LPARAM]
        windll.user32.GetWindowDC.argtypes = [HWND]
        windll.gdi32.CreateCompatibleDC.argtypes = [HDC]
        windll.gdi32.CreateCompatibleBitmap.argtypes = [HDC, INT, INT]
        windll.gdi32.SelectObject.argtypes = [HDC, HGDIOBJ]
        windll.gdi32.BitBlt.argtypes = [HDC, INT, INT, INT, INT, HDC, INT, INT,
                                        DWORD]
        windll.gdi32.DeleteObject.argtypes = [HGDIOBJ]
        windll.gdi32.GetDIBits.argtypes = [HDC, HBITMAP, UINT, UINT, c_void_p,
                                           POINTER(BITMAPINFO), UINT]

    def _set_restypes(self):
        windll.user32.GetSystemMetrics.restypes = INT
        windll.user32.EnumDisplayMonitors.restypes = BOOL
        windll.user32.GetWindowDC.restypes = HDC
        windll.gdi32.CreateCompatibleDC.restypes = HDC
        windll.gdi32.CreateCompatibleBitmap.restypes = HBITMAP
        windll.gdi32.SelectObject.restypes = HGDIOBJ
        windll.gdi32.BitBlt.restypes = BOOL
        windll.gdi32.GetDIBits.restypes = INT
        windll.gdi32.DeleteObject.restypes = BOOL

    def enum_display_monitors(self, screen=-1):
        if screen == -1:
            SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
            SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
            left = windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            right = windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            top = windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            bottom = windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            yield ({
                b'left': int(left),
                b'top': int(top),
                b'width': int(right),
                b'height': int(bottom)
            })
        else:

            def _callback(monitor, dc, rect, data):
                rct = rect.contents
                monitors.append({
                    b'left': int(rct.left),
                    b'top': int(rct.top),
                    b'width': int(rct.right - rct.left),
                    b'height': int(rct.bottom - rct.top)
                })
                return 1

            monitors = []
            callback = self.MONITORENUMPROC(_callback)
            windll.user32.EnumDisplayMonitors(0, 0, callback, 0)
            for mon in monitors:
                yield mon

    def get_pixels(self, monitor):
        width, height = monitor[b'width'], monitor[b'height']
        left, top = monitor[b'left'], monitor[b'top']
        SRCCOPY = 0xCC0020
        DIB_RGB_COLORS = BI_RGB = 0
        srcdc = memdc = bmp = None

        try:
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = width
            bmi.bmiHeader.biHeight = -height  # Why minus? See [1]
            bmi.bmiHeader.biPlanes = 1  # Always 1
            bmi.bmiHeader.biBitCount = 24
            bmi.bmiHeader.biCompression = BI_RGB
            buffer_len = height * width * 3
            self.image = create_string_buffer(buffer_len)
            srcdc = windll.user32.GetWindowDC(0)
            memdc = windll.gdi32.CreateCompatibleDC(srcdc)
            bmp = windll.gdi32.CreateCompatibleBitmap(srcdc, width, height)
            windll.gdi32.SelectObject(memdc, bmp)
            windll.gdi32.BitBlt(memdc, 0, 0, width, height, srcdc, left, top,
                                SRCCOPY)
            bits = windll.gdi32.GetDIBits(memdc, bmp, 0, height, self.image,
                                          bmi, DIB_RGB_COLORS)
            if bits != height:
                raise ScreenshotError('MSS: GetDIBits() failed.')
        finally:
            # Clean up
            if srcdc:
                windll.gdi32.DeleteObject(srcdc)
            if memdc:
                windll.gdi32.DeleteObject(memdc)
            if bmp:
                windll.gdi32.DeleteObject(bmp)

        # Replace pixels values: BGR to RGB
        self.image[2:buffer_len:3], self.image[0:buffer_len:3] = \
            self.image[0:buffer_len:3], self.image[2:buffer_len:3]
        return self.image


def mss(*args, **kwargs):
    mss_class = {
        'Darwin': MSSMac,
        'Windows': MSSWindows
    }[system()]

    return mss_class(*args, **kwargs)


# ----------------------------------------------------------------------
# ----------- [ take screenshot for webdriver or desktop ] -------------
# ----------------------------------------------------------------------
def take_screenshot():
    if config.get_option("disable_screenshot"):
        return

    from . import testexecutor
    web_drivers = testexecutor.current_executor().get_property("web_drivers")
    running_test_fixture = testexecutor.current_executor().get_property("running_test_fixture")

    if web_drivers:
        for index, web_driver in enumerate(web_drivers):
            screenshot = {
                "source": "Web Driver",
                "path": "%s-%s.png" % (running_test_fixture.full_name, index + 1)
            }
            running_test_fixture.screenshots.append(screenshot)

            try:
                screenshot["alert"] = web_driver.switch_to.alert.text
            except Exception:
                pass

            while True:
                try:
                    web_driver.switch_to.alert.dismiss()
                except Exception:
                    break

            try:
                screenshot["url"] = web_driver.current_url
            except Exception:
                pass

            try:
                screenshot["title"] = web_driver.title
            except Exception:
                pass

            try:
                with open(os.path.join(config.get_option("temp"), screenshot["path"]), mode="wb") as f:
                    f.write(web_driver.get_screenshot_as_png())
            except Exception:
                preporter.warn("Failed to take the screenshot.\n%s" % traceback.format_exc())
    else:
        if system() == 'Darwin' and not pyobjc_installed:
            preporter.warn("The package pyobjc is necessary for taking screenshot of desktop, please install it.")
            return

        screenshot = {
            "source": "Desktop",
            "path": "%s.png" % running_test_fixture.full_name
        }
        running_test_fixture.screenshots.append(screenshot)

        output = BytesIO()
        try:
            mss().save(output=output, screen=-1)  # -1 means all monitors
            with open(os.path.join(config.get_option("temp"), screenshot["path"]), mode="wb") as f:
                f.write(output.getvalue())
        except Exception:
            preporter.warn("Failed to take the screenshot.\n%s" % traceback.format_exc())
