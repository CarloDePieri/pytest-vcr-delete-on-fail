import os
from typing import Optional, Set, Dict, Any, List, Union, Callable

import pytest
import re

from _pytest.mark import Mark
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo


marker_name = "vcr_delete_on_fail"
cassette_path_list_str = "cassette_path_list"
cassette_path_func_str = "cassette_path_func"
delete_default_str = "delete_default"
skip_str = "skip"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo):
    """Hook used to make available to fixtures tests results."""
    outcome = yield
    rep = outcome.get_result()

    # init the empty reports item if necessary
    if not hasattr(item, "reports"):
        setattr(item, "reports", {"setup": None, "call": None, "teardown": None})

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
        pattern = re.compile(
            r"(@pytest\.fixture\()(.*)(scope\ *\=\ *)([\"\'])(class)([\"\'])(.*)(\))"
        )
        found = pattern.search(report.longreprtext)
        if found:
            return True
    return False


def has_class_scoped_setup_failed(item: Item) -> bool:
    """Return True if test has failed because of a class scoped fixture in the setup phase."""
    return item.cls.cls_setup_failed


def has_class_scoped_teardown_failed(item: Item) -> bool:
    """Return True if test has failed because of a class scoped fixture in the teardown phase."""
    return item.cls.cls_teardown_failed


def get_cassette_folder_path(test_file_path: str) -> str:
    """Return the cassette path given the test file path."""
    return os.path.join(
        os.path.dirname(test_file_path),
        "cassettes",
        os.path.basename(test_file_path).replace(".py", ""),
    )


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
    return (
        (item.reports["setup"] and item.reports["setup"].failed)
        or (item.reports["call"] and item.reports["call"].failed)
        or (item.reports["teardown"] and item.reports["teardown"].failed)
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: Item, nextitem: Optional[Item]):
    yield
    markers = list(item.iter_markers(marker_name))
    cassettes = set()
    skip = False

    if len(markers) > 0 and test_failed(item):
        # at least a marker was used and the test has failed
        for mark in markers:

            arguments = parse_marker_arguments(mark)

            if should_skip_the_test(arguments):
                # This test has been marked as skip: no cassette will be deleted
                skip = True

            mark_cassettes = get_cassettes(arguments, item)
            cassettes = cassettes.union(mark_cassettes)

        if not skip:
            for cassette in cassettes:
                delete_cassette(cassette)


def parse_marker_arguments(mark: Mark) -> Dict[str, Any]:
    """Return a dict with the parsed mark arguments."""
    arguments = mark.kwargs
    if cassette_path_list_str not in arguments and len(mark.args) > 0:
        # use the first unnamed argument as cassette_path_list
        arguments[cassette_path_list_str] = mark.args[0]
    return arguments


def should_skip_the_test(args: Dict[str, Any]) -> bool:
    """Return True if the test should skip cassette deletion. This is caused by a cassette_path_list explicitly set to
    None or by a skip=True argument."""
    return (
        cassette_path_list_str in args and args[cassette_path_list_str] is None
    ) or args.get(skip_str, False)


def should_delete_default_cassette(args: Dict[str, Any]) -> bool:
    """Return True if the default cassette should be deleted. This is caused by a delete_default=True argument or by
    not expressing cassette_path_list (either as named or unnamed arguments)."""
    return args.get(delete_default_str, False) or cassette_path_list_str not in args


def _parse_path_list(
    path_list: List[Union[str, Callable[[Item], str]]], item: Item
) -> Set[str]:
    """Parse the path list and return a set of cassette paths."""
    cassettes = set()
    for cassette in path_list:
        if callable(cassette):
            try:
                cassette = cassette(item)
            except Exception:
                pass
        if isinstance(cassette, str):
            cassettes.add(cassette)
    return cassettes


def _parse_path_func(
    path_func: Callable[[Item], Union[List[str], str]], item: Item
) -> Set[str]:
    """Run the path function and return a set of resulting cassette paths."""
    cassettes = set()
    try:
        generated = path_func(item)
        if isinstance(generated, list):
            for cassette in generated:
                if isinstance(cassette, str):
                    cassettes.add(cassette)
        elif isinstance(generated, str):
            cassettes.add(generated)
    except Exception:
        pass
    return cassettes


def get_cassettes(args: Dict[str, Any], item: Item) -> Set[str]:
    """Return a set of cassette paths derived from the provided marker args."""
    cassettes = set()

    if should_delete_default_cassette(args):
        cassettes.add(get_default_cassette_path(item))

    if cassette_path_list_str in args and isinstance(
        args[cassette_path_list_str], list
    ):
        # The user specified cassette_path_list and it's really a list
        cassettes = cassettes.union(
            _parse_path_list(args[cassette_path_list_str], item)
        )

    if cassette_path_func_str in args and callable(args[cassette_path_func_str]):
        # The user specified a path function
        cassettes = cassettes.union(
            _parse_path_func(args[cassette_path_func_str], item)
        )

    return cassettes


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        f"{marker_name}({cassette_path_list_str}, {delete_default_str}, {skip_str}, {cassette_path_func_str}"
        f"): the cassette that will be deleted on text failure. {cassette_path_list_str}: Optional[List["
        f"Union[str, Callable[[Item], str]]]] is a list of strings or functions that determines which"
        f" cassettes will be deleted; {cassette_path_func_str}: Optional[Callable[[Item], Union[List[str],"
        f" str]]] can express cassette paths as well. In both cases, the Item object is a pytest nodes.Item."
        f" If no argument is passed to the marker the cassette will be determined automatically. If the"
        f" argument {delete_default_str}=True is used, the automatically determined cassette will be deleted"
        f" even when providing a {cassette_path_list_str}. If the argument {skip_str}=True is used or a None"
        f" {cassette_path_list_str} is provided, no cassette will be deleted at all. This marker can be"
        f" used multiple times.",
    )
