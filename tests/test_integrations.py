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

                # Define a shorthand for the delete_cassette_on_failure marker
                vcr_delete_on_fail = pytest.mark.delete_cassette_on_failure([get_encrypted_cassette,
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


def test_it_can_integrate_with_the_class_setup_workflow(class_setup_teardown):
    """it can integrate with the class setup workflow"""
    test_string = textwrap.dedent("""
        import os
        import pytest
        import requests
        import vcr

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

        # this marker is from pytest_recording, will record requests from tests
        @pytest.mark.vcr
        # the class setup cassette can be deleted by passing the same function used by vcr_setup
        @pytest.mark.delete_cassette_on_failure([get_setup_cassette_path], delete_default=True)
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
