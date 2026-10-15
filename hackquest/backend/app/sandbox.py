"""Safe handling of the Round 5 code challenge.

DESIGN DECISION - why there is no `eval`/`exec` here:

The competition API process must never execute participant-supplied Python.
`eval`, `exec` and `restricted` are all escapable and would give any participant
arbitrary code execution on the server, which is both a total compromise of the
platform and, for a student event, a serious liability.

Instead this module provides two safe submission paths:

1. `analyze_code` - static AST analysis. Parses (never executes) the submitted
   function and rejects dangerous constructs.
2. `check_structured_patch` - participants submit the fix as a structured
   declaration rather than free code. The result is computed by *our* trusted
   function, so participant text never becomes code.

A real execution sandbox (gVisor / Firecracker container) is the right way to run
participant code for real. `CONTAINER_SANDBOX_CMD` may be set to enable it in a
hardened deployment; it is intentionally unset by default. See
docs/SECURITY.md.
"""
import ast
import json

from .validators import norm_int

FORBIDDEN_NODES = (
    ast.Import, ast.ImportFrom,
    ast.Global, ast.Nonlocal,
)

FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "input",
    "globals", "locals", "vars", "getattr", "setattr", "delattr",
    "breakpoint", "memoryview", "exit", "quit",
}

FORBIDDEN_ATTRS = {
    "__class__", "__bases__", "__subclasses__", "__globals__",
    "__code__", "__mro__", "__builtins__", "__reduce__", "__import__",
}


class CodeRejection(Exception):
    pass


def analyze_code(code: str) -> dict:
    """Statically parse participant code. Never executes it."""
    code = (code or "").strip()
    if not code:
        raise CodeRejection("No code submitted.")
    if len(code) > 8000:
        raise CodeRejection("Submission too long (8000 characters max).")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise CodeRejection(f"Syntax error on line {e.lineno}: {e.msg}")

    fn = next((n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "count_evens"), None)
    if fn is None:
        raise CodeRejection("Define a function named count_evens(numbers).")

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            raise CodeRejection("Imports and global declarations are not permitted.")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise CodeRejection(f"Use of '{node.id}' is not permitted.")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            raise CodeRejection(f"Attribute '{node.attr}' is not permitted.")
        if isinstance(node, ast.While):
            raise CodeRejection("Loops beyond the provided 'for' are not permitted.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("print",):
            continue

    # Extract the comparison used inside the function, if present.
    # `if n % 2 == 0` parses as Compare(BinOp(n % 2), Eq, 0), so the modulo
    # expression lives in Compare.left, not directly as a Name.
    comparator = None
    for node in ast.walk(fn):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        binop = None
        if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Mod):
            binop = node.left
        elif isinstance(node.left, ast.Name):
            binop = node.left  # bare `n == 0`
        if binop is None:
            continue
        try:
            rhs = ast.literal_eval(node.comparators[0])
        except (ValueError, TypeError, SyntaxError):
            rhs = None
        comparator = {
            "operator": "%",
            "lhs": binop.id if isinstance(binop, ast.Name) else "<expr>",
            "rhs": rhs,
            "comparator": type(node.ops[0]).__name__,
        }
    return {"parsed": True, "lines": len(code.splitlines()), "comparator": comparator}


def _reference_even_test(n: int) -> bool:
    """Trusted ground truth supplied by the platform, not the participant."""
    return n % 2 == 0


HIDDEN_TESTS = [
    ([], 0),
    ([1, 3, 5], 0),
    ([2, 4, 6], 3),
    ([0, 1, 2], 2),
    ([-2, -1, 0, 3, 4], 3),
]

# Additional tests kept server-side and never sent to participants.
SECRET_TESTS = [
    ([7, 8, 9, 10], 2),
    ([-4, -3, -2], 2),
    ([0], 1),
    (list(range(1, 21)), 10),
    ([2] * 50, 50),
]


def evaluate_semantics(even_predicate) -> dict:
    """Run the hidden tests against a trusted predicate.

    `even_predicate` is a platform-owned callable, never participant code.
    """
    passed, results = 0, []
    for args, expected in HIDDEN_TESTS + SECRET_TESTS:
        got = sum(1 for n in args if even_predicate(n))
        ok = got == expected
        passed += ok
        results.append({"input": args, "expected": expected,
                        "got": got, "passed": ok})
    return {"passed": passed,
            "total": len(HIDDEN_TESTS) + len(SECRET_TESTS),
            "results": results}


def check_structured_patch(patch: dict) -> dict:
    """Validate a structured fix declaration.

    Accepted shapes:
        {"comparator": 0}              -> n % 2 == 0
        {"operator": "%", "rhs": 0}    -> same
        {"divisor": 2, "remainder": 0}  -> same
    """
    if not isinstance(patch, dict):
        raise CodeRejection("Submit the fix as a structured object.")

    divisor, remainder = None, None
    if "comparator" in patch:
        remainder = norm_int(str(patch.get("comparator")))
    elif "remainder" in patch:
        remainder = norm_int(str(patch.get("remainder")))
        divisor = norm_int(str(patch.get("divisor", "2")))
    else:
        divisor = norm_int(str(patch.get("divisor", "2"))) if "divisor" in patch else None
        remainder = 0
        if "rhs" in patch:
            remainder = norm_int(str(patch["rhs"]))

    if divisor is None:
        divisor = 2
    if remainder is None:
        remainder = 0
    if divisor == 0:
        raise CodeRejection("Division by zero is undefined.")

    predicate = lambda n: (n % divisor) == remainder  # noqa: E731
    res = evaluate_semantics(predicate)
    return {"correct": res["passed"] == res["total"],
            "passed": res["passed"], "total": res["total"],
            "results": res["results"]}


def parse_json_field(raw: str) -> dict:
    try:
        obj = json.loads(raw)
    except (TypeError, ValueError):
        raise CodeRejection("Malformed JSON payload.")
    if not isinstance(obj, dict):
        raise CodeRejection("Expected a JSON object.")
    return obj


def challenge_segment() -> str:
    return "count_evens-fixed"