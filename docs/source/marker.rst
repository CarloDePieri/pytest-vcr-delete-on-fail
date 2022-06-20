Pytest Marker
=============

The main tool offered by this plugin to delete cassettes on failure is the :py:func:`pytest.mark.vcr_delete_on_fail`
decorator.

Automatic naming
----------------

| By default it will target the cassette found at
| ``./cassettes/{module-name}/{test-class-if-any.}{test_name}.yaml``
| which is the same policy used by `pytest-recording`_:

.. _pytest-recording: https://github.com/kiwicom/pytest-recording

.. code-block:: python

    import pytest
    import requests


    # Configure pytest_recording
    @pytest.fixture(scope="module")
    def vcr_config():
        return {"record_mode": ["once"]}


    # this will trigger pytest-recording and record a vcr
    @pytest.mark.vcr
    # this will delete that cassette, if the test fails
    @pytest.mark.vcr_delete_on_fail
    # @pytest.mark.vcr_delete_on_fail()  # alternative syntax
    def test_this():
        requests.get("https://github.com")
        assert False

.. note:: When using the marker decorator, the cassette will be deleted **after** the test teardown phase. This is
    different from how :doc:`the context managers <context_managers>` work.

.. warning:: This marker will delete any cassette found at the given path, even if the test didn't reach the instruction
    that would have recorded a new cassette in the run that resulted in a failure. This is intended to ensure a fresh
    environment after every failure.

The marker is actually quite flexible and accepts several arguments (the full signature can be found
in the API Reference: :py:func:`pytest.mark.vcr_delete_on_fail`).

Multiple cassettes
------------------

More than one cassette can be specified by passing in a list:

.. code-block:: python

    my_vcr = vcr.VCR(record_mode="once")


    def get_cassette_name(letter: str) -> str:
        return f"{letter}.yaml"


    @pytest.mark.vcr_delete_on_fail(["a.yaml", get_cassette_name("b")])
    def test_this():
        with my_vcr.use_cassette("a.yaml"):
            requests.get("https://github.com")
        with my_vcr.use_cassette(get_cassette_name("b")):
            requests.get("https://gitlab.com")
        assert False


.. note:: The marker argument list element ``get_cassette_name("b")`` will execute immediately at test collection time and
    will result in a simple string passed as list element.

Delete cassettes programmatically
---------------------------------

The cassette can also be determined by functions that will run after the test teardown:

.. code-block:: python

    from _pytest.python import Function

    # setup vcr
    my_vcr = vcr.VCR(record_mode="once")


    def get_cassette(node: Function) -> str:
        # the Function argument is a pytest node that has several information about the test
        # and can be used to programmatically build the cassette path
        test_name = node.name
        return f"{test_name}.yaml"


    # a function can be passed as target as a list element. It will run after the test teardown
    @pytest.mark.vcr_delete_on_fail([get_cassette])
    # @pytest.mark.vcr_delete_on_fail(target=get_cassette)  # alternative syntax
    # @pytest.mark.vcr_delete_on_fail.with_args(get_cassette)  # alternative syntax
    def test_this(request):
        # This node is the same Function instance that 'get_cassette' will get as argument later
        node: Function = request.node
        test_name = node.name
        with my_vcr.use_cassette(f"{test_name}.yaml"):
            requests.get("https://github.com")
        assert False

.. warning:: A function `can't be passed directly as the only unnamed marker argument`_. This is why the syntax
    ``@pytest.mark.vcr_delete_on_fail(get_cassette)`` will not work (and will probably means that the test will not
    even be detected).

.. _can't be passed directly as the only unnamed marker argument: https://doc.pytest.org/en/latest/example/markers.html#passing-a-callable-to-custom-markers

Functions and lists can be nested arbitrarily: all ``str`` will be extracted and treated as paths
of cassettes to be deleted.

The correct type for a valid ``target`` can be found in the Api Reference:
:py:data:`pytest_vcr_delete_on_fail.ValidTarget`.

Skip cassette deletion
----------------------

It's possible to selectively skip a cassette deletion, which could come in handy to inspect its content:

.. code-block:: python

    # pytest markers propagate to all test in a class
    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    class TestCollection:

        # this test cassette will be delete, since the test failed
        def test_this(self):
            requests.get("https://github.com")
            assert False

        # this test cassette will remain on disk despite the test failure
        @pytest.mark.vcr_delete_on_fail(skip=True)
        # @pytest.mark.vcr_delete_on_fail(None)  # equivalent to the above
        def test_this_as_well(self):
            requests.get("https://github.com")
            assert False

About pytest fixtures
---------------------

Other than in the test itself, this marker detects failures in every setup / teardown pytest function scoped fixtures.

.. code-block:: python

    import pytest
    import requests


    @pytest.fixture
    def setup_fixture():
        raise Exception
        yield


    @pytest.fixture
    def teardown_fixture():
        yield
        raise Exception


    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_one(setup_fixture):
        assert requests.get("https://github.com").status_code == 200


    @pytest.mark.vcr
    @pytest.mark.vcr_delete_on_fail
    def test_two(teardown_fixture):
        assert requests.get("https://github.com").status_code == 200

Both these tests would result in no cassette saved on disk.