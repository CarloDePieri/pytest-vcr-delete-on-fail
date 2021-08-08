import os
import pytest
import shutil


test_cassettes_folder = "tests/cassettes"


#
# ensure the cassettes folder used for testing is cleared before every test
#
@pytest.fixture(scope="function", autouse=True)
def clear_cassettes():
    if os.path.isdir(test_cassettes_folder):
        shutil.rmtree(test_cassettes_folder)
    yield


def run_test(test_string: str) -> int:
    """Write the test string to a temporary unique file and run pytest on it. Return the exit code."""
    # make sure the test file is unique - this will prevent caching
    test_file_path = f"tests/test_temp_{hash(test_string)}.py"
    with open(test_file_path, "w") as f:
        f.write(test_string)
    ret_code = pytest.main(["-x", test_file_path])
    os.remove(test_file_path)
    return ret_code


@pytest.fixture(scope="module")
def vcr_config():
    return {"record_mode": ["once"]}
