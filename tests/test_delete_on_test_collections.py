import textwrap

import pytest

# noinspection PyUnusedLocal
# language=python prefix="if True:" # IDE language injection
fail_on_setup_test = textwrap.dedent(
    """
        import pytest
        import requests
            
        @pytest.fixture
        def setup():
            requests.get("{url}")
            assert False
            
        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail
        class TestCollection:
        
            def test_first(self, setup):
                assert True
        
            def test_second(self, setup):
                assert True
        """
)
# language=python prefix="if True:" # IDE language injection
fail_on_call_test = textwrap.dedent(
    """
        import pytest
        import requests
            
        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail
        class TestCollection:
        
            def test_first(self):
                requests.get("{url}")
                assert False
        
            def test_second(self):
                requests.get("{url}")
                assert False
        """
)
# noinspection PyUnusedLocal
# language=python prefix="if True:" # IDE language injection
fail_on_teardown_test = textwrap.dedent(
    """
        import pytest
        import requests
            
        @pytest.fixture
        def teardown():
            yield
            requests.get("{url}")
            assert False
            
        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail
        class TestCollection:
        
            def test_first(self, teardown):
                assert True
        
            def test_second(self, teardown):
                assert True
        """
)


class TestATestCollections:
    """Test: A test collections..."""

    #
    #
    #
    @pytest.mark.parametrize(
        "test_source,outcomes",
        [
            (fail_on_setup_test, {"errors": 2}),
            (fail_on_call_test, {"failed": 2}),
            (fail_on_teardown_test, {"errors": 2, "passed": 2}),
        ],
        ids=["setup", "call", "teardown"],
    )
    def test_should_delete_cassettes_on_fail(
        self,
        test_source,
        outcomes,
        add_test_file,
        run_tests,
        get_test_cassettes,
        default_conftest,
        test_url,
    ):
        """A test collections should delete cassettes on fail."""
        test = add_test_file(test_source.format(url=test_url))
        assert run_tests().outcomes_are(**outcomes)
        assert not get_test_cassettes(test)

    #
    #
    #
    def test_should_be_able_to_handle_nested_marker(
        self, add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
    ):
        """A test collections should be able to handle nested marker."""
        test_name = "test_custom"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import pytest
            import requests
            import vcr

            my_vcr = vcr.VCR(record_mode="once")

            additional = "cassettes/{test_name}/additional.yaml"

            @pytest.mark.vcr
            @pytest.mark.vcr_delete_on_fail
            class TestCollection:

                @pytest.mark.vcr_delete_on_fail([additional])
                def test_first(self):
                    requests.get("{test_url}")
                    with my_vcr.use_cassette(additional):
                        requests.get("{test_url}")
                    assert False

                @pytest.mark.vcr_delete_on_fail(skip=True)
                def test_second(self):
                    requests.get("{test_url}")
                    assert False
            """
        test = add_test_file(test_source, name=test_name)
        assert run_tests().outcomes_are(failed=2)
        cassettes = get_test_cassettes(test)
        assert "TestCollection.test_second.yaml" in map(lambda x: x.name, cassettes)
        assert len(cassettes) == 1

    #
    #
    #
    def test_should_mark_failed_class_setup_or_teardown(self, add_test_file, run_tests):
        """A test collections should mark failed class setup or teardown."""
        # language=python prefix="if True:" # IDE language injection
        test_source = """
            import pytest
    
            @pytest.mark.order(1)
            class TestSetToFail:
                @pytest.fixture(scope="class", autouse=True)
                def setup_phase(self):
                    raise Exception
                @pytest.mark.xfail
                def test_should_fail_at_class_setup(self):
                    pass
    
            @pytest.mark.order(2)
            class TestAlsoSetToFail:
                @pytest.fixture(scope="class", autouse=True)
                def teardown_phase(self):
                    yield
                    raise Exception
                @pytest.mark.xfail
                def test_should_fail_at_class_teardown(self):
                    pass
    
            # NOTE: this must be run together with and after the TestSetToFail and TestAlsoSetToFail classes since it 
            # checks the recorded reports on THOSE tests
            @pytest.mark.order(3)
            def test_failing_at_setup_time_should_have_a_report_claiming_so(request):
                cls = list(filter(lambda x: x.name == "test_should_fail_at_class_setup", request.session.items))[0].cls
                assert cls.cls_setup_failed
                cls = list(
                    filter(
                        lambda x: x.name == "test_should_fail_at_class_teardown",
                         request.session.items
                    )
                )[0].cls
                assert cls.cls_teardown_failed
            """
        add_test_file(test_source)
        assert run_tests().outcomes_are(xfailed=2, xpassed=1, passed=1)
