$(window).load(function () {
    $(function () {
        $('.tree li > .item').on('click', function (e) {
            renderDetailPanel($(this).parent().data("data"));
            e.stopPropagation();
        });

        $('.tree li.parent>.item>.sign').on('click', function (e) {
            var children = $(this).parent().parent().find(' > ul > li');
            if (children.is(":visible")) {
                children.hide('fast');
                $(this).text("+");
            } else {
                children.show('fast');
                $(this).text("-");
            }
            e.stopPropagation();
        });

        // init filter for tree
        $('.navigation .all .badge').text(testSuite.statusCount['total']);
        $('.navigation .pass .badge').text(testSuite.statusCount['passed']);
        $('.navigation .fail .badge').text(testSuite.statusCount['failed']);
        $('.navigation .skip .badge').text(testSuite.statusCount['skipped']);

        // add sign for parent node
        var parentNodes = $('.tree li.parent');
        for (var i = 0; i < parentNodes.length; i ++) {
            var parentNode = $(parentNodes[i]);
            var children = parentNode.find(' > ul > li');
            if (children.is(':visible')) {
                parentNode.find(' > .item > .sign').text('-');
            } else {
                parentNode.find(' > .item > .sign').text('+');
            }
        }

        // set light box option
        lightbox.option({
            'resizeDuration': 0
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

renderTree = function (testSuite) {
    appendToNode = function (parentNode, data, visible) {
        var node = null;
        if (data.type == "testfixture" || data.type == "testcase") {
            // an empty test fixture
            if (data.type == "testfixture" && data.isEmpty) {
                return node;
            }
            var nodeContent = '<li class="node leaf"><div class="item" title="{fullName}"><div class="sign {status}"></div><div class="name">{name}</div></div></li>';
            if (data.hasOwnProperty("fixtureType")) {
                // test fixture
                node = $(nodeContent.format({
                    "name": '@' + data.fixtureType,
                    "fullName": data.fullName,
                    "status": data.status
                }));
            } else {
                // test case
                node = $(nodeContent.format({
                    "name": data.name,
                    "fullName": data.fullName,
                    "status": data.status
                }));
            }
        }
        else {
            // test container
            var nodeContent = '<li class="node parent"><div class="item" title="{fullName}"><div class="sign" title="Click to expand/collapse."></div><div class="name">{name}</div><div class="badge">{total}</div><div class="rate-container"><div class="passed rate" style="width: {passRate}%"></div><div class="failed rate" style="width: {failRate}%"></div><div class="skipped rate" style="width: {skipRate}%"></div></div></div><ul></ul></li>';
            node = $(nodeContent.format({
                "name": data.name,
                "fullName": data.fullName,
                "total": data.statusCount.total,
                "passRate": data.passRate,
                "failRate": data.failRate,
                "skipRate": data.skipRate
            }));
        }
        if (!visible) {
            node.css('display', 'none');
        }
        node.data("data", data);
        parentNode.find(' > ul').append(node);
        return node;
    };

    // render tree
    var testSuiteNode = appendToNode($('.navigation .tree'), testSuite, true);

    for (var i = 0; i < testSuite.testClasses.length; i++) {
        var testClass = testSuite.testClasses[i];
        var testClassNode = appendToNode(testSuiteNode, testClass, true);

        for (var j = 0; j < testClass.testGroups.length; j++) {
            var testGroup = testClass.testGroups[j];
            var testGroupNode = appendToNode(testClassNode, testGroup, false);

            for (var k = 0; k < testGroup.testCases.length; k++) {
                var testCase = testGroup.testCases[k];
                appendToNode(testGroupNode, testCase, false);
            }
        }
    }
};

renderTestFixturePanel = function (detailPanel, data) {
    var testFixturePanel = $('<div class="test-fixture panel"><div class="panel-heading"></div><div class="panel-body"><table></table></div></div>');
    var panelHeader = testFixturePanel.find('.panel-heading');
    panelHeader.addClass(data.status);
    panelHeader.text('@' + data.fixtureType);

    var fieldTable = testFixturePanel.find('table');
    var fullName = $('<tr><td>Full Name</td><td>{0}</td></tr>'.format(data.fullName));
    fieldTable.append(fullName);
    var name = $('<tr><td>Method Name</td><td>{0}</td></tr>'.format(data.name));
    fieldTable.append(name);
    var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
    fieldTable.append(startTime);
    var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
    fieldTable.append(endTime);
    var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
    fieldTable.append(duration);
    var description = $('<tr><td>Description</td><td>{0}</td></tr>'.format(data.description));
    fieldTable.append(description);
    var logs = $('<tr><td>Logs</td><td class="logs"></td></tr>');
    fieldTable.append(logs);
    var logGroup = logs.find('.logs');
    for (var i = 0; i < data.logs.length; i++) {
        var level = data.logs[i].level;
        var message = data.logs[i].message;
        var log = $('<span class="log-level">[{0}] </span><span class="{0}">{1}</span><br/>'.format(level, message));
        logGroup.append(log);
    }
    if (data.screenshot != null) {
        var screenshot = $('<tr><td>Screenshot</td><td><a class="screenshot-link" href="{0}" data-lightbox="{0}"><img class="screenshot" src="{0}" /></a></td></tr>'.format(data.screenshot));
        fieldTable.append(screenshot);
    }

    detailPanel.append(testFixturePanel);
};

renderDetailPanel = function (data) {
    var detailPanel = $('.detail');
    var detailPanelHeader = detailPanel.find('.panel-heading .text');
    var detailPanelBody = detailPanel.find('.panel-body');
    detailPanelHeader.text(data.fullName);
    detailPanelBody.empty();
    switch (data.type) {
        case "testcase":
            var fieldTable = $('<table class="testcase"></table>');

            var tags = $('<tr><td>Tags</td><td></td></tr>');
            var tagSlot = tags.find('td:nth-child(2)');
            for (var i=0; i < data.tags.length; i++) {
                tagSlot.append($('<span class="tag">{0}</span>'.format(data.tags[i])));
            }
            fieldTable.append(tags);

            var group = $('<tr><td>Group</td><td></td></tr>');
            group.find('td:nth-child(2)').append($('<span class="group">{0}</span>'.format(data.group)));
            fieldTable.append(group);

            var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
            fieldTable.append(startTime);
            var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
            fieldTable.append(endTime);
            var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
            fieldTable.append(duration);
            var description = $('<tr><td>Description</td><td>{0}</td></tr>'.format(data.description));
            fieldTable.append(description);

            detailPanelBody.append(fieldTable);
            if (!data.beforeMethod.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.beforeMethod);
            }
            renderTestFixturePanel(detailPanelBody, data.test);
            if (!data.afterMethod.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.afterMethod);
            }
            break;
        case "testsuite":
            var fieldTable = $('<table class="overview"></table>');

            var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
            fieldTable.append(startTime);
            var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
            fieldTable.append(endTime);
            var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
            fieldTable.append(duration);

            detailPanelBody.append(fieldTable);
            if (!data.beforeSuite.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.beforeSuite);
            }
            if (!data.afterSuite.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.afterSuite);
            }
            break;
        case "testclass":
            var fieldTable = $('<table class="overview"></table>');

            var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
            fieldTable.append(startTime);
            var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
            fieldTable.append(endTime);
            var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
            fieldTable.append(duration);
            var description = $('<tr><td>Description</td><td>{0}</td></tr>'.format(data.description));
            fieldTable.append(description);

            detailPanelBody.append(fieldTable);
            if (!data.beforeClass.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.beforeClass);
            }
            if (!data.afterClass.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.afterClass);
            }
            break;
        case "testgroup":
            var fieldTable = $('<table class="overview"></table>');

            var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
            fieldTable.append(startTime);
            var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
            fieldTable.append(endTime);
            var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
            fieldTable.append(duration);

            detailPanelBody.append(fieldTable);
            if (!data.beforeGroup.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.beforeGroup);
            }
            if (!data.afterGroup.isEmpty) {
                renderTestFixturePanel(detailPanelBody, data.afterGroup);
            }
            break;
    }
};