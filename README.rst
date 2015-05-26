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

Example
-------
You can tag test class, test, before method, after method by adding decorator @TestClass, @Test, @BeforeMethod, @AfterMethod.

c:\\folder\\test.py

.. code:: python

	from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
	from ptest.assertion import assert_equals, assert_true, fail
	from ptest.plogger import info
	from ptest.config import config

	@TestClass(run_mode="singleline")
	class PTestClass:
	    def __init__(self):
	        self.expected = 1

	    @BeforeMethod(description="Prepare test data.")
	    def before(self):
	        info("setting expected result.")
	        self.expected = 10
	
	    @Test(tags=["regression"])
	    def test1(self):
	        assert_equals(10, self.expected) # pass
	
	    @Test(tags=["smoke"])
	    def test2(self):
	        assert_none(config.get_property("key"))
	        assert_true(False) # failed
	
	    @Test(enabled=False)
	    def test3(self):
	        fail("failed") # won't be run
	
	    @AfterMethod(always_run=True, description="Clean up")
	    def after(self):
	        info("cleaning up")


Then start to execute the tests.
Use -w to specify the workspace and -t to specify the target.

::

	$ ptest -w c:\folder -t test

The target can be package/module/class/method.
If the target is package/module/class, all the test cases under target will be executed.

::

	$ ptest -t pack.sub.module.class

If you have multiple targets, just separate them by comma.

::

	$ ptest -t packa.mo,packb

For more options, please use -h.

::

	$ ptest -h
