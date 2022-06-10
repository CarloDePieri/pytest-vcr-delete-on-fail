import pytest

# language=python prefix="if True:" # IDE language injection
fail_on_call_test = """
    import pytest
    import requests
    
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_this():
        requests.get("https://github.com")
        assert False
    """
# language=python prefix="if True:" # IDE language injection
fail_on_setup_test = """
    import pytest
    import requests
        
    @pytest.fixture
    def setup():
        requests.get("https://github.com")
        assert False
        yield
    
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_this(setup):
        assert True
    """
# language=python prefix="if True:" # IDE language injection
fail_on_teardown_test = """
    import pytest
    import requests
        
    @pytest.fixture
    def teardown():
        yield
        requests.get("https://github.com")
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
        self, pytester, add_test_file
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

        _ = add_test_file(source, connect_debugger=False)
        result = pytester.runpytest()
        result.assert_outcomes(xpassed=1, xfailed=3, passed=1)

    #
    #
    #
    def test_should_not_delete_the_cassette_when_passing(
        self, pytester, add_test_file, default_conftest
    ):
        """When dealing with a single test should not delete the cassette when passing."""

        # language=python prefix="if True:" # IDE language injection
        source = """
            import pytest
            import requests
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            def test_this():
                requests.get("https://github.com")
                assert True
                    """

        _ = add_test_file(source, connect_debugger=False)
        pytester.runpytest().assert_outcomes(passed=1)

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
        pytester,
        get_test_cassettes,
    ):
        """When dealing with a single test should delete the cassette when failing."""
        test = add_test_file(test_source, connect_debugger=False)
        result = pytester.runpytest()
        result.assert_outcomes(**outcome)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_it_should_be_possible_to_express_a_custom_cassette_path(
        self, pytester, add_test_file, get_test_cassettes, is_file
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
                    requests.get("https://github.com")
                assert False
            """
        _ = add_test_file(test_source, connect_debugger=False)
        result = pytester.runpytest()
        result.assert_outcomes(failed=1)
        assert not is_file(custom_cassette)

    #
    #
    #
    def test_should_delete_the_cassette_even_with_nested_folders(
        self, pytester, add_test_file, default_conftest, get_test_cassettes
    ):
        """When dealing with a single test should delete the cassette even with nested folders."""
        pytester.mkpydir("submodule")
        # language=python prefix="if True:" # IDE language injection
        test_source = """
            import pytest
            import requests
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            def test_this():
                requests.get("https://github.com")
                assert False
            """
        test = add_test_file(
            source=test_source, connect_debugger=False, name="submodule/test_file"
        )
        result = pytester.runpytest()
        result.assert_outcomes(failed=1)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_should_manage_multiple_markers(
        self, pytester, add_test_file, default_conftest, get_test_cassettes
    ):
        """When dealing with a single test should manage multiple markers."""
        test_name = "test_custom"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""        
            import pytest
            import requests
            import vcr
            
            my_vcr = vcr.VCR(record_mode="once")
            
            def get_additional_cassette(salt):
                return "cassettes/{{}}/additional_{{}}.yaml".format("{test_name}", salt)
            
            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            @pytest.mark.vcr_delete_on_fail([get_additional_cassette("a")])
            @pytest.mark.vcr_delete_on_fail([get_additional_cassette("b"), get_additional_cassette("c")])
            def test_this():
                requests.get("https://github.com")
                with my_vcr.use_cassette(get_additional_cassette("a")):
                    requests.get("https://github.com")
                with my_vcr.use_cassette(get_additional_cassette("b")):
                    requests.get("https://github.com")
                with my_vcr.use_cassette(get_additional_cassette("c")):
                    requests.get("https://github.com")
                assert False
                """
        test = add_test_file(source=test_source, connect_debugger=False, name=test_name)
        pytester.runpytest().assert_outcomes(failed=1)
        assert not get_test_cassettes(test)
