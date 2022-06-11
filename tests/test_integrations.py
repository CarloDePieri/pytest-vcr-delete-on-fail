#
#
#
def test_it_can_integrate_with_vcrpy_encrypt(
    add_test_file, test_url, pytester, get_test_cassettes
):
    """It can integrate with vcrpy_encrypt"""
    pytester.mkpydir("test_enc")

    # noinspection PyUnusedLocal, SpellCheckingInspection
    # language=python prefix="if True:" # IDE language injection
    conftest_source = """
        import pytest
        from vcrpy_encrypt import BaseEncryptedPersister
        from pytest_vcr_delete_on_fail import get_default_cassette_path

        # Configure vcrpy_encrypt
        class MyEncryptedPersister(BaseEncryptedPersister):
            encryption_key: bytes = b"sixteensecretkey"
            should_output_clear_text_as_well = True
            clear_text_suffix = ".custom_clear"
            encoded_suffix = ".custom_enc"

        def pytest_recording_configure(config, vcr):
            vcr.register_persister(MyEncryptedPersister)

        # Configure pytest_recording
        @pytest.fixture(scope="module")
        def vcr_config():
            return {"record_mode": ["once"]}

        # Define two helper functions that will take the default path and append vcrpy_encrypt suffixes
        def get_encrypted_cassette(item) -> str:
            default = get_default_cassette_path(item)
            return f"{default}{MyEncryptedPersister.encoded_suffix}"
        def get_clear_text_cassette(item) -> str:
            default = get_default_cassette_path(item)
            return f"{default}{MyEncryptedPersister.clear_text_suffix}"

        # Define a shorthand for the vcr_delete_on_fail marker
        vcr_delete_on_fail = pytest.mark.vcr_delete_on_fail([get_encrypted_cassette,
                                                                     get_clear_text_cassette])
        """
    add_test_file(conftest_source, name="test_enc/conftest")

    # noinspection PyUnresolvedReferences
    # language=python prefix="if True:" # IDE language injection
    test_source = f"""
        import pytest
        import requests
        from test_enc.conftest import vcr_delete_on_fail

        @pytest.mark.vcr
        @vcr_delete_on_fail
        def test_this():
            requests.get("{test_url}")
            assert False
        """
    test = add_test_file(test_source, name="test_enc/test_enc")

    result = pytester.runpytest()

    assert result.outcomes_are(failed=1)
    assert not get_test_cassettes(test)


#
#
#
def test_it_can_integrate_with_the_class_setup_workflow(
    add_test_file, test_url, run_tests, get_test_cassettes
):
    """it can integrate with the class setup workflow"""
    # noinspection PyUnusedLocal
    # language=python prefix="if True:" # IDE language injection
    test_source = f"""
        import os
        import pytest
        import requests
        import vcr
        from typing import Union
        from pytest_vcr_delete_on_fail import has_class_scoped_setup_failed

        def get_setup_cassette_path(node) -> str:
            # determine the class setup cassette path from the node
            el = node.nodeid.split("::")
            name = f"{{el[1]}}_setup"
            path = os.path.join(os.path.dirname(el[0]), "cassettes", os.path.basename(el[0]).replace(".py", ""))
            return f"{{path}}/{{name}}.yaml"

        @pytest.fixture(scope="class")
        def vcr_setup(request):
            # This fixture records request made during the class scoped function that uses it
            cassette_path = get_setup_cassette_path(request.node)
            setup_vcr = vcr.VCR(record_mode=["once"])
            with setup_vcr.use_cassette(cassette_path):
                yield
                
        def get_class_setup_cassette_if_failed(item) -> Union[str, None]:
            # check if the class has been flagged with a failed class setup
            if has_class_scoped_setup_failed(item):
                # return the class setup cassette path
                return get_setup_cassette_path(item)
            # otherwise return None

        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail([get_class_setup_cassette_if_failed], delete_default=True)
        class TestATestCollection:

            @pytest.fixture(scope="class", autouse=True)
            def setup(self, request, vcr_setup):
                # class scoped setup, with vcr_setup fixture
                request.cls.value = requests.get("{test_url}")
                raise Exception

            def test_failing_at_class_setup(self):
                # This won't play, since it will fail at setup time
                assert self.value.status_code == 200
        """
    test = add_test_file(test_source)

    assert run_tests().outcomes_are(errors=1)
    assert not get_test_cassettes(test)


#
#
#
def test_it_integrates_with_the_class_teardown_workflow(
    add_test_file, default_conftest, test_url, run_tests, get_test_cassettes
):
    """it integrates with the class teardown workflow"""
    # noinspection PyUnusedLocal
    # language=python prefix="if True:" # IDE language injection
    test_source = f"""
        import os
        import pytest
        import requests
        import vcr
        from typing import Union
        from pytest_vcr_delete_on_fail import has_class_scoped_teardown_failed

        def get_teardown_cassette_path(node) -> str:
            # determine the class teardown cassette path from the node
            el = node.nodeid.split("::")
            name = f"{{el[1]}}_teardown"
            path = os.path.join(os.path.dirname(el[0]), "cassettes", os.path.basename(el[0]).replace(".py", ""))
            return f"{{path}}/{{name}}.yaml"

        @pytest.fixture(scope="class")
        def vcr_teardown(request):
            # This fixture records request made during the class scoped function that uses it
            cassette_path = get_teardown_cassette_path(request.node)
            teardown_vcr = vcr.VCR(record_mode=["once"])
            with teardown_vcr.use_cassette(cassette_path):
                yield

        def get_class_teardown_cassette_if_failed(item) -> Union[str, None]:
            # check if the class has been flagged with a failed class teardown
            if has_class_scoped_teardown_failed(item):
                # return the class teardown cassette path
                return get_teardown_cassette_path(item)
            # otherwise return None

        @pytest.mark.vcr
        @pytest.mark.vcr_delete_on_fail([get_class_teardown_cassette_if_failed], delete_default=True)
        class TestATestCollection:

            @pytest.fixture(scope="class", autouse=True)
            def teardown(self, vcr_teardown, request):
                yield
                # class scoped teardown, with vcr_teardown fixture
                r = requests.get("{test_url}")
                raise Exception

            def test_failing_at_class_teardown(self, request):
                r = requests.get("{test_url}")
                assert r.status_code == 200
        """

    test = add_test_file(test_source)

    assert run_tests().outcomes_are(errors=1, passed=1)
    assert not get_test_cassettes(test)
