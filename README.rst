=====
ptest
=====
ptest is a light test runner for Python.
Using decorator to tag test classes and test cases, executing test cases by command line, and generating clear report.

Find the latest version on github: https://github.com/KarlGong/ptest or PyPI: https://pypi.python.org/pypi/ptest

Installation
------------
The last stable release is available on PyPI and can be installed with ``pip``.

::

    $ pip install ptest

Pycharm Plugin
--------------
A Pycharm plugin for ptest is released.
Now it is easily to run/debug ptest within the IDE using the standard run configuration.
Find the latest version on github: https://github.com/KarlGong/ptest-pycharm-plugin or JetBrains: https://plugins.jetbrains.com/plugin/7860

Best Practice
-------------
Firstly, create a python file: *c:\\folder\\mytest.py*

You can tag test class, test, before method, after method by adding decorator @TestClass, @Test, @BeforeMethod, @AfterMethod.

.. code:: python

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
Use -w to specify the workspace, -t to specify the target and -n to specify the number of test executors(threads).
In this case, workspace is *c:\\folder*, target is *mytest* and number of test executors is *2*.

::

    $ ptest -w c:\folder -t mytest -n 2

The target can be package/module/class/method.
If the target is package/module/class, all the test cases under target will be executed.
For example, if you only want to execute the test *test1* in this module.

::

    $ ptest -w c:\folder -t mytest.PTestClass.test1

For more options, please use -h.

::

    $ ptest -h

For more examples, please refer to the ``examples`` folder in source distribution.

Contact me
----------
For information and suggestions you can contact me at karl.gong@outlook.com

Change Log
----------
1.4.0 (compared to 1.3.2)

- Support @BeforeSuite, @BeforeClass, @BeforeGroup, @AfterSuite, @AfterClass, @AfterGroup

- Support timeout for test fixtures.

- Redesign the html report.

1.3.2 (compared to 1.3.1)

- Add cmd line entry points for py3.

- All temp data will be stored in temp folder.

1.3.1 (compared to 1.3.0)

- Add examples folder.

- Support declare additional arguments in test methods.

1.3.0 (compared to 1.2.2)

- Support py3.

- No extra package is needed to capture screenshot.

1.2.2 (compared to 1.2.1)

- Support default value for config.get_property().

- Add filter for test case status in html report.

1.2.1 (compared to 1.2.0)

- Support multiple test listeners.

1.2.0 (compared to 1.1.1)

- Support run/debug in Pycharm via a ptest plugin.

- Support filter test cases by group.

1.1.0 (compared to 1.0.4)

- No extra codes are needed to support capturing screenshot for selenium test.

- Add always_run attribute to @Test.

- Add command option --disablescreenshot to disable taking screenshot for failed test fixture.

- Support group in test class.

1.0.4 (compared to 1.0.3)

- Support capture screenshot for no-selenium test.

- Optimize the html report.