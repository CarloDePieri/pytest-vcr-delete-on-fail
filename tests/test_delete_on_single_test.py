import pytest

# language=python prefix="if True:" # IDE language injection
fail_on_call_test = """
    import pytest
    import requests
    
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_this():
        requests.get("{}")
        assert False
    """
# noinspection PyUnreachableCode, PyUnusedLocal
# language=python prefix="if True:" # IDE language injection
fail_on_setup_test = """
    import pytest
    import requests
        
    @pytest.fixture
    def setup():
        requests.get("{}")
        assert False
        yield
    
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_this(setup):
        assert True
    """
# noinspection PyUnusedLocal
# language=python prefix="if True:" # IDE language injection
fail_on_teardown_test = """
    import pytest
    import requests
        
    @pytest.fixture
    def teardown():
        yield
        requests.get("{}")
        assert False
    
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_this(teardown):
        assert True
    """


class TestWhenDealingWithASingleTest:
    """Test: When dealing with a single test..."""

    #
    #
    #
    def test_it_should_be_able_to_add_report_to_the_test_node(
        self, add_test_file, run_tests
    ):
        """When dealing with a single test it should be able to add report to the test node."""

        # language=python prefix="if True:" # IDE language injection
        source = """
            import pytest
            
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
            @pytest.mark.order(1)
            @pytest.mark.parametrize("setup,call,teardown",
                                     [fail_on_setup, fail_on_call, fail_on_teardown], indirect=["setup", "teardown"])
            def test_runner_report(setup, call, teardown):
                assert call
            
            # NOTE: this must be run together with and after test_runner_report since it checks the recorded reports
            # on THAT parametric test
            @pytest.mark.order(2)
            def test_check_runners(request):
                def get_reports(description):
                    name = f"test_runner_report[{description[0]}-{description[1]}-{description[2]}]"
                    return list(filter(lambda t: t.name == name, request.session.items))[0].reports
                failed_on_setup = get_reports(fail_on_setup)
                # These are flagged as skipped because of xfail
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
                    """

        add_test_file(source)
        assert run_tests().outcomes_are(xpassed=1, xfailed=3, passed=1)

    #
    #
    #
    def test_should_not_delete_the_cassette_when_passing(
        self, add_test_file, default_conftest, test_url, run_tests
    ):
        """When dealing with a single test should not delete the cassette when passing."""

        # language=python prefix="if True:" # IDE language injection
        source = f"""
            import pytest
            import requests
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            def test_this():
                requests.get("{test_url}")
                assert True
                    """

        add_test_file(source)
        assert run_tests().outcomes_are(passed=1)

    #
    #
    #
    @pytest.mark.parametrize(
        "test_source,outcome",
        [
            (fail_on_setup_test, {"errors": 1}),
            (fail_on_call_test, {"failed": 1}),
            (fail_on_teardown_test, {"passed": 1, "errors": 1}),
        ],
        ids=["fail_on_setup_test", "fail_on_call_test", "fail_on_teardown_test"],
    )
    def test_should_delete_the_cassette_when_failing(
        self,
        test_source,
        outcome,
        default_conftest,
        add_test_file,
        test_url,
        run_tests,
        get_test_cassettes,
    ):
        """When dealing with a single test should delete the cassette when failing."""
        test = add_test_file(test_source.format(test_url))
        assert run_tests().outcomes_are(**outcome)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_be_possible_to_express_a_custom_cassette_path(
        self, add_test_file, test_url, run_tests, get_test_cassettes, is_file
    ):
        """When dealing with a single test it should be possible to express a custom cassette path."""
        custom_cassette = "tests/cassettes/custom.yaml"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            import vcr
            
            my_vcr = vcr.VCR(record_mode="once")
                
            @pytest.mark.vcr_delete_on_fail(["{custom_cassette}"])
            def test_this():
                with my_vcr.use_cassette("{custom_cassette}"):
                    requests.get("{test_url}")
                assert False
            """
        add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1)
        assert not is_file(custom_cassette)

    #
    #
    #
    def test_should_delete_the_cassette_even_with_nested_folders(
        self, pytester, add_test_file, default_conftest, get_test_cassettes, test_url
    ):
        """When dealing with a single test should delete the cassette even with nested folders."""
        pytester.mkpydir("submodule")
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            def test_this():
                requests.get("{test_url}")
                assert False
            """
        test = add_test_file(source=test_source, name="submodule/test_file")
        result = pytester.runpytest()
        assert result.outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_should_manage_multiple_markers(
        self, add_test_file, test_url, default_conftest, run_tests, get_test_cassettes
    ):
        """When dealing with a single test should manage multiple markers."""
        test_name = "test_custom"

        # language=python prefix="test_name: str\nif True:" # IDE language injection
        test_source = f"""        
            import pytest
            import requests
            import vcr
            
            my_vcr = vcr.VCR(record_mode="once")
            
            def get_additional_cassette(salt):
                return f"cassettes/{test_name}/additional_{{salt}}.yaml"
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            @pytest.mark.vcr_delete_on_fail([get_additional_cassette("a")])
            @pytest.mark.vcr_delete_on_fail([get_additional_cassette("b"), get_additional_cassette("c")])
            def test_this():
                requests.get("{test_url}")
                with my_vcr.use_cassette(get_additional_cassette("a")):
                    requests.get("{test_url}")
                with my_vcr.use_cassette(get_additional_cassette("b")):
                    requests.get("{test_url}")
                with my_vcr.use_cassette(get_additional_cassette("c")):
                    requests.get("{test_url}")
                assert False
                """
        test = add_test_file(source=test_source, name=test_name)
        assert run_tests().outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_the_marker_should_be_able_to_take_a_function_as_argument(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test the marker should be able to take a function as argument."""
        test_name = "test_custom"

        # language=python prefix="test_name: str\nif True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            import vcr

            my_vcr = vcr.VCR(record_mode="once")

            def get_additional_cassette(salt):
                return f"cassettes/{test_name}/additional_{{salt}}.yaml"

            def get_cassette(node):
                file_name = node.parent.name.replace(".py", "")
                return f"cassettes/{{file_name}}/additional_b.yaml"

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail([get_additional_cassette("a"), get_cassette], 
                                                    delete_default=True)
            def test_this():
                requests.get("{test_url}")
                with my_vcr.use_cassette(get_additional_cassette("a")):
                    requests.get("{test_url}")
                with my_vcr.use_cassette(get_additional_cassette("b")):
                    requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source, name=test_name)
        assert run_tests().outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_be_able_to_force_the_deletion_of_the_default_cassette(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should be able to force the deletion of the default cassette."""
        test_name = "test_custom"

        # language=python prefix="test_name=''\nif True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            import vcr

            my_vcr = vcr.VCR(record_mode="once")

            additional = f"cassettes/{test_name}/additional.yaml"

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail([additional], delete_default=True)
            def test_this():
                requests.get("{test_url}")
                with my_vcr.use_cassette(additional):
                    requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source, name=test_name)
        assert run_tests().outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_accept_the_list_as_named_argument(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should accept the list as named argument."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            from pytest_vcr_delete_on_fail import get_default_cassette_path

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail(cassette_path_list=[get_default_cassette_path])
            def test_this():
                requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_should_be_able_to_handle_only_a_function_in_the_marker_argument_list(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test should be able to handle only a function in the marker argument list."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            from pytest_vcr_delete_on_fail import get_default_cassette_path

            def dummy(item):
                return get_default_cassette_path(item)

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail([dummy])
            def test_this():
                requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_handle_none_as_only_argument(
        self, add_test_file, test_url, default_conftest, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should handle None as only argument."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail(None)
            def test_this():
                requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1)
        assert "test_this.yaml" in map(lambda x: x.name, get_test_cassettes(test))

    #
    #
    #
    def test_it_should_not_freak_out_with_an_invalid_marker_function_return(
        self, add_test_file, run_tests
    ):
        """When dealing with a single test it should not freak out with an invalid marker function return."""
        # noinspection PyUnusedLocal
        # language=python prefix="if True:" # IDE language injection
        test_source = """
            import pytest

            def broken(item):
                return 1

            @pytest.mark.vcr_delete_on_fail([broken])
            def test_with_broken_func():
                assert False
            """
        add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, errors=0)

    #
    #
    #
    def test_should_not_freak_out_if_a_provided_function_raise_exceptions(
        self, add_test_file, run_tests
    ):
        """When dealing with a single test should not freak out if a provided function raise exceptions."""
        # noinspection PyUnreachableCode
        # language=python prefix="if True:" # IDE language injection
        test_source = """
            import pytest

            def broken(_):
                raise Exception
                return 1

            @pytest.mark.vcr_delete_on_fail([broken])
            def test_with_raising_func():
                assert False
            """
        add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, errors=0)

    #
    #
    #
    def test_it_should_not_delete_cassettes_if_skip_was_specified(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should not delete cassettes if skip was specified."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            @pytest.mark.vcr_delete_on_fail(skip=True)
            def test_this():
                requests.get("{test_url}")
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1)
        assert "test_this.yaml" in map(lambda x: x.name, get_test_cassettes(test))

    #
    #
    #
    def test_it_should_support_both_a_cassette_list_and_generator(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should support both a cassette list and generator."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.order(1)
            def test_first():
                requests.get("{test_url}")

            @pytest.mark.vcr
            @pytest.mark.order(2)
            def test_second():
                requests.get("{test_url}")

            def generate_one(test_name: str):
                def wrapped(item):
                    return f"cassettes/{{item.fspath.purebasename}}/{{test_name}}.yaml"
                return wrapped
            
            @pytest.mark.vcr_delete_on_fail(
                cassette_path_list=[generate_one("test_first")],
                cassette_path_func=generate_one("test_second"))
            @pytest.mark.order(3)
            def test_third():
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, passed=2)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_support_generator_that_returns_lists(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should support generator that returns lists."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.order(1)
            def test_first():
                requests.get("{test_url}")

            @pytest.mark.vcr
            @pytest.mark.order(2)
            def test_second():
                requests.get("{test_url}")

            def generate_more(test_name_list):
                def wrapped(item):
                    return list(map(lambda x: f"cassettes/{{item.fspath.purebasename}}/{{x}}.yaml", test_name_list))
                return wrapped
            
            @pytest.mark.vcr_delete_on_fail(cassette_path_func=generate_more(["test_first", "test_second"]))
            @pytest.mark.order(3)
            def test_third():
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, passed=2)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_accept_several_marker_with_a_cassette_path_function(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should accept several marker with a cassette path function."""
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.order(1)
            def test_first():
                requests.get("{test_url}")

            @pytest.mark.vcr
            @pytest.mark.order(2)
            def test_second():
                requests.get("{test_url}")

            def generate_one(test_name: str):
                def wrapped(item):
                    return f"cassettes/{{item.fspath.purebasename}}/{{test_name}}.yaml"
                return wrapped
            
            @pytest.mark.vcr_delete_on_fail(cassette_path_func=generate_one("test_first"))
            @pytest.mark.vcr_delete_on_fail(cassette_path_func=generate_one("test_second"))
            @pytest.mark.order(3)
            def test_third():
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, passed=2)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_not_break_with_a_faulty_cassette_path_func(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """When dealing with a single test it should not break with a faulty cassette path func."""
        # noinspection PyUnusedLocal
        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests

            @pytest.mark.vcr
            @pytest.mark.order(1)
            def test_first():
                requests.get("{test_url}")
                
            def generate_broken(test_name: str):
                def wrapped(item):
                    raise Exception("nope")
                return wrapped

            def generate_one(test_name: str):
                def wrapped(item):
                    return f"cassettes/{{item.fspath.purebasename}}/{{test_name}}.yaml"
                return wrapped
            
            @pytest.mark.vcr_delete_on_fail(cassette_path_func=generate_broken("test_first"))
            @pytest.mark.vcr_delete_on_fail(cassette_path_func=generate_one("test_first"))
            @pytest.mark.order(2)
            def test_second():
                assert False
            """
        test = add_test_file(test_source)
        assert run_tests().outcomes_are(failed=1, passed=1, errors=0)
        assert not get_test_cassettes(test)
