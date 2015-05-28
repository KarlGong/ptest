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

Firstly, create a python file: *c:\\folder\\mytest.py*

.. code:: python

	from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
	from ptest.assertion import assert_equals, assert_true, fail, assert_none
	from ptest.plogger import info
	from ptest import config

	@TestClass(run_mode="singleline") # the test cases will be only executed by one thread
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
	        assert_none(config.get_property("key")) # assert the property defined via -D<key>=<value> in cmd line
	        assert_true(False) # failed
	
	    @Test(enabled=False)
	    def test3(self):
	        fail("failed") # won't be run
	
	    @AfterMethod(always_run=True, description="Clean up")
	    def after(self):
	        info("cleaning up")


Then start to execute all the testcases in module *mytest.py*.
Use -w to specify the workspace and -t to specify the target.
In this case, workspace is *c:\\folder* and target is *mytest*.

::

	$ ptest -w c:\folder -t mytest

The target can be package/module/class/method.
If the target is package/module/class, all the test cases under target will be executed.
For example, if you want to execute all the testcases under class *MyClass*, the class a is in module *mypackage.mymodule* .

::

	$ ptest -t mypackage.mymodule.MyClass

If you have multiple targets, just separate them by comma.

::

	$ ptest -t mypackagea.mymodule,mypackageb

For more options, please use -h.

::

	$ ptest -h

Selenium Support
----------------
ptest supports capturing screenshots for failed selenium test cases. But you need to make a little change to your code.

Create a python file: *c:\\folder\\seleniumtest.py*

.. code:: python

	from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
	from ptest.assertion import fail
	from selenium.webdriver import Chrome
	from ptest import testexecutor

	@TestClass(run_mode="parallel") # the test cases will be executed by multiple threads
	class SeleniumTestClass:
	    @BeforeMethod()
	    def before(self):
	        self.webdriver = Chrome()
	        # add browser to current testexecutor
	        testexecutor.update_properties(browser=self.webdriver)

	    @Test()
	    def test1(self):
	        self.webdriver.get("https://github.com/KarlGong/ptest")
	        fail()

	    @Test()
	    def test2(self):
	        self.webdriver.get("https://pypi.python.org/pypi/ptest")
	        fail()

	    @AfterMethod(always_run=True)
	    def after(self):
	        self.webdriver.quit()
	        # remove browser from current testexecutor
	        testexecutor.update_properties(browser=None)

Execute the test cases under module *seleniumtest.py* by 2 threads.
Use -n to specify the number of test executors(threads).

::

	$ ptest -w c:\folder -t seleniumtest -n 2

Contact me
----------
For information and suggestions you can contact me at karl.gong@outlook.com