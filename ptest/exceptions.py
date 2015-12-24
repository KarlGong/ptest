__author__ = 'karl.gong'

class PTestException(Exception):
    pass


class ScreenshotError(PTestException):
    pass


class ImportTestTargetError(PTestException):
    pass