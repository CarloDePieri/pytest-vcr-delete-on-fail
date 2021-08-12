import os
from typing import Optional

import pytest
import re

from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo


marker_name = "vcr_delete_on_fail"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo):
    """Hook used to make available to fixtures tests results."""
    outcome = yield
    rep = outcome.get_result()

    # init the empty reports item if necessary
    if not hasattr(item, "reports"):
        setattr(item, "reports", {
            "setup": None,
            "call": None,
            "teardown": None
        })

    # set a report attribute for each phase of a call: setup, call, teardown
    # this gets rewritten, but since a failure stop a phase, it's the last report that counts
    item.reports[rep.when] = rep

    # If class scoped test setup/teardown fail, mark the class to signal this
    if item.cls is not None:
        if has_class_scoped_phase_failed(rep):
            setattr(item.cls, f"cls_{rep.when}_failed", True)


def has_class_scoped_phase_failed(report: TestReport) -> bool:
    """This will return True if the report describe a failed phase coming from a class scoped fixture."""
    if len(report.longreprtext) > 0:
        pattern = re.compile(r"(@pytest\.fixture\()(.*)(scope\ *\=\ *)(\"|\')(class)(\"|\')(.*)(\))")
        found = pattern.search(report.longreprtext)
        if found:
            return True
    return False


def get_cassette_folder_path(test_file_path: str) -> str:
    """Return the cassette path given the test file path."""
    return os.path.join(
        os.path.dirname(test_file_path),
        "cassettes",
        os.path.basename(test_file_path).replace(".py", ""))


def get_default_cassette_path(item: Item) -> str:
    """Return the cassette full path given the test item."""
    test = item.location[2]
    test_file_path = item.location[0]
    cassette_path = get_cassette_folder_path(test_file_path)
    return f"{cassette_path}/{test}.yaml"


def delete_cassette(cassette_path: str):
    """Delete the provided cassette from disk."""
    if os.path.exists(cassette_path):
        os.remove(cassette_path)


def test_failed(item: Item) -> bool:
    """Check the reports and determine if a test has failed."""
    return (item.reports["setup"] and item.reports["setup"].failed) or \
           (item.reports["call"] and item.reports["call"].failed) or \
           (item.reports["teardown"] and item.reports["teardown"].failed)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: Item, nextitem: Optional[Item]):
    yield
    markers = list(item.iter_markers(marker_name))
    cassettes = set()
    skip = False

    if len(markers) > 0 and test_failed(item):
        # at least a marker was used and the test has failed
        for mark in markers:
            if mark.kwargs.get("skip", False):
                # This test has been marked as skip: no cassette will be deleted
                skip = True
            if len(mark.args) == 0 or mark.args[0] is None or mark.kwargs.get("delete_default", False):
                # No argument was used on the marker or the delete_default argument has been forced True
                # add the default cassette to the set
                cassettes.add(get_default_cassette_path(item))
            if len(mark.args) > 0:
                if isinstance(mark.args[0], list):
                    # some argument was specified
                    for cassette in mark.args[0]:
                        # iterate on the provided list
                        if callable(cassette):
                            try:
                                # if it's a function try to execute it and save the returned value
                                cassette = cassette(item)
                            except Exception:
                                pass
                        if isinstance(cassette, str):
                            # add the cassette to the set if it's a string
                            cassettes.add(cassette)
        if not skip:
            for cassette in cassettes:
                delete_cassette(cassette)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", f"{marker_name}(cassette_path_list: Optional[List[Union[str, Callable[[Item], str]]]],"
                   f" delete_default: Optional[bool], skip: Optional[bool]): the cassettes that will be deleted on"
                   f" test failure; list elements can be cassette string paths or functions that will return a"
                   f" string path from a pytest nodes.Item object. If no argument or None or an empty list are"
                   f" passed to the marker the cassette will be determined automatically. If the argument"
                   f" delete_default=True is used, the automatically determined cassette will be deleted even with a"
                   f" non empty cassette_path_list. If the argument skip=True is used, no cassette will be deleted at"
                   f" all. This marker can be used multiple times."
    )
