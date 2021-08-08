import os
import textwrap

import pytest

from tests.conftest import run_test


@pytest.fixture
def setup(request):
    assert request.param
    yield


@pytest.fixture
def teardown(request):
    yield
    assert request.param


fail_on_setup = (False, True, True)
fail_on_call = (True, False, True)
fail_on_teardown = (True, True, False)


@pytest.mark.vcr
@pytest.mark.xfail
@pytest.mark.parametrize("setup,call,teardown",
                         [fail_on_setup, fail_on_call, fail_on_teardown], indirect=["setup", "teardown"])
def test_runner_report(setup, call, teardown):
    """The delete module should register single test reports when failing: REGISTER"""
    assert call


# NOTE: this must be run together with test_runner_report since it checks the recorded reports on THAT parametric test
def test_check_runners(request):
    """The delete module should register single test reports when failing: CHECK"""
    def get_reports(description):
        name = f"test_runner_report[{description[0]}-{description[1]}-{description[2]}]"
        return list(filter(lambda t: t.name == name, request.session.items))[0].reports

    failed_on_setup = get_reports(fail_on_setup)
    assert failed_on_setup["setup"].skipped
    assert failed_on_setup["call"] is None
    assert failed_on_setup["teardown"].passed
    failed_on_call = get_reports(fail_on_call)
    assert failed_on_call["setup"].passed
    assert failed_on_call["call"].skipped
    assert failed_on_call["teardown"].passed
    failed_on_teardown = get_reports(fail_on_teardown)
    assert failed_on_teardown["setup"].passed
    assert failed_on_teardown["call"].passed
    assert failed_on_teardown["teardown"].skipped


class TestWhenDealingWithASingleTest:
    """Test: When dealing with a single test..."""

    def test_should_be_able_to_delete_the_cassette_on_test_call_fail(self):
        """When dealing with a single test should be able to delete the cassette on test call fail."""

        test_string = textwrap.dedent("""
            import pytest
            import requests
                
            @pytest.fixture(scope="module")
            def vcr_config():
                return {"record_mode": ["once"]}
            
            @pytest.mark.vcr
            def test_this():
                requests.get("https://github.com")
                assert False
            """)
        ret = run_test(test_string)
        assert ret == 1
        assert len(os.listdir("tests/cassettes")) == 0
