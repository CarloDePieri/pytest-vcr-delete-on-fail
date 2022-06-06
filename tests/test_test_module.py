import os
import shutil

import pytest
import requests
import textwrap
import vcr

from tests.conftest import run_test, test_cassettes_folder


cassette_file = f"{test_cassettes_folder}/test.yaml"


def get_test_string(passing: bool) -> str:
    return textwrap.dedent(
        f"""
                import requests
                import vcr
                
                class TestCollection:
                    def test_this(self):
                        with vcr.use_cassette("{cassette_file}"):
                            requests.get("https://github.com")
                        assert {"True" if passing else "False"}
                """
    )


def there_are_no_temp_file() -> bool:
    return (
        len(list(filter(lambda f: f.startswith("test_temp"), os.listdir("tests")))) == 0
    )


@pytest.mark.usefixtures("clear_cassettes")
class TestTheTestModule:
    """Test: The test module..."""

    @pytest.mark.parametrize(
        "test_string,return_code",
        [(get_test_string(True), 0), (get_test_string(False), 1)],
    )
    def test_should_be_able_to_run_arbitrary_test_files(self, test_string, return_code):
        """The module should be able to run arbitrary test files."""
        ret_code = run_test(test_string)
        assert ret_code == return_code
        assert there_are_no_temp_file()
        assert os.path.isfile(cassette_file)

    @pytest.mark.parametrize("dummy", [True, True])
    def test_should_ensure_that_no_cassette_are_there_at_the_start_of_a_test_a(
        self, dummy
    ):
        """The test module should ensure that no cassette are there at the start of a test a."""
        common_cassette = f"{test_cassettes_folder}/common.yaml"
        assert not os.path.isfile(common_cassette)
        with vcr.use_cassette(f"{common_cassette}"):
            requests.get("https://github.com")

    def test_should_be_able_to_create_file_in_subfolder(self):
        """The test module should be able to create file in subfolder."""
        run_test(get_test_string(True), "submodule")
        assert os.path.isdir("tests/submodule")
        shutil.rmtree("tests/submodule")
