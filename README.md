[![PyPI](https://img.shields.io/pypi/v/pytest-vcr-delete-on-fail)](https://pypi.org/project/pytest-vcr-delete-on-fail/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-vcr-delete-on-fail)](https://pypi.org/project/pytest-vcr-delete-on-fail/) [![CI Status](https://img.shields.io/github/workflow/status/CarloDePieri/pytest-vcr-delete-on-fail/prod?logo=github)](https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/actions/workflows/prod.yml) [![Coverage Status](https://coveralls.io/repos/github/CarloDePieri/pytest-vcr-delete-on-fail/badge.svg?branch=main)](https://coveralls.io/github/CarloDePieri/pytest-vcr-delete-on-fail?branch=main) ![Sonarqube ratings](https://img.shields.io/badge/sonarqube%20ratings-A-success) [![Maintenance](https://img.shields.io/maintenance/yes/2022)](https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A pytest plugin that automates vcrpy cassettes deletion on test failure.

## Rationale

Sometimes when testing a function containing multiple http requests a failure will occur halfway through (this happens
all the time when doing TDD). When using [vcrpy](https://github.com/kevin1024/vcrpy) to cache http requests, this could
result in a test cache that only cover a fraction of the function under test, which in turn could prevent the function
to ever succeed or the test to pass in subsequent run if the http requests that didn't get cached depended on a
fresh context (maybe they are time sensitive or there's randomness involved).

This possibility leads to doubt and untrust towards the test suite, which is wrong on too many level.

This plugin provides a pytest marker that solves the uncertainty: when a marked test fails its http requests cache will
be purged, so that it can start fresh on the next run.

## Install

Simply run:

```bash
pip install pytest-vcr-delete-on-fail
```

## Usage

Once the plugin is installed, mark the designated test like this:

```python
import pytest
import requests
import vcr

my_vcr = vcr.VCR(record_mode="once")

cassette_path = "tests/cassettes/this.yaml"

@pytest.mark.vcr_delete_on_fail([cassette_path])
def test_this():
    with my_vcr.use_cassette(cassette_path):
        requests.get("https://github.com")
    assert False
```

Running the test will result in no cassettes on disk: the http request first got cached but since the test failed the
cassette was later deleted.

When using [pytest-recording](https://github.com/kiwicom/pytest-recording) to automatically save cassettes (or when
using its path and naming conventions manually), this plugin's marker can be used without arguments since it will figure
out the cassette path on its own:

```python
import pytest
import requests

# Configure pytest_recording
@pytest.fixture(scope="module")
def vcr_config():
    return {"record_mode": ["once"]}

@pytest.mark.vcr_delete_on_fail
def test_this():
    requests.get("https://github.com")
    assert False
```

## Targeted pytest version

Pytest internal API can change from major version, so this plugin versions are targeted at specific pytest versions.
Do note that, consequently, plugin features can vary as well between major versions.

| pytest-vcr-delete-on-fail | pytest  |
|:-------------------------:|:-------:|
|           1.1.0           |   6.*   |

## Advanced usage

The marker is actually quite flexible; this is the full signature:

```python
pytest.mark.vcr_delete_on_fail(
    cassette_path_list: Optional[List[Union[str, Callable[[Item], str]]]],
    delete_default: Optional[bool],
    skip: Optional[bool])
```

###### cassette_path_list

Either the first unnamed argument or a named one; when both are missing, the cassette path will be automatically
determined. This list's elements can either be `str` or functions that take a pytest `nodes.Item` object and return a
`str`: these are the to-be-deleted cassettes' full path. If `cassette_path_list is None`, no cassette will be deleted
for that test (which is equivalent to pass `skip=True`); if an empty list is passed instead, that marker won't result
in a cassette deletion but it won't prevent other markers to delete cassettes.

###### delete_default

Only valid as named argument. It's `True` by default if no `cassette_path_list` is passed to the marker, `False`
otherwise. If `True` the cassette with the automatically computed path will be deleted.

###### skip

Only valid as named argument. It's `False` by default. If `True` no cassette will be deleted for that test. It's
equivalent to passing `cassette_path_list=None`.

###### cassette_path_func

A function that takes the `nodes.Item` as only argument and that returns a cassette path or a list of cassette paths
that will be deleted.

### Utilities

When writing a function to determine a cassette path here are some useful imports from `pytest_vcr_delete_on_fail`:

###### get_default_cassette_path(item: nodes.Item) -> str

A function that return the path of the default cassette.

###### has_class_scoped_setup_failed(item: nodes.Item) -> bool

It returns True if a class scoped fixture failed in the setup phase. This could come in handy when using class scoped setup: an example
of this pattern can be found in [test_integrations.py](https://github.com/CarloDePieri/pytest-vcr-delete-on-fail/blob/main/tests/test_integrations.py).

###### has_class_scoped_teardown_failed(item: nodes.Item) -> bool

It returns True if a class scoped fixture failed in the teardown phase.

## Development

Install [invoke](http://pyinvoke.org/) and [poetry](https://python-poetry.org/):

```bash
pip install invoke poetry
```

Now clone the git repo:

```bash
git clone https://github.com/CarloDePieri/pytest-vcr-delete-on-fail.git
cd pytest-vcr-delete-on-fail
inv install
```

This will try to create a virtualenv based on `python3.7` and install there all
project's dependencies. If a different python version is preferred, it can be
selected by specifying  the `--python` (`-p`) flag like this:

```bash
inv install -p python3.8
```

The test suite can be run with commands:

```bash
inv test         # run the test suite
inv test-spec    # run the tests while showing the output as a spec document
inv test-cov     # run the tests suite and produce a coverage report
```

To run the test suite against all supported python version (they must be in path!) run:

```bash
inv test-all-python-version
```

To test the GitHub workflow with [act](https://github.com/nektos/act):

```bash
inv act-dev           # test the dev workflow
inv act-dev -c shell  # open a shell in the act container (the above must fail first!)
inv act-dev -c clean  # stop and delete a failed act container
```
