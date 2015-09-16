$(window).load(function () {
    $(function () {
        $('.tree li:has(ul)').addClass('parent_li');
        $('.tree li.parent_li > span').on('click', function (e) {
            var children = $(this).parent('li.parent_li').find(' > ul > li');
            if (children.is(":visible")) {
                children.hide('fast');
                $(this).find(' > i').addClass('icon-plus-sign').removeClass('icon-minus-sign');
            } else {
                children.show('fast');
                $(this).find(' > i').addClass('icon-minus-sign').removeClass('icon-plus-sign');
            }
            e.stopPropagation();
        });
    });
});

String.prototype.format = function (args) {
    var result = this;
    if (arguments.length > 0) {
        if (arguments.length == 1 && typeof (args) == "object") {
            for (var key in args) {
                if (args[key] != undefined) {
                    var reg = new RegExp("({" + key + "})", "g");
                    result = result.replace(reg, args[key]);
                }
            }
        }
        else {
            for (var i = 0; i < arguments.length; i++) {
                if (arguments[i] != undefined) {
                    var reg = new RegExp("({)" + i + "(})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
};

initTree = function (testSuite) {
    var testSuiteNode = $('<li><span>{0}</span><ul></ul></li>'.format(testSuite.name));
    $('.tree').find(' > ul').append(testSuiteNode);

    var beforeSuite = testSuite.beforeSuite;
    if (!beforeSuite.isEmpty) {
        var beforeSuiteNode = $('<li><span>{0}</span></li>'.format(beforeSuite.fixtureType));
        testSuiteNode.find(' > ul').append(beforeSuiteNode);
    }

    for (var i = 0; i < testSuite.testClasses.length; i++) {
        var testClass = testSuite.testClasses[i];
        var testClassNode = $('<li><span>{0}</span><ul></ul></li>'.format(testClass.name));
        testSuiteNode.find(' > ul').append(testClassNode);

        var beforeClass = testClass.beforeClass;
        if (!beforeClass.isEmpty) {
            var beforeClassNode = $('<li><span>{0}</span></li>'.format(beforeClass.fixtureType));
            testClassNode.find(' > ul').append(beforeClassNode);
        }

        for (var j = 0; j < testClass.testGroups.length; j++) {
            var testGroup = testClass.testGroups[j];
            var testGroupNode = $('<li><span>{0}</span><ul></ul></li>'.format(testGroup.name));
            testClassNode.find(' > ul').append(testGroupNode);

            var beforeGroup = testGroup.beforeGroup;
            if (!beforeGroup.isEmpty) {
                var beforeGroupNode = $('<li><span>{0}</span></li>'.format(beforeGroup.fixtureType));
                testGroupNode.find(' > ul').append(beforeGroupNode);
            }

            for (var k = 0; k < testGroup.testCases.length; k++) {
                var testCase = testGroup.testCases[k];
                var testCaseNode = $('<li><span>{0}</span></li>'.format(testCase.name));
                testGroupNode.find(' > ul').append(testCaseNode);
            }

            var afterGroup = testGroup.afterGroup;
            if (!afterGroup.isEmpty) {
                var afterGroupNode = $('<li><span>{0}</span></li>'.format(afterGroup.fixtureType));
                testGroupNode.find(' > ul').append(afterGroupNode);
            }
        }

        var afterClass = testClass.afterClass;
        if (!afterClass.isEmpty) {
            var afterClassNode = $('<li><span>{0}</span></li>'.format(afterClass.fixtureType));
            testClassNode.find(' > ul').append(afterClassNode);
        }
    }

    var afterSuite = testSuite.afterSuite;
    if (!afterSuite.isEmpty) {
        var afterSuiteNode = $('<li><span>{0}</span></li>'.format(afterSuite.fixtureType));
        testSuiteNode.find(' > ul').append(afterSuiteNode);
    }
};