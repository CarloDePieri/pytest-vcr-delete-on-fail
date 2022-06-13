import pytest


class TestADoFContextBlock:
    """Test: A DoF context block..."""

    def test_should_be_able_to_delete_a_cassette(
        self, add_test_file, test_url, pytester, is_file
    ):
        """A DoF context block should be able to delete a cassette."""
        custom_cassette = "cassettes/custom.yaml"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import requests
            import vcr
            from pytest_vcr_delete_on_fail import delete_on_fail
        
            my_vcr = vcr.VCR(record_mode="once")
                
            def test_this():
                with delete_on_fail(["{custom_cassette}"]):
                    with my_vcr.use_cassette("{custom_cassette}"):
                        requests.get("{test_url}")
                    assert False  # intentional fail
            """

        add_test_file(test_source)
        result = pytester.runpytest()

        assert result.outcomes_are(failed=1)
        assert result.has_fail_with_comment("intentional fail")

        assert not is_file(custom_cassette)

    def test_should_be_able_to_delete_a_list_of_cassettes(
        self, add_test_file, test_url, pytester, is_file, has_fail_with_comment
    ):
        """A DoF context block should be able to delete a list of cassettes."""
        custom_cassette_a = "cassettes/custom_a.yaml"
        custom_cassette_b = "cassettes/custom_b.yaml"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import requests
            import vcr
            from pytest_vcr_delete_on_fail import delete_on_fail
        
            my_vcr = vcr.VCR(record_mode="once")
                
            def test_this():
                with delete_on_fail(["{custom_cassette_a}", "{custom_cassette_b}"]):
                    with my_vcr.use_cassette("{custom_cassette_a}"):
                        requests.get("{test_url}")
                    with my_vcr.use_cassette("{custom_cassette_b}"):
                        requests.get("{test_url}")
                    assert False  # intentional fail
            """

        add_test_file(test_source)
        result = pytester.runpytest()

        assert result.outcomes_are(failed=1)
        assert result.has_fail_with_comment("intentional fail")

        assert not is_file(custom_cassette_a)
        assert not is_file(custom_cassette_b)

    def test_should_have_a_way_to_skip_deletion(
        self, add_test_file, test_url, pytester, is_file, has_fail_with_comment
    ):
        """A DoF context block should have a way to skip deletion."""
        custom_cassette = "cassettes/custom.yaml"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import requests
            import vcr
            from pytest_vcr_delete_on_fail import delete_on_fail
        
            my_vcr = vcr.VCR(record_mode="once")
                
            def test_this():
                with delete_on_fail(["{custom_cassette}"], skip=True):
                    with my_vcr.use_cassette("{custom_cassette}"):
                        requests.get("{test_url}")
                    assert False  # intentional fail
            """

        add_test_file(test_source)
        result = pytester.runpytest()

        assert result.outcomes_are(failed=1)
        assert result.has_fail_with_comment("intentional fail")

        assert is_file(custom_cassette)

    def test_should_skip_deletion_with_a_none_or_empty_argument(
        self, add_test_file, test_url, pytester, is_file, has_fail_with_comment
    ):
        """A DoF context block should skip deletion with a None or empty argument."""
        custom_cassette = "cassettes/custom.yaml"

        # language=python prefix="if True:" # IDE language injection
        test_source = f"""
            import requests
            import vcr
            from pytest_vcr_delete_on_fail import delete_on_fail
        
            my_vcr = vcr.VCR(record_mode="once")
                
            def test_this():
                with delete_on_fail([]):
                    with delete_on_fail(None):
                        with my_vcr.use_cassette("{custom_cassette}"):
                            requests.get("{test_url}")
                        assert False  # intentional fail
            """

        add_test_file(test_source)
        result = pytester.runpytest()

        assert result.outcomes_are(failed=1)
        assert result.has_fail_with_comment("intentional fail")

        assert is_file(custom_cassette)
