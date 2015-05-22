__author__ = 'karl.gong'

from _ptest.main import main
import _ptest.decorator as decorator
import _ptest.assertion as assertion
from _ptest.config import config as config
from _ptest.listener import TestListener as TestListener
from _ptest.plogger import debug, info, warn, error, critical

if __name__ == '__main__':
    main()