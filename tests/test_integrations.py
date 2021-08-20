import os
import shutil

import pytest
import textwrap

from tests.conftest import fails, cassettes_remaining


@pytest.fixture
def enc_teardown():
    yield
    shutil.rmtree("tests/enc")


def test_it_can_integrate_with_vcrpy_encrypt(enc_teardown):
    """It can integrate with vcrpy_encrypt"""
    # Prepare the conftest to configure vcrpy_encrypt
    conftest_string = textwrap.dedent("""
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
                """)
    folder = "tests/enc"
    if not os.path.isdir(folder):
        os.mkdir(folder)
        with open(f"{folder}/__init__.py", "w") as f:
            f.write("")
    with open(f"{folder}/conftest.py", "w") as f:
        f.write(conftest_string)

    test_string = textwrap.dedent("""
                import pytest
                import requests
                from tests.enc.conftest import vcr_delete_on_fail

                @pytest.mark.vcr
                @vcr_delete_on_fail
                def test_this():
                    requests.get("https://github.com")
                    assert False
                """)
    assert fails(test_string, subfolder="enc")
    assert cassettes_remaining(path=f"{folder}/cassettes/test_temp_{hash(test_string)}") == 0


@pytest.fixture
def class_setup_teardown():
    yield
    shutil.rmtree("tests/class_setup")


@pytest.fixture
def class_teardown_teardown():
    yield
    shutil.rmtree("tests/class_teardown")


def test_it_can_integrate_with_the_class_setup_workflow(class_setup_teardown):
    """it can integrate with the class setup workflow"""
    test_string = textwrap.dedent("""
        import os
        import pytest
        import requests
        import vcr
        from typing import Union
        from pytest_vcr_delete_on_fail import has_class_scoped_setup_failed

        def get_setup_cassette_path(node) -> str:
            # determine the class setup cassette path from the node
            el = node.nodeid.split("::")
            name = f"{el[1]}_setup"
            path = os.path.join(os.path.dirname(el[0]), "cassettes", os.path.basename(el[0]).replace(".py", ""))
            return f"{path}/{name}.yaml"

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
                request.cls.value = requests.get("https://github.com")
                raise Exception

            def test_failing_at_class_setup(self):
                assert self.value.status_code == 200
                requests.get("https://gitlab.com")
        """)
    assert fails(test_string, "class_setup")
    assert cassettes_remaining(path=f"tests/class_setup/cassettes/test_temp_{hash(test_string)}") == 0


def test_it_integrates_with_the_class_teardown_workflow(class_teardown_teardown):
    """it integrates with the class teardown workflow"""
    test_string = textwrap.dedent("""
        import os
        import pytest
        import requests
        import vcr
        from typing import Union
        from pytest_vcr_delete_on_fail import has_class_scoped_teardown_failed

        def get_teardown_cassette_path(node) -> str:
            # determine the class teardown cassette path from the node
            el = node.nodeid.split("::")
            name = f"{el[1]}_teardown"
            path = os.path.join(os.path.dirname(el[0]), "cassettes", os.path.basename(el[0]).replace(".py", ""))
            return f"{path}/{name}.yaml"

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
            def teardown(self, vcr_teardown):
                yield
                # class scoped teardown, with vcr_teardown fixture
                r = requests.get("https://github.com")
                if self.value.status_code == r.status_code:
                    raise Exception

            def test_failing_at_class_teardown(self, request):
                r = requests.get("https://gitlab.com")
                request.cls.value = r
        """)
    assert fails(test_string, "class_teardown")
    assert cassettes_remaining(path=f"tests/class_teardown/cassettes/test_temp_{hash(test_string)}") == 0
