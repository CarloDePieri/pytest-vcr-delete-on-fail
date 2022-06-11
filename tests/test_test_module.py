import pytest


#
#
#
def test_it_should_handle_automatically_more_than_one_test_file(
    pytester, add_test_file
):
    """It should handle automatically more than one test file"""
    # language=python prefix="if True:" # IDE language injection
    t_0_source = """
        def test_first():
            assert True
        """
    add_test_file(t_0_source, connect_debugger=False)

    # language=python prefix="if True:" # IDE language injection
    t_1_source = """
        def test_second():
            assert False
        """
    add_test_file(t_1_source, connect_debugger=False)

    # language=python prefix="if True:" # IDE language injection
    t_2_source = """
        def test_third():
            assert True
        """
    add_test_file(t_2_source, connect_debugger=False, name="test_custom")

    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=2)

    # Check in the test stdout that the correct filename are present
    for test_name in [
        "test_it_should_handle_automatically_more_than_one_test_file.py",
        "test_it_should_handle_automatically_more_than_one_test_file_1.py",
        "test_custom.py",
    ]:
        assert (
            len(list(filter(lambda line: test_name in line, result.stdout.lines))) > 0
        )


#
#
#
class TestARemoteDebuggerInjecter:
    """Test: A remote debugger injecter..."""

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, pytester, add_test_file):
        """TestARemoteDebuggerInjecter setup"""
        # language=python prefix="if True:" # IDE language injection
        t_0_source = """
            def test_first():
                assert True
            """
        add_test_file(t_0_source, connect_debugger=True, name="test_file")

    def test_should_result_in_a_module(self, pytester, is_file):
        """A remote debugger injecter should result in a module."""
        assert is_file("__init__.py")

    def test_should_inject_the_debugger_in_the_test_file(self, pytester):
        """A remote debugger injecter should inject the debugger in the test file."""
        test_file_lines = pytester.run("cat", "test_file.py").stdout.lines
        assert (
            test_file_lines[0]
            == "from .debugger import connect_debugger; connect_debugger()"
        )

    def test_should_make_available_the_debug_module(self, pytester):
        """A remote debugger injecter should make available the debug module."""
        out = pytester.run("cat", "debugger.py").stdout.lines
        assert "connect_debugger" in out[3]


#
#
#
def test_it_should_allow_to_make_assertions_about_cassettes(
    pytester, add_test_file, get_test_cassettes, default_conftest, test_url
):
    """It should allow to make assertions about cassettes"""
    # language=python prefix="if True:" # IDE language injection
    t_0_source = f"""
        import pytest
        import requests
            
        @pytest.mark.vcr
        def test_first():
            assert requests.get("{test_url}").status_code == 200
        """
    t_0 = add_test_file(t_0_source, connect_debugger=False)

    # language=python prefix="if True:" # IDE language injection
    t_1_source = f"""
        import requests
            
        def test_second():
            assert requests.get("{test_url}").status_code == 200
        """
    t_1 = add_test_file(t_1_source, connect_debugger=False)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)

    t_0_cassettes_names = map(lambda x: x.name, get_test_cassettes(t_0))
    assert "test_first.yaml" in t_0_cassettes_names
    assert "test_second.yaml" not in t_0_cassettes_names

    t_1_cassettes = get_test_cassettes(t_1)
    assert not t_1_cassettes


#
#
#
def test_it_should_handle_assertions_about_nested_modules_cassettes(
    pytester, add_test_file, get_test_cassettes, default_conftest, test_url
):
    """It should handle assertions about nested modules cassettes."""
    # language=python prefix="if True:" # IDE language injection
    t_0_source = f"""
        import pytest
        import requests
            
        @pytest.mark.vcr
        def test_first():
            assert requests.get("{test_url}").status_code == 200
        """
    pytester.mkpydir("test_nested")

    t_0 = add_test_file(
        t_0_source, connect_debugger=False, name="test_nested/test_nested_module"
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)

    t_0_cassettes_names = map(lambda x: x.name, get_test_cassettes(t_0))
    assert "test_first.yaml" in t_0_cassettes_names


#
#
#
@pytest.mark.parametrize(
    "value,test_id",
    [(True, "first"), (True, "second"), (False, "third")],
    ids=["first", "second", "third"],
)
def test_it_should_not_break_with_parametric_tests(
    value, test_id, pytester, add_test_file, is_file
):
    """It should not break with parametric tests."""

    # language=python prefix="value: bool\nif True:" # IDE language injection
    source = f"""
        def test_this():
            assert {value}
        """
    _ = add_test_file(source, connect_debugger=False)

    assert is_file(f"test_it_should_not_break_with_parametric_tests[{test_id}].py")

    result = pytester.runpytest()
    if value:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(failed=1)


#
#
#
def test_it_has_a_simple_way_to_check_for_a_file_existence(is_file, pytester):
    """It has a simple way to check for a file existence"""
    filename_a = "test-file_a"
    filename_b = "module/test-file_b[param].py"
    pytester.run("touch", f"{filename_a}")
    pytester.run("mkdir", "module")
    pytester.run("touch", f"{filename_b}")
    assert is_file(filename_a)
    assert is_file(filename_b)
    assert not is_file("not-there")


#
#
#
def test_it_should_offer_an_integrated_test_http_server(
    pytester, add_test_file, test_url
):
    """It should offer an integrated test http server"""
    # language=python prefix="if True:" # IDE language injection
    source = f"""
        import requests
        
        def test_this():
            assert requests.get("{test_url}").status_code == 200
        """
    _ = add_test_file(source)
    pytester.runpytest().assert_outcomes(passed=1)
