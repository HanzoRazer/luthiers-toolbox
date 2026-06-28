"""Guard test for the complexity-gate identity key.

Locks in the invariant that the baseline key distinguishes same-named methods
in different classes within one file. Without this, dropping the line component
from the key (file:function:line -> file:function) would let one baselined
entry silently suppress a different over-threshold method that happens to share
the bare method name (e.g. two classes each with a complex `validate`).

Add to services/api/tests/test_technical_debt_gates.py (or keep standalone).
Run: services/api/.venv pytest tests/test_complexity_key_collision.py -q
"""
import textwrap

from app.ci.check_complexity import check_complexity


# Two classes, each with a same-named method whose complexity clears threshold=1.
_SAME_NAME_METHODS = textwrap.dedent(
    '''
    class A:
        def validate(self, x):
            if x: return 1
            else: return 2

    class B:
        def validate(self, x):
            if x: return 3
            else: return 4
    '''
)


def _write(tmp_path, body):
    (tmp_path / "app").mkdir(parents=True, exist_ok=True)
    f = tmp_path / "app" / "mod.py"
    f.write_text(body, encoding="utf-8")
    return tmp_path


def test_same_named_methods_are_keyed_distinctly(tmp_path):
    """Two same-named methods in different classes must be keyed distinctly.

    (At threshold=1 radon also enumerates the enclosing classes A and B, so we
    assert on membership/distinctness of the two method keys rather than exact
    equality of the whole violation set.)
    """
    root = _write(tmp_path, _SAME_NAME_METHODS)
    violations = check_complexity(root, threshold=1, baseline=None)

    functions = {v["function"] for v in violations}
    # Qualified (fullname) identity keeps them distinct; a bare-name key would
    # collapse both to "validate".
    assert {"A.validate", "B.validate"} <= functions, functions


def test_baselining_one_does_not_suppress_the_other(tmp_path):
    """Baselining A.validate must NOT suppress B.validate (the false-negative guard)."""
    root = _write(tmp_path, _SAME_NAME_METHODS)
    baseline = {
        "threshold": 1,
        "violation_count": 1,
        "violations": [
            {"file": "app/mod.py", "function": "A.validate", "complexity": 2, "line": 3}
        ],
    }
    violations = check_complexity(root, threshold=1, baseline=baseline)

    remaining = {v["function"] for v in violations}
    assert "A.validate" not in remaining, remaining  # baselined entry suppressed
    assert "B.validate" in remaining, remaining       # the other still caught
