# Task: Implement a Calculator

Create a file called `calculator.py` in the current directory.

## Requirements

### Function: `calc(expression: str) -> float`

Parse and evaluate a mathematical expression string. Return the result as a float.

**Supported operations** (in order of precedence, lowest to highest):
1. Addition (`+`) and subtraction (`-`)
2. Multiplication (`*`) and division (`/`)
3. Unary negation (`-`)
4. Parentheses (`(`, `)`) for grouping

**Rules:**
- Do NOT use `eval()`, `exec()`, `compile()`, or `ast.literal_eval()`. You must parse the expression yourself.
- Whitespace in expressions should be ignored: `" 2 + 3 "` → `5.0`
- Division by zero should raise `ZeroDivisionError`
- Invalid expressions should raise `ValueError` with a descriptive message
- Results should be floating point (return type is `float`)
- Support decimal numbers: `"3.14 * 2"` → `6.28`
- Support negative numbers: `"-5 + 3"` → `-2.0`
- Nested parentheses must work: `"((2 + 3) * (4 - 1))"` → `15.0`

### CLI Interface

When `calculator.py` is run as a script (`python calculator.py`), it should:
1. Read a single expression from command-line arguments (all args joined with spaces)
2. Print the result to stdout
3. Exit with code 0 on success, code 1 on error (print error message to stderr)

Example:
```
$ python calculator.py 2 + 3 * 4
14.0
$ python calculator.py "(2 + 3) * 4"
20.0
$ python calculator.py 1 / 0
Error: division by zero
```

## Constraints

- Single file: `calculator.py`
- No external dependencies (stdlib only)
- Python 3.10+ compatible
- Do NOT use `eval()` or any code execution function
