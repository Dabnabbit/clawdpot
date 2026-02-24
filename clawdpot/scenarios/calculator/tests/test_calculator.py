"""Judge tests for the calculator scenario.

15 tests covering arithmetic, parentheses, errors, and edge cases.
These tests are copied into the workdir and run against the AI-generated
calculator.py to objectively score the output.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# Import calculator.py from the workdir (current directory when pytest runs)
_calc_path = Path(__file__).parent.parent / "calculator.py"
if not _calc_path.exists():
    # When run inside workdir, calculator.py is at the root
    _calc_path = Path("calculator.py")


def _load_calc():
    """Dynamically import calculator.py from the working directory."""
    path = Path("calculator.py").resolve()
    if not path.exists():
        pytest.skip("calculator.py not found")
    spec = importlib.util.spec_from_file_location("calculator", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def calc():
    """Provide the calc() function from the generated calculator.py."""
    mod = _load_calc()
    if not hasattr(mod, "calc"):
        pytest.fail("calculator.py does not define a calc() function")
    return mod.calc


# --- Basic arithmetic (4 tests) ---

def test_addition(calc):
    assert calc("2 + 3") == pytest.approx(5.0)


def test_subtraction(calc):
    assert calc("10 - 4") == pytest.approx(6.0)


def test_multiplication(calc):
    assert calc("3 * 7") == pytest.approx(21.0)


def test_division(calc):
    assert calc("15 / 4") == pytest.approx(3.75)


# --- Operator precedence (2 tests) ---

def test_precedence_mul_before_add(calc):
    """2 + 3 * 4 should be 14, not 20."""
    assert calc("2 + 3 * 4") == pytest.approx(14.0)


def test_precedence_complex(calc):
    """10 - 2 * 3 + 4 / 2 should be 6."""
    assert calc("10 - 2 * 3 + 4 / 2") == pytest.approx(6.0)


# --- Parentheses (3 tests) ---

def test_parentheses_simple(calc):
    assert calc("(2 + 3) * 4") == pytest.approx(20.0)


def test_parentheses_nested(calc):
    assert calc("((2 + 3) * (4 - 1))") == pytest.approx(15.0)


def test_parentheses_deep(calc):
    assert calc("(((1 + 2)))") == pytest.approx(3.0)


# --- Edge cases (3 tests) ---

def test_whitespace_handling(calc):
    assert calc("  2  +  3  ") == pytest.approx(5.0)


def test_decimal_numbers(calc):
    assert calc("3.14 * 2") == pytest.approx(6.28)


def test_negative_unary(calc):
    assert calc("-5 + 3") == pytest.approx(-2.0)


# --- Error handling (2 tests) ---

def test_division_by_zero(calc):
    with pytest.raises(ZeroDivisionError):
        calc("1 / 0")


def test_invalid_expression(calc):
    with pytest.raises(ValueError):
        calc("2 + + 3")


# --- No eval() check (1 test) ---

def test_no_eval():
    """Verify calculator.py does not use eval(), exec(), or compile()."""
    p = Path("calculator.py")
    if not p.exists():
        pytest.skip("calculator.py not found")
    source = p.read_text(encoding="utf-8")
    # Simple check: these strings should not appear outside comments
    lines = [line for line in source.splitlines()
             if line.strip() and not line.strip().startswith("#")]
    code = "\n".join(lines)
    for forbidden in ("eval(", "exec(", "compile(", "ast.literal_eval("):
        assert forbidden not in code, f"calculator.py uses forbidden function: {forbidden}"
