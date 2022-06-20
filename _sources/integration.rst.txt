Integrations
============

This page contains examples on how to integrate ``pytest-vcr-delete-on-fail`` with other tools that utilize cassettes,
leveraging its flexible decorator.

It's also a way for me to quickly access implementation that I often reuse.

`vcr-encrypt`_
--------------

A simple tool to encrypt vcrpy cassettes so they can be safely kept under version control.

.. _vcr-encrypt: https://github.com/CarloDePieri/vcrpy-encrypt

.. code-block:: python

    import pytest
    import requests
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
    vcr_delete_on_fail = pytest.mark.vcr_delete_on_fail(
        [
            get_encrypted_cassette,
            get_clear_text_cassette,
        ]
    )


    @pytest.mark.vcr
    @vcr_delete_on_fail
    def test_this():
        requests.get("{test_url}")
        assert False
