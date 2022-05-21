import textwrap

import pytest

from tests.conftest import passes, fails, cassettes_remaining

fail_on_setup_test = textwrap.dedent(
    """
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
            
        @pytest.fixture
        def setup():
            requests.get("https://github.com")
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
fail_on_call_test = textwrap.dedent(
    """
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
            
        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail
        class TestCollection:
        
            def test_first(self):
                requests.get("https://github.com")
                assert False
        
            def test_second(self):
                requests.get("https://github.com")
                assert False
        """
)
fail_on_teardown_test = textwrap.dedent(
    """
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
        @pytest.mark.vcr_delete_on_fail
        class TestCollection:
        
            def test_first(self, teardown):
                assert True
        
            def test_second(self, teardown):
                assert True
        """
)


@pytest.mark.usefixtures("clear_cassettes")
class TestATestCollections:
    """Test: A test collections..."""

    @pytest.mark.parametrize(
        "test_string", [fail_on_setup_test, fail_on_call_test, fail_on_teardown_test]
    )
    def test_should_delete_cassettes_on_fail(self, test_string):
        """A test collections should delete cassettes on fail."""
        assert fails(test_string)
        assert cassettes_remaining(test_string) == 0

    def test_should_be_able_to_handle_nested_marker(self):
        """A test collections should be able to handle nested marker."""
        test_string = textwrap.dedent(
            """
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
                @pytest.mark.vcr_delete_on_fail
                class TestCollection:

                    @pytest.mark.vcr_delete_on_fail([additional])
                    def test_first(self):
                        requests.get("https://github.com")
                        with my_vcr.use_cassette(additional):
                            requests.get("https://github.com")
                        assert False

                    @pytest.mark.vcr_delete_on_fail(skip=True)
                    def test_second(self):
                        requests.get("https://github.com")
                        assert False
                """
        )
        assert fails(test_string)
        assert cassettes_remaining(test_string) == 1

    def test_should_mark_failed_class_setup_or_teardown(self):
        """A test collections should mark failed class setup or teardown."""
        test_string = textwrap.dedent(
            """
        import pytest

        @pytest.mark.order(1)
        class TestSetToFail:
            @pytest.fixture(scope="class", autouse=True)
            def setup(self):
                raise Exception
            @pytest.mark.xfail
            def test_should_fail_at_class_setup(self):
                pass

        @pytest.mark.order(2)
        class TestAlsoSetToFail:
            @pytest.fixture(scope="class", autouse=True)
            def teardown(self):
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
            cls = list(filter(lambda x: x.name == "test_should_fail_at_class_teardown", request.session.items))[0].cls
            assert cls.cls_teardown_failed
        """
        )
        assert passes(test_string)
