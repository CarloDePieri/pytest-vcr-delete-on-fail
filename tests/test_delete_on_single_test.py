import os
import shutil
import textwrap

import pytest

from tests.conftest import run_test, test_cassettes_folder


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


@pytest.mark.xfail
@pytest.mark.parametrize("setup,call,teardown",
                         [fail_on_setup, fail_on_call, fail_on_teardown], indirect=["setup", "teardown"])
def test_runner_report(setup, call, teardown, clear_cassettes):
    """The delete module should register single test reports when failing: REGISTER"""
    assert call


# NOTE: this must be run together with test_runner_report since it checks the recorded reports on THAT parametric test
def test_check_runners(request, clear_cassettes):
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


fail_on_call_test = textwrap.dedent("""
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
        
        @pytest.mark.vcr
        @pytest.mark.delete_cassette_on_failure
        def test_this():
            requests.get("https://github.com")
            assert False
        """)
fail_on_setup_test = textwrap.dedent("""
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
            
        @pytest.fixture
        def setup():
            requests.get("https://github.com")
            assert False
            yield
        
        @pytest.mark.vcr
        @pytest.mark.delete_cassette_on_failure
        def test_this(setup):
            assert True
        """)
fail_on_teardown_test = textwrap.dedent("""
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
            
        @pytest.fixture
        def teardown():
            yield
            requests.get("https://github.com")
            assert False
        
        @pytest.mark.vcr
        @pytest.mark.delete_cassette_on_failure
        def test_this(teardown):
            assert True
        """)


@pytest.mark.usefixtures("clear_cassettes")
class TestWhenDealingWithASingleTest:
    """Test: When dealing with a single test..."""

    @pytest.mark.parametrize("test_string", [fail_on_setup_test, fail_on_call_test, fail_on_teardown_test])
    def test_should_delete_the_cassette_when_failing(self, test_string):
        """When dealing with a single test should delete the cassette when failing."""
        ret = run_test(test_string)
        assert ret == 1
        cassette_folder = f"{test_cassettes_folder}/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_it_should_be_possible_to_express_a_custom_cassette_path(self):
        """When dealing with a single test it should be possible to express a custom cassette path."""

        custom_cassette = "tests/cassettes/custom.yaml"
        test_string = textwrap.dedent(f"""
            import pytest
            import requests
            import vcr
            
            my_vcr = vcr.VCR(record_mode="once")
                
            @pytest.mark.delete_cassette_on_failure(["{custom_cassette}"])
            def test_this(vcr_delete_test_cassette_on_failure):
                with my_vcr.use_cassette("{custom_cassette}"):
                    requests.get("https://github.com")
                assert False
            """)
        ret = run_test(test_string)
        assert ret == 1
        assert not os.path.isfile(custom_cassette)

    def test_should_delete_the_cassette_even_with_nested_folders(self):
        """When dealing with a single test should delete the cassette even with nested folders."""

        test_string = textwrap.dedent("""
                import pytest
                import requests
                    
                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}
                
                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure
                def test_this():
                    requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string, "submodule")
        assert return_code == 1
        cassette_folder = f"tests/submodule/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0
        # teardown - clean the submodule folder
        shutil.rmtree("tests/submodule")

