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


def get_cassette_folder_path(test_file_path: str) -> str:
    """Return the cassette path given the test file path."""
    return os.path.join(
        os.path.dirname(test_file_path),
        "cassettes",
        os.path.basename(test_file_path).replace(".py", ""))


def get_default_cassette_path(item) -> str:
    """Return the cassette full path given the test item."""
    test = item.location[2]
    test_file_path = item.location[0]
    cassette_path = get_cassette_folder_path(test_file_path)
    return f"{cassette_path}/{test}.yaml"


def delete_cassette(cassette_path: str):
    """Delete the provided cassette from disk."""
    if os.path.exists(cassette_path):
        os.remove(cassette_path)


def test_failed(item) -> bool:
    """Check the reports and determine if a test has failed."""
    return (item.reports["setup"] and item.reports["setup"].failed) or \
           (item.reports["call"] and item.reports["call"].failed) or \
           (item.reports["teardown"] and item.reports["teardown"].failed)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    yield
    markers = list(item.iter_markers("delete_cassette_on_failure"))
    if len(markers) > 0 and test_failed(item):
        # at least a marker was used and the test has failed
        use_default_cassette = False
        for mark in markers:
            if len(mark.args) == 0 or mark.kwargs.get("delete_default", False):
                # No argument was used on the marker or the delete_default argument has been forced True:
                # use the default cassette
                use_default_cassette = True
            if len(mark.args) > 0:
                # some argument was specified
                for cassette in mark.args[0]:
                    if callable(cassette):
                        try:
                            cassette = cassette(item)
                        except Exception:
                            pass
                    if isinstance(cassette, str):
                        delete_cassette(cassette)
        if use_default_cassette:
            cassette = get_default_cassette_path(item)
            delete_cassette(cassette)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "delete_cassette_on_failure(cassette_path_list): the cassettes to be deleted on test failure;" +
                   " the list elements can be string or callable(item) -> str where item is a pytest nodes.Item" +
                   " object); if no argument is specified (or the argument delete_default=True is used), the cassette" +
                   " will be determined automatically. This marker can be used multiple times."
    )
