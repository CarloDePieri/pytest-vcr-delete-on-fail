import os
import shutil

import pytest
import textwrap

from tests.conftest import fails, cassettes_remaining


@pytest.fixture
def enc_teardown():
    yield
    shutil.rmtree("tests/enc")


def test_it_can_integrate_with_vcrpy_encrypt_easily(enc_teardown):
    """It can integrate with vcrpy_encrypt easily"""

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
