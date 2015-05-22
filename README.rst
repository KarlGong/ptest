ptest
=====
ptest is light testing framework for Python.

Install ptest
-------------
To install ptest, simple:
::
	$ pip install ptest

Example
-------
You can specify test class, test, before method, after method by adding decorator @TestClass, @Test, @BeforeMethod, @AfterMethod.

c:\\test.py
.. code-block:: python
	from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
	from ptest.assertion import assert_equals, assert_true, fail
	
	@TestClass(run_mode="singleline")
	class PTestClass:
		def __init__(self):
			self.expected = 1

		@BeforeMethod(description="Prepare test data.")
		def before(self):
			self.expected = 10
	
		@Test(tags=["regression"])
		def test1(self):
			assert_equals(10, self.expected) # pass
	
		@Test(tags=["smoke"])
		def test2(self):
			assert_true(False) # failed
	
		@Test(enabled=False)
		def test3(self):
			fail("failed") # won't be run
	
		@AfterMethod(always_run=True, description="Clean up")
		def after(self):
		self.expected = None

Then start to execute the tests.
Use -w to specify the workspace and -t to specify the target.
::
	$ ptest -w c: -t test

The target can be package/module/class/method.
If the target is package/module/class, all the test cases under target will be executed.
::
	$ ptest -t pack.sub.module.class

If you have multiple targets, just separate them by comma.
::
	$ ptest -t packa.mo,packb
