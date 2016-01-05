1 - Introduction
================
ptest is a light test runner for Python. With ptest, you can tag test classes & test cases by decorators, execute test cases by command line, and get clear reports.

Writing a test is typically a two-step process:

1. Write the business logic of your test and insert `ptest decorators <#2---decorators>`_ in your code.

2. `Run ptest <#3---running-ptest>`_.

The concepts used in this documentation are as follows:

- A suite is represented by one run of ptest.

- A ptest class is a python class which is decorated by **@TestClass**.

- A ptest group is a virtual container of tests under ptest class.

- A test method is a python method which is decorated by **@Test**.

A ptest test can be configured by **@BeforeXXX** and **@AfterXXX** decorators which allows to perform some Python logic before and after a certain point, these points being either of the items listed above.

The rest of this manual will explain the following:

- A list of all the decorators with a brief explanation.
- This will give you an idea of the various functionalities offered by ptest but you will probably want to consult the section dedicated to each of these decorators to learn the details.

2 - Decorators
==============
Here is a quick overview of the decorators available in ptest along with their attributes.

**@TestClass** - the decorated class will be marked as ptest class

- *enabled* - whether this test class is enabled

- *run_mode* - the run mode of all the test cases in this test class. If set to "parallel", all the test cases will be run by multiple threads. If set to "singleline", all the test cases will be only run by one thread.

- *description* - the description of this test class

- *custom_args* - the custom arguments of this test class

**@Test** - the decorated method will be marked as ptest test

- *enabled* - whether this test is enabled

- *tags* - the tags of this test (it can be string (separated by comma) or list or tuple)

- *group* - the group that this test is belong to

- *description* - the description of this test

- *timeout* - the timeout of this test (in seconds)

- *custom_args* - the custom arguments of this test

**@BeforeSuite** - the decorated method will be executed before test suite started

- *enabled* - whether this test fixture is enabled

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@AfterSuite** - the decorated method will be executed after test suite finished

- *enabled* - whether this test fixture is enabled

- *always_run* - if set to true, this test fixture will be run even if the **@BeforeSuite** is failed. Otherwise, this test fixture will be skipped.

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@BeforeClass** - the decorated method will be executed before test class started

- *enabled* - whether this test fixture is enabled

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@AfterClass** - the decorated method will be executed after test class finished

- *enabled* - whether this test fixture is enabled

- *always_run* - if set to true, this test fixture will be run even if the **@BeforeClass** is failed. Otherwise, this test fixture will be skipped.

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@BeforeGroup** - the decorated method will be executed before test group started

- *enabled* - whether this test fixture is enabled

- *group* - the group that this test fixture is belong to

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@AfterGroup** - the decorated method will be executed after test group finished

- *enabled* - whether this test fixture is enabled

- *always_run* - if set to true, this test fixture will be run even if the **@BeforeGroup** is failed. Otherwise, this test fixture will be skipped.

- *group* - the group that this test fixture is belong to

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@BeforeMethod** - the decorated method will be executed before test started

- *enabled* - whether this test fixture is enabled

- *group* - the group that this test fixture is belong to

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

**@AfterMethod** - the decorated method will be executed after test finished

- *enabled* - whether this test fixture is enabled

- *always_run* - if set to true, this test fixture will be run even if the **@BeforeMethod** is failed. Otherwise, this test fixture will be skipped.

- *group* - the group that this testfixture is belong to

- *description* - the description of this test fixture

- *timeout* - the timeout of this test fixture (in seconds)

- *custom_args* - the custom arguments of this test fixture

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
You can invoke the ptest by code:

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
ptest provides a listener that allows you to be notified whenever ptest starts/finishs suite/class/group/test.
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
5.1 - Success, failure and assert
---------------------------------
A test is considered successful if it completed without throwing any exception.

Your test methods will typically be made of calls that can throw an exception, or of various assertions (using the Python "assert" keyword).  An "assert" failing will trigger an AssertionError, which in turn will mark the method as failed.

Here is an example test method:

.. code:: python

    from ptest.decorator import TestClass, Test

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            assert 1 == 2

ptest also provides an assertion module which lets you perform assertions on complex objects:

.. code:: python

    from ptest.decorator import TestClass, Test
    from ptest.assertion import assert_list_elements_equal

    @TestClass()
    class PTestClass:
        @Test()
        def test(self):
            assert_list_elements_equal([1,2], [2,1,1])

5.2 - Logging and results
=========================
ptest generates two reports - standard xunit xml result and html report.

5.2.1 - plogger
---------------
With *plogger*, you can log any message which can help to find the cause of failed test.
There are two loggers in plogger:

- *pconsole* - the messages will be output to console

- *preproter* - the messages will be output to html report

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

You can disable ptest to take screenshot by adding command line option ``--disablescreenshot``
