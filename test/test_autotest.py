import pytest
import src.autotest as auto

working_code = """
def sum(x: int, y: int) -> int:
    return x + y
"""
no_return_code = """
def sum(x: int, y: int):
    x + y
"""
wrong_type_annotation = """
def sum(x: int, y: int) -> int:
    return float(x + y)
"""
syntax_error_code = """
def syntax_error(x: int, y: int) -> int:
    return x +
"""

infinite_loop_code = """
def infinite(x: int, y: int) -> int:
    while True:
        x + y
"""

@pytest.mark.parametrize(
    "code, expected_result",
    [
        pytest.param(working_code, True, id="working_code"),
        pytest.param(no_return_code, True, id="working_code"),
        pytest.param(wrong_type_annotation, False, id="wrong_type"),
        pytest.param(syntax_error_code, False, id="syntax_error"),
        pytest.param(infinite_loop_code, False, id="infinite_loop"),
    ]
)
def test_autotest(code, expected_result):
    result = auto.autotest(code)
    assert result.passed == expected_result
