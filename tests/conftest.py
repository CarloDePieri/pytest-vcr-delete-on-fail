import os
import pytest
import shutil


test_cassettes_folder = "tests/cassettes"


#
# ensure the cassettes folder used for testing is cleared before every test
#
@pytest.fixture(scope="function")
def clear_cassettes():
    if os.path.isdir(test_cassettes_folder):
        shutil.rmtree(test_cassettes_folder)
    yield


def run_test(test_string: str, subfolder: str = "", delete_test: bool = True) -> int:
    """Write the test string to a temporary unique file and run pytest on it. Return the exit code."""
    # make sure the test file is unique - this will prevent caching
    test_folder = os.path.join("tests", subfolder)
    if subfolder != "":
        if not os.path.isdir(test_folder):
            os.mkdir(test_folder)
    test_file_path = os.path.join(test_folder, f"test_temp_{hash(test_string)}.py")
    with open(test_file_path, "w") as f:
        f.write(test_string)
    ret_code = pytest.main([test_file_path])
    # NOTE: does NOT delete the subfolder, since there could be cassettes to test on there
    if delete_test:
        os.remove(test_file_path)
    return ret_code


@pytest.fixture(scope="module")
def vcr_config():
    return {"record_mode": ["once"]}


def passes(test_string: str, subfolder: str = "", delete_test: bool = True) -> bool:
    """Execute the test_string test and return True if it was successful."""
    return run_test(test_string, subfolder, delete_test) == 0


def fails(
    test_string: str, subfolder: str = "", error_code: int = 1, delete_test: bool = True
) -> bool:
    """Execute the test_string test and return True if it failed with a specific error_code (1 by default)."""
    return run_test(test_string, subfolder, delete_test) == error_code


def cassettes_remaining(test_string: str = None, path: str = None) -> int:
    """Return the number of file left in a test cassettes folder."""
    if test_string is None and path is None:
        raise RuntimeError("Missing at least one argument")
    else:
        if path:
            folder = path
        else:
            folder = f"tests/cassettes/test_temp_{hash(test_string)}"
        return len(os.listdir(folder))
