=====
ptest
=====
ptest is a light test runner for Python. With ptest, you can tag test classes & test cases by decorators, execute test cases by command line, and get clear reports.

Find the latest version on github: https://github.com/KarlGong/ptest or PyPI: https://pypi.python.org/pypi/ptest

The documentation is on github wiki: https://github.com/KarlGong/ptest/wiki/documentation

Installation
------------
The last stable release is available on PyPI and can be installed with ``pip``.

::

    $ pip install ptest

Pycharm Plugin
--------------
A Pycharm plugin for ptest is released.
Now it is easily to run/debug ptest within the IDE using the standard run configuration.
Find the latest version on JetBrains: https://plugins.jetbrains.com/plugin/7860

Best Practice
-------------
Firstly, create a python file: *c:\\folder\\mytest.py*

You can tag test class, test, before method, after method by adding decorator @TestClass, @Test, @BeforeMethod, @AfterMethod.

.. code:: python

    # c:\folder\mytest.py
    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import assert_equals, fail, assert_not_none
    from ptest.plogger import preporter
    from ptest import config

    @TestClass(run_mode="parallel")  # the test cases in this class will be executed by multiple threads
    class PTestClass:
        @BeforeMethod(description="Prepare test data.")
        def before(self):
            preporter.info("setting expected result.")
            self.expected = 10

        @Test(tags=["regression", "smoke"])
        def test1(self):
            assert_equals(10, self.expected)  # pass

        @Test(tags="smoke, nightly")
        def test2(self):
            assert_not_none(config.get_property("key"))  # assert the property defined via -D<key>=<value> in cmd line

        @Test(enabled=False)  # won't be run
        def test3(self):
            fail("failed")

        @AfterMethod(always_run=True, description="Clean up")
        def after(self):
            preporter.info("cleaning up")


Then start to execute all the testcases in module *mytest.py* with 2 threads.
Use ``-w`` to specify the workspace, ``-t`` to specify the target and ``-n`` to specify the number of test executors(threads).
In this case, workspace is *c:\\folder*, target is *mytest* and number of test executors is *2*.

*Note:* If you are using Windows, please confirm that **%python_installation_dir%\\Scripts** (e.g., C:\\Python27\\Scripts, C:\\Python35\\Scripts) is added to the PATH environment variable.

::

    Python 2.x:
     $ ptest -w c:\folder -t mytest -n 2
    Python 3.x:
     $ ptest3 -w c:\folder -t mytest -n 2

The target can be package/module/class/method.
If the target is package/module/class, all the test cases under target will be executed.
For example, if you only want to execute the test *test1* in this module.

::

    Python 2.x:
     $ ptest -w c:\folder -t mytest.PTestClass.test1
    Python 3.x:
     $ ptest3 -w c:\folder -t mytest.PTestClass.test1

For more options, please use ``-h``.

::

    Python 2.x:
     $ ptest -h
    Python 3.x:
     $ ptest3 -h

For more code examples, please refer to the ``examples`` folder in source distribution or visit https://github.com/KarlGong/ptest/tree/master/examples

Contact me
----------
For information and suggestions you can contact me at karl.gong@outlook.com
