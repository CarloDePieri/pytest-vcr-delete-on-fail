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

    def test_should_not_delete_the_cassette_when_passing(self):
        """When dealing with a single test should not delete the cassette when passing."""
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
                    assert True
                """)
        ret = run_test(test_string)
        assert ret == 0
        cassette_folder = f"{test_cassettes_folder}/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 1

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

    def test_should_manage_multiple_markers(self):
        """When dealing with a single test should manage multiple markers."""
        test_string = textwrap.dedent("""
                import os
                import pytest
                import requests
                import vcr

                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}

                my_vcr = vcr.VCR(record_mode="once")

                def get_additional_cassette(salt):
                    file_name = os.path.basename(__file__).replace(".py", "")
                    return f"tests/cassettes/{file_name}/additional_{salt}.yaml"

                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure
                @pytest.mark.delete_cassette_on_failure([get_additional_cassette("a")])
                @pytest.mark.delete_cassette_on_failure([get_additional_cassette("b"), get_additional_cassette("c")])
                def test_this():
                    requests.get("https://github.com")
                    with my_vcr.use_cassette(get_additional_cassette("a")):
                        requests.get("https://github.com")
                    with my_vcr.use_cassette(get_additional_cassette("b")):
                        requests.get("https://github.com")
                    with my_vcr.use_cassette(get_additional_cassette("c")):
                        requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_the_marker_should_be_able_to_take_a_function_as_argument(self):
        """When dealing with a single test the marker should be able to take a function as argument."""
        test_string = textwrap.dedent("""
                import os
                import pytest
                import requests
                import vcr

                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}

                my_vcr = vcr.VCR(record_mode="once")

                def get_additional_cassette(salt):
                    file_name = os.path.basename(__file__).replace(".py", "")
                    return f"tests/cassettes/{file_name}/additional_{salt}.yaml"

                def get_cassette(node):
                    file_name = node.parent.name.replace(".py", "")
                    return f"tests/cassettes/{file_name}/additional_b.yaml"

                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure([get_additional_cassette("a"), get_cassette], 
                                                        delete_default=True)
                def test_this():
                    requests.get("https://github.com")
                    with my_vcr.use_cassette(get_additional_cassette("a")):
                        requests.get("https://github.com")
                    with my_vcr.use_cassette(get_additional_cassette("b")):
                        requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_it_should_be_able_to_force_the_deletion_of_the_default_cassette(self):
        """When dealing with a single test it should be able to force the deletion of the default cassette."""
        test_string = textwrap.dedent("""
                import os
                import pytest
                import requests
                import vcr

                my_vcr = vcr.VCR(record_mode="once")

                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}

                file_name = os.path.basename(__file__).replace(".py", "")
                additional = f"tests/cassettes/{file_name}/additional.yaml"

                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure([additional], delete_default=True)
                def test_this():
                    requests.get("https://github.com")
                    with my_vcr.use_cassette(additional):
                        requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_should_be_able_to_handle_only_a_function_in_the_marker_argument_list(self):
        """When dealing with a single test should be able to handle only a function in the marker argument list."""
        test_string = textwrap.dedent("""
                import pytest
                import requests
                from vcrpy_delete_on_fail import get_default_cassette_path

                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}

                def dummy(item):
                    return get_default_cassette_path(item)

                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure([dummy])
                def test_this():
                    requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_it_should_not_freak_out_with_an_invalid_marker_function_return(self):
        """When dealing with a single test it should not freak out with an invalid marker function return."""
        test_string = textwrap.dedent("""
                import pytest

                def broken(item):
                    return 1

                @pytest.mark.delete_cassette_on_failure([broken])
                def test_with_broken_func():
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1

    def test_should_not_freak_out_if_a_provided_function_raise_exceptions(self):
        """When dealing with a single test should not freak out if a provided function raise exceptions."""
        test_string = textwrap.dedent("""
                import pytest

                def broken(item):
                    raise Exception
                    return 1

                @pytest.mark.delete_cassette_on_failure([broken])
                def test_with_broken_func():
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1

    def test_it_should_not_delete_cassettes_if_skip_was_specified(self):
        """When dealing with a single test it should not delete cassettes if skip was specified."""
        test_string = textwrap.dedent("""
                import pytest
                import requests

                @pytest.fixture(scope="module")
                def vcr_config():
                    return {"record_mode": ["once"]}

                @pytest.mark.vcr
                @pytest.mark.delete_cassette_on_failure
                @pytest.mark.delete_cassette_on_failure(skip=True)
                def test_with_broken_func():
                    requests.get("https://github.com")
                    assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 1
