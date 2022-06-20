Context Managers
================

.. py:currentmodule:: pytest_vcr_delete_on_fail

While the marker is a good general tool, sometimes a more precise one is needed. Enters the context managers
:py:func:`delete_on_fail` and :py:func:`vcr_and_dof`.

They allow to target only a specific area of a single test. Any failure inside the context manager block will trigger
the deletion of the target cassette(s).

.. note:: The cassette will be deleted immediately after the failure, before exiting the context manager block. This
    means that the deletion will happen **before** any teardown fixtures.

:py:func:`delete_on_fail`
-------------------------

.. code-block:: python

    import requests
    import vcr
    from pytest_vcr_delete_on_fail import delete_on_fail

    my_vcr = vcr.VCR(record_mode="once")
    cassette = "cassettes/custom.yaml"


    def test_this():
        with delete_on_fail(
            [cassette],  # cassette(s) to be deleted on fail
            skip=False,  # optional, whether to skip this deletion
        ):
            with my_vcr.use_cassette(cassette):
                requests.get("https://github.com")
            assert False

Deletes the target cassette(s) if an *Exception* is raised inside the code block. In this example
``cassettes/custom.yaml`` will not be present on disk after the execution leaves the ``delete_on_fail`` code block.

:py:func:`vcr_and_dof`
----------------------

A convenient thin wrapper around both ``delete_on_fail`` and ``VCR().use_cassette``: it allows to record a cassette
and delete it on failure with a single context manager.

.. code-block:: python

    import requests
    import vcr
    from pytest_vcr_delete_on_fail import vcr_and_dof, get_default_cassette_path

    my_vcr = vcr.VCR(record_mode="once")


    def test_this(request):
        # Determine the cassette path programmatically
        cassette = get_default_cassette_path(request.node)
        with vcr_and_dof(
            # This is the VCR instance that will be used to call use_cassette
            my_vcr,
            # This is the cassette to record AND to delete if needed
            cassette,
            # Optionally, it's possible to delete more cassettes on failure
            additional_delete=[],
            # Any additional argument will be passed to use_cassette
            filter_query_parameters=["api_key"]
        ):
            requests.get("https://yourapi.dummy?api_key=secretstring")

.. note:: :py:func:`get_default_cassette_path` is the same function used internally by the marker to determine the
    default cassette path.