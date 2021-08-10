import os
import textwrap

import pytest

from tests.conftest import run_test

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
            
        @pytest.mark.vcr
        @pytest.mark.delete_cassette_on_failure
        class TestCollection:
        
            def test_first(self, setup):
                assert True
        
            def test_second(self, setup):
                assert True
        """)
fail_on_call_test = textwrap.dedent("""
        import pytest
        import requests
            
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}
            
        @pytest.mark.vcr
        @pytest.mark.delete_cassette_on_failure
        class TestCollection:
        
            def test_first(self):
                requests.get("https://github.com")
                assert False
        
            def test_second(self):
                requests.get("https://github.com")
                assert False
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
        class TestCollection:
        
            def test_first(self, teardown):
                assert True
        
            def test_second(self, teardown):
                assert True
        """)


@pytest.mark.usefixtures("clear_cassettes")
class TestATestCollections:
    """Test: A test collections..."""

    @pytest.mark.parametrize("test_string", [fail_on_setup_test, fail_on_call_test, fail_on_teardown_test])
    def test_should_delete_cassettes_on_fail(self, test_string):
        """A test collections should delete cassettes on fail."""
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 0

    def test_should_be_able_to_handle_nested_marker(self):
        """A test collections should be able to handle nested marker."""
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
                @pytest.mark.delete_cassette_on_failure
                class TestCollection:

                    @pytest.mark.delete_cassette_on_failure([additional])
                    def test_first(self):
                        requests.get("https://github.com")
                        with my_vcr.use_cassette(additional):
                            requests.get("https://github.com")
                        assert False

                    @pytest.mark.delete_cassette_on_failure(skip=True)
                    def test_second(self):
                        requests.get("https://github.com")
                        assert False
                """)
        return_code = run_test(test_string)
        assert return_code == 1
        cassette_folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        assert len(os.listdir(cassette_folder)) == 1
