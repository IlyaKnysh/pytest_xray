from os import environ

import pytest

from .constants import XRAY_API_BASE_URL, XRAY_PLUGIN
from .models import XrayTestReport
from .utils import PublishXrayResults, associate_marker_metadata_for, get_test_key_for
from . import execution

JIRA_XRAY_FLAG = "--jira-xray"


def pytest_configure(config):
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    plugin = PublishXrayResults(
        XRAY_API_BASE_URL,
        client_id=environ["XRAY_API_CLIENT_ID"],
        client_secret=environ["XRAY_API_CLIENT_SECRET"],
    )
    config.pluginmanager.register(plugin, XRAY_PLUGIN)


def pytest_addoption(parser):
    group = parser.getgroup("JIRA Xray integration")

    group.addoption(
        JIRA_XRAY_FLAG, action="store_true", help="jira_xray: Publish test results to Xray API"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    for item in items:
        associate_marker_metadata_for(item)


def pytest_terminal_summary(terminalreporter):
    if not terminalreporter.config.getoption(JIRA_XRAY_FLAG):
        return

    test_reports = []
    if "passed" in terminalreporter.stats:
        for each in terminalreporter.stats["passed"]:
            keys = get_test_key_for(each)
            test_key = keys[0]
            test_exec_key = keys[1] if keys[1] else execution.execution_id
            test_key = [test_key] if isinstance(test_key, str) else test_key
            try:
                for test_key in test_key:
                    report = XrayTestReport.as_passed(test_key, test_exec_key, each.duration)
                    test_reports.append(report)
            except TypeError:
                raise Exception(f'Xray mark is missed for {terminalreporter.config.args}')

    if "failed" in terminalreporter.stats:
        for each in terminalreporter.stats["failed"]:
            keys = get_test_key_for(each)
            test_key = keys[0]
            test_exec_key = keys[1] if keys[1] else execution.execution_id
            if test_key:
                test_key = [test_key] if isinstance(test_key, str) else test_key
                for test_key in test_key:
                    report = XrayTestReport.as_failed(
                        test_key, test_exec_key, each.duration, each.longreprtext
                    )
                    test_reports.append(report)

    publish_results = terminalreporter.config.pluginmanager.get_plugin(XRAY_PLUGIN)

    if not callable(publish_results):
        raise TypeError("Xray plugin is not a callable. Please review 'pytest_configure' hook!")

    publish_results(*test_reports)
