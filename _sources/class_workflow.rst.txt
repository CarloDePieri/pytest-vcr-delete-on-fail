Class setup/teardown workflow
=============================

.. py:currentmodule:: pytest_vcr_delete_on_fail

Handling cassettes recording and deletion on failure inside class scoped setup / teardown is an often needed feature
but not immediate to implement (internally pytest treats *function scoped* and *class scoped* failures slightly
differently).

These are two viable different implementations, base respectively on :py:func:`pytest.mark.vcr_delete_on_fail` and on
:py:func:`vcr_and_dof`.


vcr_delete_on_fail
------------------

.. code-block:: python

    import pytest
    import requests
    import vcr
    from typing import Union
    from pytest_vcr_delete_on_fail import has_class_scoped_setup_failed
    from contextlib import contextmanager
    from pathlib import Path


    def get_setup_cassette_path(node) -> str:
        # determine the class setup cassette path from the node
        name = f"{node.cls.__name__}.__setup__.yaml"
        return str(Path(node.path.parent / "cassettes" / node.path.stem / name))


    @pytest.fixture(scope="class")
    def vcr_setup(request):
        # This fixture returns a context manager that records network
        # requests to a class setup cassette
        cassette_path = get_setup_cassette_path(request.node)
        setup_vcr = vcr.VCR(record_mode=["once"])

        @contextmanager
        def _wrapped(**kwargs):
            with setup_vcr.use_cassette(cassette_path, **kwargs) as v:
                yield v

        return _wrapped


    def get_class_setup_cassette_if_failed(item) -> Union[str, None]:
        # check if the class has been flagged with a failed class setup, after the test has run
        if has_class_scoped_setup_failed(item):
            # return the class setup cassette path; this could, if needed, return a list of
            # all class cassettes
            return get_setup_cassette_path(item)
        # otherwise return None


    # This marker is responsible for the deletion of the setup cassette on fail
    delete_setup_on_fail = pytest.mark.vcr_delete_on_fail(
        [get_class_setup_cassette_if_failed]
    )


    @delete_setup_on_fail
    class TestATestCollection:

        @pytest.fixture(scope="class", autouse=True)
        def setup(self, request, vcr_setup):
            with vcr_setup():
                # Everything in here will be recorded on the setup cassette
                request.cls.value = requests.get("{test_url}")
                raise Exception
            # Do note that this yield should be outside the vcr_setup block, otherwise
            # every network request performed by this class' tests will be recorded
            # in the setup cassette
            yield

        def test_failing_at_class_setup(self):
            # This won't even run, since it will fail at setup time
            assert self.value.status_code == 200


Between the two, this is the more verbose solution. It has the advantage that it can detect a failure in
a ``setup`` setup fixture, since it uses :py:func:`pytest.mark.vcr_delete_on_fail`.

.. note:: The full signature of :py:func:`has_class_scoped_setup_failed` and :py:func:`has_class_scoped_teardown_failed`
    can be found in the API Reference.

vcr_and_dof
-----------

.. code-block:: python

    import pytest
    import requests
    import vcr
    from pytest_vcr_delete_on_fail import vcr_and_dof
    from contextlib import contextmanager
    from pathlib import Path

    my_vcr = vcr.VCR(record_mode="once")

    # The following fixture returns a context manager that records network request to a class
    # setup cassette. It will also delete said cassette if an exception is raised
    @pytest.fixture(scope="class")
    def vcr_and_dof_setup(request):
        name = f"{{request.node.cls.__name__}}.__setup__.yaml"
        cassette_path = str(
            Path(request.node.path.parent / "cassettes" / request.path.stem / name)
        )

        @contextmanager
        def _wrapped(**kwargs):
            with vcr_and_dof(my_vcr, cassette_path, **kwargs) as v:
                yield v

        return _wrapped


    class TestATestCollection:

        code: int

        @pytest.fixture(scope="class", autouse=True)
        def setup(self, request, vcr_and_dof_setup):
            with vcr_and_dof_setup(
                # if needed, all class cassettes can be deleted on fail by adding them here
                additional_cassettes=[],
            ):
                # Everything in here will be recorded on the setup cassette
                # Any exception will immediately delete the cassette
                request.cls.code = requests.get("{test_url}").status_code
                raise Exception
            # Do note that this yield should be outside the vcr_and_dof_setup block, otherwise every
            # network request performed by this class tests will be recorded in the setup cassette.
            # Also, every exception will trigger the setup cassette deletion
            yield

        def test_failing_at_class_setup(self):
            # This won't even run, since it will fail at setup time
            assert self.code == 200


While being more concise and simple, this solution only detect failures inside the ``vcr_and_dof_setup``
context manager.