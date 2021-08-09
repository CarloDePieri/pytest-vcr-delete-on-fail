import os
import pytest


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook used to make available to fixtures tests results.
    To function this presume no stand-alone test: only tests inside classes are supported."""
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
    item.reports[rep.when] = rep


def get_cassette_path(test_file_path: str) -> str:
    """Return the cassette path given the test file path."""
    return os.path.join(
        os.path.dirname(test_file_path),
        "cassettes",
        os.path.basename(test_file_path).replace(".py", ""))


def delete_cassette(cassette_path: str):
    """Delete the provided cassette from disk."""
    # TODO support encrypted cassette
    if os.path.exists(cassette_path):
        os.remove(cassette_path)


def is_test_failed(item) -> bool:
    """Check the reports and determine if a test has failed."""
    return (item.reports["setup"] and item.reports["setup"].failed) or \
           (item.reports["call"] and item.reports["call"].failed) or \
           (item.reports["teardown"] and item.reports["teardown"].failed)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    yield
    mark = item.get_closest_marker("delete_cassette_on_failure")
    if mark is not None and is_test_failed(item):
        if len(mark.args) == 0:
            # use default cassette path
            # TODO provide a way to have a custom function to determine the cassette path
            test = item.location[2]
            test_file_path = item.location[0]
            cassette_path = get_cassette_path(test_file_path)
            cassette = f"{cassette_path}/{test}.yaml"
            delete_cassette(cassette)
        else:
            # custom path has been provided, delete those
            for cassette in mark.args[0]:
                delete_cassette(cassette)


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "delete_cassette_on_failure(custom_list): list of custom cassette to be deleted on test failure;" +
                   "if custom_list is absent, will determine automatically the cassette path"
    )
