=====
ptest
=====
ptest is a light testing framework for Python.
Using decorator to tag test classes and test cases, executing test cases by command line, and generating clear report.

Find the latest version on github: https://github.com/KarlGong/ptest or PyPI: https://pypi.python.org/pypi/ptest

Installation
------------
The last stable release is available on PyPI and can be installed with ``pip``.

::

    $ pip install ptest

Best Practice
-------------
Firstly, create a python file: *c:\\folder\\mytest.py*

You can tag test class, test, before method, after method by adding decorator @TestClass, @Test, @BeforeMethod, @AfterMethod.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import assert_equals, assert_true, fail, assert_none
    from ptest.plogger import info
    from ptest import config

    @TestClass(run_mode="parallel") # the test cases in this class will be executed by multiple threads
    class PTestClass:
        @BeforeMethod(description="Prepare test data.")
        def before(self):
            info("setting expected result.")
            self.expected = 10
    
        @Test(tags=["regression", "smoke"])
        def test1(self):
            assert_equals(10, self.expected) # pass
    
        @Test(tags="smoke, nightly")
        def test2(self):
            assert_none(config.get_property("key")) # assert the property defined via -D<key>=<value> in cmd line
            assert_true(False) # failed
    
        @Test(enabled=False) # won't be run
        def test3(self):
            fail("failed")
    
        @AfterMethod(always_run=True, description="Clean up")
        def after(self):
            info("cleaning up")


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

Contact me
----------
For information and suggestions you can contact me at karl.gong@outlook.com

Change Log
----------
1.1.0 (compared to 1.0.4)

- No extra codes are needed to support capturing screenshot for selenium test.

- Add always_run attribute to @Test.

- Add command option --disablescreenshot to disable taking screenshot for failed test fixture.

- Support group in test class.

1.0.4 (compared to 1.0.3)

- Support capture screenshot for no-selenium test.

- Optimize the html report.