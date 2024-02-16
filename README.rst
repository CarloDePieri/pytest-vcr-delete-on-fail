*************************
pytest-vcr-delete-on-fail
*************************

.. image:: https://img.shields.io/pypi/v/pytest-vcr-delete-on-fail
    :target: https://pypi.org/project/pytest-vcr-delete-on-fail/
    :alt: PyPI
.. image:: https://img.shields.io/pypi/pyversions/pytest-vcr-delete-on-fail
    :target: https://pypi.org/project/pytest-vcr-delete-on-fail/
    :alt: PyPI - Python Version
.. image:: https://img.shields.io/github/actions/workflow/status/CarloDePieri/pytest-vcr-delete-on-fail/prod.yml?branch=main
    :target: https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/actions/workflows/prod.yml
    :alt: CI Status
.. image:: https://coveralls.io/repos/github/CarloDePieri/pytest-vcr-delete-on-fail/badge.svg?branch=main
    :target: https://coveralls.io/github/CarloDePieri/pytest-vcr-delete-on-fail?branch=main
    :alt: Coverage status
.. image:: https://img.shields.io/badge/sonarqube%20ratings-A-success
    :alt: Sonarqube ratings: A
.. image:: https://img.shields.io/github/license/CarloDePieri/pytest-vcr-delete-on-fail
    :target: https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/blob/main/LICENSE
    :alt: License: GPL-3.0
.. image:: https://img.shields.io/maintenance/yes/2024
    :target: https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/
    :alt: Maintained!
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code style: black

A pytest plugin that automates vcrpy cassettes deletion on test failure.

.. code-block:: console

    $ pip install pytest-vcr-delete-on-fail

Then, in your test:

.. code-block:: python

    import pytest
    import requests
    import vcr

    my_vcr = vcr.VCR(record_mode="once")

    cassette_path = "tests/cassettes/this.yaml"

    @pytest.mark.vcr_delete_on_fail(cassette_path)
    def test_this():
        with my_vcr.use_cassette(cassette_path):
            requests.get("https://github.com")
        assert False

In this example a cassette will be saved on disk when exiting the ``use_cassette`` context manager, but since the test
eventually fails, the cassette will be deleted after the test teardown.

Rationale
^^^^^^^^^

Sometimes when testing a function containing multiple http requests a failure will occur halfway through (this happens
all the time when doing TDD). When using `vcrpy`_ to cache http requests, this could
result in a test cache that only cover a fraction of the function under test, which in turn could prevent the function
to ever succeed or the test to pass in subsequent run if the http requests that didn't get cached depended on a
fresh context (maybe they are time sensitive or there's randomness involved).

This possibility leads to doubt and lack of trust towards the test suite, which is wrong on too many level.

This plugin provides tools to solve this uncertainty, by deleting a test http requests cache if it fails, so that it
can start fresh on the next run.

.. _vcrpy: https://github.com/kevin1024/vcrpy

.. The documentation index page include only up to this point. The rest appears only on github / pypi.

Docs
----

More information and examples can be found in the in-depth `documentation`_.

.. _documentation: https://carlodepieri.github.io/pytest-vcr-delete-on-fail

Development
-----------

Install `invoke`_ and `poetry`_:

.. _invoke: http://pyinvoke.org/
.. _poetry: https://python-poetry.org/

.. code-block:: console

    $ pip install invoke poetry

Now clone the git repo:

.. code-block:: console

    $ git clone https://github.com/CarloDePieri/pytest-vcr-delete-on-fail.git
    $ cd pytest-vcr-delete-on-fail
    $ inv install

This will try to create a virtualenv based on ``python3.8`` and install there all
project's dependencies. If a different python version is preferred, it can be
selected by specifying  the ``--python`` (``-p``) flag like this:

.. code-block:: console

    $ inv install -p python3.9

The test suite can be run with commands:

.. code-block:: console

    $ inv test         # run the test suite
    $ inv test-cov     # run the tests suite and produce a coverage report

To run the test suite against all supported python version (they must be in path!) run:

.. code-block:: console

    $ inv test-all-python-version

To test the GitHub workflow with `act`_:

.. _act: https://github.com/nektos/act

.. code-block:: console

    $ inv act-dev               # test the dev workflow
    $ inv act-dev -c shell      # open a shell in the act container (the above must fail first!)
    $ inv act-dev -c clean      # stop and delete a failed act container

To write the documentation with autobuild and livereload launch:

.. code-block:: console

    $ inv docs-serve