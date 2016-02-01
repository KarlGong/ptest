1 - Introduction
================
ptest is a light test runner for Python. With ptest, you can tag test classes & test cases by decorators, execute test cases by command line, and get clear reports.

Writing a test in ptest is typically a two-step process:

1. Write the business logic of your test and insert `ptest decorators <#2---decorators>`_ in your code.

2. `Run ptest <#3---running-ptest>`_.

The concepts used in this documentation are as follows:

- A suite is represented by one run of ptest.

- A ptest class is a python class which is decorated by **@TestClass**.

- A ptest group is a virtual container of tests under ptest class.

- A test method is a python method which is decorated by **@Test**.

A ptest test can be configured by **@BeforeXXX** and **@AfterXXX** decorators which allows to perform some Python logic before and after a certain point, these points being either of the items listed above.

2 - Decorators
==============
2.1 - Overview
--------------
Here is a quick overview of the decorators available in ptest along with their attributes.

`@TestClass <#221---test-and-testclass>`_ - the decorated class will be marked as ptest class

- `enabled <#231---enabled>`_ - whether this test class is enabled

- `run_mode <#237---run_mode>`_ - the run mode of all the test cases in this test class. If set to "parallel", all the test cases will be run by multiple threads. If set to "singleline", all the test cases will be only run by one thread.

- `run_group <#238---run_group>`_ - the run group of this test class. If run group is specified, all the test classes in the same run group will be run one by one. If not, this test class will be belong to it own run group.

- `description <#232---description>`_ - the description of this test class

- `custom_args <#233---custom_args>`_ - the custom arguments of this test class

`@Test <#221---test-and-testclass>`_ - the decorated method will be marked as ptest test

- `enabled <#231---enabled>`_ - whether this test is enabled

- `tags <#239---tags>`_ - the tags of this test (it can be string (separated by comma) or list or tuple)

- `expected_exceptions <#2310---expected_exceptions>`_ - the expected exceptions of this test fixture. If no exception or a different one is thrown, this test will be marked as failed.

- `group <#236---group>`_ - the group that this test belongs to

- `description <#232---description>`_ - the description of this test

- `timeout <#234---timeout>`_ - the timeout of this test (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test

`@BeforeSuite <#225---beforesuite,-aftersuite-and-inherit>`_ - the decorated method will be executed before test suite started

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@AfterSuite <#225---beforesuite,-aftersuite-and-inherit>`_ - the decorated method will be executed after test suite finished

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `always_run <#235---always_run>`_ - if set to true, this test fixture will be run even if the **@BeforeSuite** is failed. Otherwise, this test fixture will be skipped.

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@BeforeClass <#224---beforeclass-and-afterClass>`_ - the decorated method will be executed before test class started

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@AfterClass <#224---beforeclass-and-afterClass>`_ - the decorated method will be executed after test class finished

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `always_run <#235---always_run>`_ - if set to true, this test fixture will be run even if the **@BeforeClass** is failed. Otherwise, this test fixture will be skipped.

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@BeforeGroup <#223---beforegroup-and-aftergroup>`_ - the decorated method will be executed before test group started

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `group <#236---group>`_ - the group that this test fixture belongs to

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@AfterGroup <#223---beforegroup-and-aftergroup>`_ - the decorated method will be executed after test group finished

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `always_run <#235---always_run>`_ - if set to true, this test fixture will be run even if the **@BeforeGroup** is failed. Otherwise, this test fixture will be skipped.

- `group <#236---group>`_ - the group that this test fixture belongs to

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@BeforeMethod <#222---beforemethod-and-aftermethod>`_ - the decorated method will be executed before test started

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `group <#236---group>`_ - the group that this test fixture belongs to

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

`@AfterMethod <#222---beforemethod-and-aftermethod>`_ - the decorated method will be executed after test finished

- `enabled <#231---enabled>`_ - whether this test fixture is enabled

- `always_run <#235---always_run>`_ - if set to true, this test fixture will be run even if the **@BeforeMethod** is failed. Otherwise, this test fixture will be skipped.

- `group <#236---group>`_ - the group that this testfixture belongs to

- `description <#232---description>`_ - the description of this test fixture

- `timeout <#234---timeout>`_ - the timeout of this test fixture (in seconds)

- `custom_args <#233---custom_args>`_ - the custom arguments of this test fixture

2.2 - Usage
-----------
2.2.1 - Test and TestClass
~~~~~~~~~~~~~~~~~~~~~~~~~~
You can use **@TestClass** to mark a class as ptest class and **@Test** to mark a method as ptest test.

*Note:* By default, a ptest test belongs to the ``DEFAULT`` group.
And the ``DEFAULT`` group will be ignored if no test group features (**@BeforeGroup**, **@AfterGroup**, specify other value for the *group* attribute of **@Test**) are used.

.. code:: python

    from ptest.decorator import TestClass, Test
    from ptest.assertion import assert_equals

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            expected = 10
            assert_equals(10, expected)

2.2.2 - BeforeMethod and AfterMethod
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Method which is decorated by **@BeforeMethod** will be executed before test started.
Method which is decorated by **@AfterMethod** will be executed after test finished.

*Note:* You can not specify multiple `enabled <#231---enabled>`_ **@BeforeMethod** or **@AfterMethod** for one test group.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import assert_equals

    @TestClass()
    class PTestClass:
        @BeforeMethod()
        def setup_data(self):
            self.expected = 10

        @Test()
        def test(self):
            assert_equals(10, self.expected)

        @AfterMethod()
        def clean_up_data(self):
            self.expected = None

2.2.3 - BeforeGroup and AfterGroup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Method which is decorated by **@BeforeGroup** will be executed before test group started.
Method which is decorated by **@AfterGroup** will be executed after test group finished.

*Note:* You can not specify multiple `enabled <#231---enabled>`_ **@BeforeGroup** or **@AfterGroup** for one test group.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeGroup, AfterGroup
    from ptest.assertion import assert_equals

    CN_GROUP = "CN"
    US_GROUP = "US"

    @TestClass()
    class PTestClass:
        # CN group
        @BeforeGroup(group=CN_GROUP)
        def before_group_cn(self):
            self.expected = "cn"

        @AfterGroup(group=CN_GROUP)
        def after_group_cn(self):
            self.expected = None

        @Test(group=CN_GROUP)
        def test_cn(self):
            assert_equals("cn", self.expected)

        # US group
        @BeforeGroup(group=US_GROUP)
        def before_group_us(self):
            self.expected = "us"

        @AfterGroup(group=US_GROUP)
        def after_group_us(self):
            self.expected = None

        @Test(group=US_GROUP)
        def test_us(self):
            assert_equals("us", self.expected)

2.2.4 - BeforeClass and AfterClass
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Method which is decorated by **@BeforeClass** will be executed before test class started.
Method which is decorated by **@AfterClass** will be executed after test class finished.

*Note:* You can not specify multiple `enabled <#2.3.1---enabled>`_ **@BeforeClass** or **@AfterClass** for one test class.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeClass, AfterClass
    from ptest.assertion import assert_equals

    @TestClass()
    class PTestClass:
        @BeforeClass()
        def before_class(self):
            self.expected = "cn&us"

        @Test(group="CN")
        def test_cn(self):
            assert_equals("cn&us", self.expected)

        @Test(group="US")
        def test_us(self):
            assert_equals("cn&us", self.expected)

        @AfterClass()
        def after_class(self):
            self.expected = None

2.2.5 - BeforeSuite, AfterSuite and inherit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Method which is decorated by **@BeforeSuite** will be executed before test suite started.
Method which is decorated by **@AfterSuite** will be executed after test suite finished.

*Note:* If you specify multiple `enabled <#231---enabled>`_ **@BeforeSuite** or **@AfterSuite** in different classes,
ONLY one **@BeforeSuite** or **@AfterSuite** will be executed.
So we recommend you to put **@BeforeSuite** or **@AfterSuite** into a base class, and create test classes to inherit it.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod, BeforeSuite, AfterSuite
    from ptest.assertion import assert_true

    class PTestBase:
        @BeforeSuite()
        def before_suite(self):
            self.max = 999

        @AfterSuite()
        def after_suite(self):
            self.max = None

        @BeforeMethod()
        def setup_data(self):
            self.now = 10

        @AfterMethod()
        def clean_up_data(self):
            self.now = None

    @TestClass()
    class PTestClass1(PTestBase):
        @Test()
        def test(self):
            assert_true(self.max > self.now)

    @TestClass()
    class PTestClass2(PTestBase):
        @Test()
        def test(self):
            self.now = 10000
            assert_true(self.max > self.now)

2.3 - Attributes
----------------
2.3.1 - enabled
~~~~~~~~~~~~~~~
*enabled* attribute is for all decorators. If the attribute is set to false, the decorator will be ignored.

The default value is ``True``. The value type should be ``bool``.

**Examples:**

If *enabled* attribute of **@TestClass** is set to ``False``, this test class will be ignored.

.. code:: python

    from ptest.decorator import TestClass, Test
    from ptest.assertion import assert_equals

    @TestClass(enabled=False)
    class PTestClass:
        @Test()
        def test(self):
            pass


If *enabled* attribute of **@BeforeMethod** is set to ``False``, the **@BeforeMethod** will be ignored.
In following case, the ``before2`` method will be run before every test.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod
    from ptest.assertion import assert_equals

    @TestClass(enabled=False)
    class PTestClass:
        @BeforeMethod(enabled=False)
        def before1(self):
            self.expected = 1

        @BeforeMethod()
        def before2(self):
            self.expected = 2

        @Test()
        def test(self):
            assert_equals(2, self.expected)

2.3.2 - description
~~~~~~~~~~~~~~~~~~~
*description* attribute is for all decorators. This attribute is used to specify the description of the decorator.

The default value is an empty string ``""``. The value type should be ``str``.

**Examples:**

You can specify the description by *description* attribute.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod
    from ptest.assertion import assert_equals

    @TestClass(description="This is a sample test class for ptest.")
    class PTestClass:
        @BeforeMethod(description="I need to setup data.")
        def setup(self):
            self.expected = 1

        @Test(description="I need to verify the data.")
        def test(self):
            assert_equals(1, self.expected)

2.3.3 - custom_args
~~~~~~~~~~~~~~~~~~~
*custom_args* attribute is for all decorators. This attribute is a placeholder for unsupported attributes.

**Examples:**

You can use *custom_args* to do some record things.

.. code:: python

    from ptest.decorator import TestClass, Test

    @TestClass(test_suite_id="ptest-suite")
    class PTestClass:
        @Test(test_case_id="PT-123")
        def test(self):
            pass

2.3.4 - timeout
~~~~~~~~~~~~~~~
*timeout* attribute is for all decorators except **@TestClass**. This attribute is used to specify the timeout (in seconds) of decorated method.

The default value is ``0`` (0 means no timeout). The value type should be ``int``.

**Examples:**

If the firefox is not setup in 30 seconds, the **@BeforeMethod** will be timed out and marked as failed.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import assert_true
    from selenium.webdriver import Firefox

    @TestClass()
    class PTestClass:
        @BeforeMethod(timeout=30)
        def setup(self):
            self.browser = Firefox()

        @Test()
        def test(self):
            self.browser.get("http://www.google.com")
            assert_true("http://www.google.com" in self.browser.current_url)

        @AfterMethod()
        def teardown(self):
            self.browser.quit()

2.3.5 - always_run
~~~~~~~~~~~~~~~~~~
*always_run* attribute is for all **@AfterXXX** decorators. If set to ``true``, the decorated method will be run even if its corresponding **@BeforeXXX** is failed. Otherwise, the decorated method will be skipped.

The default value is ``True``. The value type should be ``bool``.

**Examples:**

The **@AfterMethod** will be run even if **@BeforeMethod** if failed.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import fail, assert_equals

    @TestClass()
    class PTestClass:
        @BeforeMethod()
        def setup(self):
            self.expected = 1
            fail()

        @Test()
        def test(self):
            assert_equals(1, self.expected)

        @AfterMethod()
        def teardown(self):
            self.expected = None

2.3.6 - group
~~~~~~~~~~~~~
*group* attribute is for **@BeforeGroup**, **@BeforeMethod**, **@Test**, **@AfterMethod**, **@AfterGroup** decorators. The attribute is used to specify which group is the test fixture belong to.

The default value is ``"DEFAULT"``. The value type should be ``str``.

**Examples:**

In following case, the **@BeforeMethod** *before_cn* and *after_cn* are belong to ``CN`` group and the **@BeforeMethod** *before_us* and *after_us* are belong to ``US`` group

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeMethod, AfterMethod
    from ptest.assertion import assert_equals

    CN_GROUP = "CN"
    US_GROUP = "US"

    @TestClass()
    class PTestClass:
        # CN group
        @BeforeMethod(group=CN_GROUP)
        def before_cn(self):
            self.expected = "cn"

        @AfterMethod(group=CN_GROUP)
        def after_cn(self):
            self.expected = None

        @Test(group=CN_GROUP)
        def test_cn(self):
            assert_equals("cn", self.expected)

        # US group
        @BeforeMethod(group=US_GROUP)
        def before_us(self):
            self.expected = "us"

        @AfterMethod(group=US_GROUP)
        def after_us(self):
            self.expected = None

        @Test(group=US_GROUP)
        def test_us(self):
            assert_equals("us", self.expected)

2.3.7 - run_mode
~~~~~~~~~~~~~~~~
*run_mode* attribute is only for **@TestClass** decorator. This attribute is used to specify the run mode of all the test cases in the test class. If set to ``"parallel"``, all the test cases will be run by multiple threads. If set to ``"singleline"``, all the test cases will be only run by one thread.

The default value is ``"parallel"``. The value type should be ``str`` and it must be ``"singleline"`` or ``"parallel"``.

**Examples:**

In following case, all the test cases use the same browser, so they should only be run by one thread.

.. code:: python

    from ptest.decorator import TestClass, Test, BeforeClass, AfterClass
    from ptest.assertion import assert_true
    from selenium.webdriver import Firefox

    @TestClass(run_mode="singleline")
    class PTestClass:
        @BeforeClass()
        def setup(self):
            self.browser = Firefox()

        @Test()
        def test1(self):
            self.browser.get("http://www.google.com")
            assert_true("http://www.google.com" in self.browser.current_url)

        @Test()
        def test2(self):
            self.browser.get("http://github.com")
            assert_true("https://github.com" in self.browser.current_url)

        @Test()
        def test3(self):
            self.browser.get("https://www.python.org")
            assert_true("https://www.python.org" in self.browser.current_url)

        @AfterClass()
        def teardown(self):
            self.browser.quit()

2.3.8 - run_group
~~~~~~~~~~~~~~~~~
*run_group* attribute is only for **@TestClass** decorator. This attribute is used to specify the run group of test class. If run group is specified, all the test classes in the same run group will be run one by one. If not, this test class will be belong to it own run group.

The default value is ``None``. The value type should be ``str``.

**Examples:**

In following case, the ``PTestClass1`` and ``PTestClass2`` will be run one by one even if the ``-n(--testexecutornumber)`` is set of greater than 1.

.. code:: python

    from ptest.decorator import TestClass, Test

    RUN_GROUP = "my run group"

    @TestClass(run_group=RUN_GROUP)
    class PTestClass1:
        @Test()
        def test1(self):
            pass

        @Test()
        def test2(self):
            pass


    @TestClass(run_group=RUN_GROUP)
    class PTestClass2:
        @Test()
        def test3(self):
            pass

        @Test()
        def test4(self):
            pass

2.3.9 - tags
~~~~~~~~~~~~
*tags* attribute is only for **@Test** decorator. This attribute is used to specify the tags of the test case.

The default value is an empty list ``[]``. The value type should be ``str`` (separated by comma) or ``list`` or ``tuple``.

**Examples:**

You can specify the tags by *tags* attribute.

.. code:: python

    from ptest.decorator import TestClass, Test
    
    @TestClass()
    class PTestClass:
        @Test(tags="nightly,smoke")
        def test1(self):
            pass
        
        @Test(tags=["smoke"])
        def test2(self):
            pass

2.3.10 - expected_exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*expected_exceptions* attribute is only for **@Test** decorator. This attribute is used to specify the expected exceptions of the test case. If no exception or a different one is thrown, this test case will be marked as failed.

The default value is ``None``. The value type should be ``Exception Class`` or ``list`` or ``tuple`` or ``dict``.

    ``Exception Class``:
        expected_exceptions=AttributeError

    Exception Class ``list`` or ``tuple``:
        | expected_exceptions=[AttributeError, IndexError]
        | expected_exceptions=(AttributeError, IndexError)

    Exception Class and regular expression of expected message ``dict``:
        expected_exceptions={AttributeError: '.*object has no attribute.*'}

*Note:* If you want to match the entire exception message, just include anchors in the regex pattern.

**Examples:**

You can specify the expected exceptions by *expected_exceptions* attribute.

.. code:: python

    from ptest.decorator import TestClass, Test

    @TestClass()
    class PTestClass:
        @Test(expected_exceptions=AssertionError)
        def test1(self):
            assert False # pass, the AssertionError is thrown

        @Test(expected_exceptions=ImportError)
        def test2(self):
            assert False # failed, thrown exception doesn't match ImportError

        @Test(expected_exceptions=AssertionError)
        def test3(self):
            pass # failed, no exception is thrown

        @Test(expected_exceptions=Exception)
        def test4(self):
            assert False # pass, the AssertionError is subclass of Exception

        @Test(expected_exceptions=(AttributeError, AssertionError))
        def test5(self):
            sum = self.x + self.y # pass, the AttributeError is thrown

        @Test(expected_exceptions={AttributeError: '.*object has no attribute.*'})
        def test6(self):
            diff = self.x - self.y # failed, the AttributeError is thrown but the message doesnt' match

3 - Running ptest
=================
ptest can be invoked in different ways:

- `Command line <#31---command-line>`_

- `Code <#32---code>`_

- `PyCharm <#33---pycharm>`_

3.1 - Command line
------------------
ptest command line parameters:

+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| Option                   | Argument                         | Documentation                                                                                |
+==========================+==================================+==============================================================================================+
| -w(--workspace)          | A directory                      || Specify the workspace dir (relative to working directory).                                  |
|                          |                                  || Default is current working directory.                                                       |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -P(--pythonpaths)        | A comma-separated list of paths  || Specify the additional locations (relative to workspace)                                    |
|                          |                                  || where to search test libraries from when they are imported.                                 |
|                          |                                  || Multiple paths can be given by separating them with a comma.                                |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -p(--propertyfile)       | A property file                  || Specify the property file (relative to workspace).                                          |
|                          |                                  || The properties in property file will be overwritten by user defined properties in cmd line. |
|                          |                                  || Get property via get_property() in module ptest.config.                                     |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -R(--runfailed)          | A xml file                       | Specify the xunit result xml path (relative to workspace)                                    |
|                          |                                  | and run the failed/skipped test cases in it.                                                 |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -t(--targets)            | A comma-separated list of targets|| Specify the path of test targets, separated by comma.                                       |
|                          |                                  || Test target can be package/module/class/method.                                             |
|                          |                                  || The target path format is: package[.module[.class[.method]]]                                |
|                          |                                  || NOTE: ptest ONLY searches modules under --workspace, --pythonpaths and sys.path             |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -i(--includetags)        | A comma-separated list of tags   | Select test cases to run by tags, separated by comma.                                        |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -e(--excludetags)        | A comma-separated list of tags   || Select test cases not to run by tags, separated by comma.                                   |
|                          |                                  || These test cases are not run even if included with --includetags.                           |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -g(--includegroups)      | A group name                     | Select test cases to run by groups, separated by comma.                                      |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -n(--testexecutornumber) | A positive integer               | Specify the number of test executors. Default value is 1.                                    |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -o(--outputdir)          | A directory                      | Specify the output dir (relative to workspace).                                              |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -r(--reportdir)          | A directory                      | Specify the html report dir (relative to output dir).                                        |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -x(--xunitxml)           | A xml file                       | Specify the xunit result xml path (relative to output dir).                                  |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -l(--listeners)          | A comma-separated list of classes|| Specify the path of test listener classes, separated by comma.                              |
|                          |                                  || The listener class should implement class TestListener in ptest.plistener                   |
|                          |                                  || The listener path format is: package.module.class                                           |
|                          |                                  || NOTE: 1. ptest ONLY searches modules under --workspace, --pythonpaths and sys.path          |
|                          |                                  || 2. The listener class must be thread safe if you set -n(--testexecutornumber) greater than 1|
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -v(--verbose)            |                                  | Set ptest console to verbose mode.                                                           |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| --temp                   | A directory                      | Specify the temp dir (relative to workspace).                                                |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| --disablescreenshot      |                                  | Disable taking screenshot for failed test fixtures.                                          |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -m(--mergexunitxmls)     | A comma-separated list of xmls   || Merge the xunit result xmls (relative to workspace).                                        |
|                          |                                  || Multiple files can be given by separating them with a comma.                                |
|                          |                                  || Use --to to specify the path of merged xunit result xml.                                    |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| --to                     | A path                           | Specify the 'to' destination (relative to workspace).                                        |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+
| -D<key>=<value>          |                                  || Define properties via -D<key>=<value>. e.g., -Dmykey=myvalue                                |
|                          |                                  || Get defined property via get_property() in module ptest.config.                             |
+--------------------------+----------------------------------+----------------------------------------------------------------------------------------------+

This documentation can be obtained by executing ``ptest --help`` in cmd.

3.2 - Code
----------
You can invoke ptest by code:

.. code:: python

    from ptest.main import main

    main("-t xxx")
    main(["-R", "last\xunit.xml"])
    main(("-m", "xunit1.xml,xunit2.xml", "--to", "xunit.xml"))

3.3 - PyCharm
-------------
A Pycharm plugin for ptest is released.
It is easily to run/debug ptest within the IDE using the standard run configuration.
Find the latest version on github: https://github.com/KarlGong/ptest-pycharm-plugin or JetBrains: https://plugins.jetbrains.com/plugin/7860

4 - Test Listeners
==================
ptest provides a listener that allows you to be notified whenever ptest starts/finishes suite/class/group/test.
Your need to implement class TestListener in ptest.plistener

Create a listener.py under workspace:

.. code:: python

    from ptest.plistener import TestListener

    class MyTestListener(TestListener):
        def on_test_case_finish(self, test_case):
            print(test_case.status)

*Note:* The listener class must be thread safe if you set ``-n(--testexecutornumber)`` greater than 1.

Then use ``-l(--listeners)`` to specify the path of test listener classes

::

    $ ptest -t abc -l listener.MyTestListener

5 - Test results
================
5.1 - Success, failure, skipped and assert
------------------------------------------
A test is considered successful if it completed without throwing any exception or if it threw an exception that was expected (see the documentation for the `expected_exceptions <#2310---expected_exceptions>`_ attribute found on the **@Test** decorator).
And it will be marked as skipped if its **@BeforeXXX** failed.

Your test methods will typically be made of calls that can throw an exception, or of various assertions (using the Python ``assert`` keyword).  An ``assert`` failing will trigger an ``AssertionError``, which in turn will mark the method as failed.

Here is an example test method:

.. code:: python

    from ptest.decorator import TestClass, Test

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            assert 1 == 2

ptest also provides an assertion module which lets you perform assertions on complex objects:

simple assertion:

.. code:: python

    from ptest.decorator import TestClass, Test
    from ptest.assertion import assert_list_elements_equal

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            assert_list_elements_equal([1,2], [2,1,1])

``assert_that`` assertion:

.. code:: python

    from ptest.decorator import TestClass, Test
    from ptest.assertion import assert_that

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            assert_that([1,2,3]).contains(1).does_not_contain(4)

5.2 - Logging and results
=========================
ptest generates two reports - standard xunit xml result and html report.

5.2.1 - plogger
---------------
With *plogger*, you can log any message which can help to find the cause of failed test.
There are two loggers in plogger:

- *pconsole* - the messages will be output to console

- *preporter* - the messages will be output to html report

Here is an example to log the value which is generated by Random:

.. code:: python

    from random import Random
    from ptest.decorator import TestClass, Test
    from ptest.plogger import preporter, pconsole

    @TestClass()
    class PTestClass:
        @Test()
        def random(self):
            x = Random().random()
            pconsole.write_line("The random value is %s" % x)
            preporter.info("The random value %s" % x)
            assert x > 0.5

5.2.2 - Screenshot
------------------
By default, ptest will take screenshot for any failed test fixtures.
If your test cases are based on selenium web driver, ptest will take screenshot for the web driver.
Otherwise, ptest will take screenshot for the desktop.

You can disable ptest to take screenshot by adding command line option ``--disablescreenshot``.
