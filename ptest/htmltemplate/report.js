$(window).load(function () {
    $(function () {
        // set light box option
        lightbox.option({
            'resizeDuration': 0
        });

        // add listener for expand all
        $('.navigation .toolbar .expand').on('click', function (e) {
            $('.tree li.parent.collapsed>.item>.sign').click();
            e.stopPropagation();
        });

        // add listener for collapse all
        $('.navigation .toolbar .collapse').on('click', function (e) {
            $('.tree li.parent.expanded>.item>.sign').click();
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

renderTree = function (testSuite, statusFilter) {
    appendToNode = function (parentNode, data, visible) {
        var node = null;
        if (data.type == "testcase") {
            switch (statusFilter){
                case "passed":
                    if (data.status != "passed") {
                        return null;
                    }
                    break;
                case "failed":
                    if (data.status != "failed") {
                        return null;
                    }
                    break;
                case "skipped":
                    if (data.status != "skipped") {
                        return null;
                    }
                    break;
            }
            var nodeContent = '<li class="node leaf"><div class="item" title="{fullName}"><div class="sign {status}"></div><div class="name">{name}</div></div></li>';
            // test case
            node = $(nodeContent.format({
                "name": data.name,
                "fullName": data.fullName,
                "status": data.status
            }));
        }
        else {
            // test container
            var nodeContent = '<li class="node parent"><div class="item" title="{fullName}"><div class="sign" title="Click to expand/collapse."></div><div class="name">{name}</div><div class="{statusFilter} badge">{total}</div><div class="rate-container"><div class="passed rate" style="width: {passRate}%"></div><div class="failed rate" style="width: {failRate}%"></div><div class="skipped rate" style="width: {skipRate}%"></div></div></div><ul></ul></li>';
            var nodeContentFormatter = {
                "name": data.name,
                "fullName": data.fullName,
                "statusFilter": statusFilter,
                "total": data.statusCount.total,
                "passRate": data.passRate,
                "failRate": data.failRate,
                "skipRate": data.skipRate
            }
            switch (statusFilter) {
                case "passed":
                    if (data.passRate == 0) {
                        return null;
                    }
                    nodeContentFormatter["total"] = data.statusCount.passed;
                    nodeContentFormatter["passRate"] = 100;
                    nodeContentFormatter["failRate"] = 0;
                    nodeContentFormatter["skipRate"] = 0;
                    break;
                case "failed":
                    if (data.failRate == 0 ) {
                        return null;
                    }
                    nodeContentFormatter["total"] = data.statusCount.failed;
                    nodeContentFormatter["passRate"] = 0;
                    nodeContentFormatter["failRate"] = 100;
                    nodeContentFormatter["skipRate"] = 0;
                    break;
                case "skipped":
                    if (data.skipRate == 0) {
                        return null;
                    }
                    nodeContentFormatter["total"] = data.statusCount.passed;
                    nodeContentFormatter["passRate"] = 0;
                    nodeContentFormatter["failRate"] = 0;
                    nodeContentFormatter["skipRate"] = 100;
                    break;
            }
            node = $(nodeContent.format(nodeContentFormatter));
        }
        if (!visible) {
            node.css('display', 'none');
        }
        node.data("data", data);
        parentNode.find(' > ul').append(node);
        return node;
    };

    // clear tree
    $('.navigation .tree>ul').empty()

    // render tree
    var testSuiteNode = appendToNode($('.navigation .tree'), testSuite, true);
    if (testSuiteNode == null) {
        return;
    }

    for (var i = 0; i < testSuite.testClasses.length; i++) {
        var testClass = testSuite.testClasses[i];
        var testClassNode = appendToNode(testSuiteNode, testClass, true);
        if (testClassNode == null) {
            continue;
        }

        for (var j = 0; j < testClass.testGroups.length; j++) {
            var testGroup = testClass.testGroups[j];
            var testGroupNode = appendToNode(testClassNode, testGroup, false);
            if (testGroupNode == null) {
                continue;
            }

            for (var k = 0; k < testGroup.testCases.length; k++) {
                var testCase = testGroup.testCases[k];
                appendToNode(testGroupNode, testCase, false);
            }
        }
    }

    // add sign for parent node
    var parentNodes = $('.tree li.parent');
    for (var i = 0; i < parentNodes.length; i ++) {
        var parentNode = $(parentNodes[i]);
        var children = parentNode.find(' > ul > li');
        if (children.is(':visible')) {
            parentNode.find(' > .item > .sign').text('-');
            parentNode.addClass('expanded');
        } else {
            parentNode.find(' > .item > .sign').text('+');
            parentNode.addClass('collapsed');
        }
    }

     // add listener for expand/collapse parent node
    $('.tree li.parent>.item>.sign').on('click', function (e) {
        var node = $(this).parent().parent();
        var children = node.find(' > ul > li');
        if (children.is(":visible")) {
            children.hide('fast');
            $(this).text("+");
            node.removeClass('expanded').addClass('collapsed');
        } else {
            children.show('fast');
            $(this).text("-");
            node.removeClass('collapsed').addClass('expanded');
        }
        e.stopPropagation();
    });

    // add listener for selecting node
    $('.tree li > .item').on('click', function (e) {
            renderDetailPanel($(this).parent().data("data"));
            $('.tree li .selected').removeClass('selected');
            $(this).addClass('selected');
            e.stopPropagation();
    });
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
    var detailPanelHeader = detailPanel.find('.panel-heading');
    var detailPanelBody = detailPanel.find('.panel-body');
    detailPanelHeader.empty();
    detailPanelBody.empty();
    var title = $('<span class="text">{0}</span>'.format(data.fullName));
    detailPanelHeader.append(title);
    switch (data.type) {
        case "testcase":
            var fieldTable = $('<table class="overview"></table>');

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
            var numberContent = '<div class="all badge">{0}</div><div class="passed badge">{1}</div><div class="failed badge">{2}</div><div class="skipped badge">{3}</div>';
            var number = $(numberContent.format(data.statusCount.total, data.statusCount.passed, data.statusCount.failed, data.statusCount.skipped));
            detailPanelHeader.append(number);

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
            var numberContent = '<div class="all badge">{0}</div><div class="passed badge">{1}</div><div class="failed badge">{2}</div><div class="skipped badge">{3}</div>';
            var number = $(numberContent.format(data.statusCount.total, data.statusCount.passed, data.statusCount.failed, data.statusCount.skipped));
            detailPanelHeader.append(number);

            var fieldTable = $('<table class="overview"></table>');

            var startTime = $('<tr><td>Start Time</td><td>{0}</td></tr>'.format(data.startTime));
            fieldTable.append(startTime);
            var endTime = $('<tr><td>End Time</td><td>{0}</td></tr>'.format(data.endTime));
            fieldTable.append(endTime);
            var duration = $('<tr><td>Duration</td><td>{0}s</td></tr>'.format(data.elapsedTime));
            fieldTable.append(duration);
            var runMode = $('<tr><td>Run Mode</td><td>{0}</td></tr>'.format(data.runMode));
            fieldTable.append(runMode);
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
            var numberContent = '<div class="all badge">{0}</div><div class="passed badge">{1}</div><div class="failed badge">{2}</div><div class="skipped badge">{3}</div>';
            var number = $(numberContent.format(data.statusCount.total, data.statusCount.passed, data.statusCount.failed, data.statusCount.skipped));
            detailPanelHeader.append(number);

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