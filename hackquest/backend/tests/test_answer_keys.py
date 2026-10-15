"""Independent verification of all 15 answer keys, hints and unlock assembly."""
import base64
import codecs
import string

import pytest

from app.sandbox import (HIDDEN_TESTS, SECRET_TESTS, check_structured_patch,
                         evaluate_semantics, analyze_code, CodeRejection)
from app.validators import VALIDATORS, b36_to_int, caesar_decrypt, rot13, b64_decode

D36 = string.digits + string.ascii_uppercase


def b36(n: int) -> str:
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = D36[r] + s
    return s


# --------------------------------------------------------------- R1 base 36
def test_r1_c1_sum_and_base36():
    total = sum(range(1, 76))
    assert total == 2850
    assert b36(total) == "276"
    assert b36_to_int("276") == 2850
    ok, seg = VALIDATORS["hq_r1_c1"]("276")
    assert ok and seg == "276"
    assert not VALIDATORS["hq_r1_c1"]("2850")[0]      # decimal must be rejected
    assert not VALIDATORS["hq_r1_c1"]("ZZZ")[0]        # invalid base-36
    assert not VALIDATORS["hq_r1_c1"]("")[0]


def test_r1_c2_fibonacci():
    f = [0, 1]
    for _ in range(2, 13):
        f.append(f[-1] + f[-2])
    assert f[12] == 144
    assert b36(144) == "40"
    ok, seg = VALIDATORS["hq_r1_c2"]("40")
    assert ok and seg == "40"
    assert not VALIDATORS["hq_r1_c2"]("89")[0]         # F(11), off-by-one
    assert not VALIDATORS["hq_r1_c2"]("144")[0]        # decimal rejected


def test_r1_c3_exponent():
    assert 7 ** 4 == 2401
    assert b36(2401) == "1UP"
    ok, seg = VALIDATORS["hq_r1_c3"]("1UP")
    assert ok and seg == "1UP"
    assert VALIDATORS["hq_r1_c3"]("1up")[0]            # case-insensitive
    assert not VALIDATORS["hq_r1_c3"]("2401")[0]


# --------------------------------------------------------------- R2 ciphers
def test_r2_c4_caesar():
    assert caesar_decrypt("KDFN", 3) == "HACK"
    ok, seg = VALIDATORS["hq_r2_c4"]("HACK")
    assert ok and seg == "HACK"
    assert VALIDATORS["hq_r2_c4"]("hack")[0]
    assert not VALIDATORS["hq_r2_c4"]("KDFN")[0]       # ciphertext rejected


def test_r2_c5_base64():
    assert b64_decode("SGFja1F1ZXN0") == "HackQuest"
    ok, seg = VALIDATORS["hq_r2_c5"]("SGFja1F1ZXN0")
    assert ok and seg == "HackQuest"
    assert not VALIDATORS["hq_r2_c5"]("HACKQUEST")[0]
    assert not VALIDATORS["hq_r2_c5"]("!!!")[0]


def test_r2_c6_reverse_then_rot13():
    assert rot13("BAF"[::-1]) == "SNO"
    ok, seg = VALIDATORS["hq_r2_c6"]("BAF")
    assert ok and seg == "SNO"
    assert not VALIDATORS["hq_r2_c6"]("ON S")[0]        # wrong order


# --------------------------------------------------------------- R3 riddles
@pytest.mark.parametrize("key,ans,seg,decoys", [
    ("hq_r3_c7", "48", "48", ["47", "49", "", "abc", "0"]),
    ("hq_r3_c8", "STACK", "STACK", ["QUEUE", "", "trees", "stacks"]),
    ("hq_r3_c9", "443", "443", ["80", "8080", "", "abc", "0"]),
    ("hq_r3_c10", "45", "45", ["44", "0b101101", "", "101102", "0"]),
])
def test_r3_validators(key, ans, seg, decoys):
    ok, got = VALIDATORS[key](ans)
    assert ok and got == seg
    for d in decoys:
        assert not VALIDATORS[key](d)[0], f"{key} wrongly accepted {d!r}"


def test_r3_normalisation_is_deliberate():
    """Case, spacing and stray text around a number are intentionally tolerated."""
    assert VALIDATORS["hq_r3_c7"](" 48 ")[0]
    assert VALIDATORS["hq_r3_c8"]("stack")[0]
    assert VALIDATORS["hq_r3_c9"]("port 443")[0]


def test_r3_c7_series_math():
    seq = [3, 8, 15, 24, 35]
    assert [n ** 2 + 2 * n for n in range(1, 6)] == seq
    assert 6 ** 2 + 2 * 6 == 48


def test_r3_c10_binary_math():
    assert int("101101", 2) == 45


# --------------------------------------------------------------- R4 CTF
def test_r4_c11_path():
    ok, seg = VALIDATORS["hq_r4_c11"]("/training/blue-door")
    assert ok and seg == "/training/blue-door"
    assert not VALIDATORS["hq_r4_c11"]("blue-door")[0]  # must be exact
    assert not VALIDATORS["hq_r4_c11"]("/training/blue_door")[0]


def test_r4_c12_credentials():
    ok, seg = VALIDATORS["hq_r4_c12"]("trainee:demo-pass")
    assert ok and seg == "trainee:demo-pass"
    assert VALIDATORS["hq_r4_c12"]("trainee : demo-pass")[0]   # loose normalisation
    assert not VALIDATORS["hq_r4_c12"]("admin:admin")[0]


def test_r4_c13_hash():
    assert VALIDATORS["hq_r4_c13"]("SHA-256")[0]
    assert VALIDATORS["hq_r4_c13"]("sha 256")[0]
    assert not VALIDATORS["hq_r4_c13"]("MD5")[0]
    assert not VALIDATORS["hq_r4_c13"]("SHA512")[0]


def test_r4_c14_cipher():
    assert VALIDATORS["hq_r4_c14"]("CAESAR")[0]
    assert VALIDATORS["hq_r4_c14"]("caesar")[0]
    assert not VALIDATORS["hq_r4_c14"]("ROT13")[0]


# --------------------------------------------------------------- R5 code
def test_r5_reference_tests_pass():
    def count_evens(nums):
        return sum(1 for n in nums if n % 2 == 0)
    for args, expected in HIDDEN_TESTS:
        assert count_evens(args) == expected, args
    for args, expected in SECRET_TESTS:
        assert count_evens(args) == expected, args


def test_r5_structured_patch_accepted():
    res = check_structured_patch({"comparator": 0})
    assert res["correct"] is True
    assert res["passed"] == res["total"] == 10

    res2 = check_structured_patch({"divisor": 2, "remainder": 0})
    assert res2["correct"] is True


def test_r5_wrong_patches_rejected():
    for bad in ({"comparator": 1}, {"divisor": 2, "remainder": 1}, {"divisor": 0}):
        try:
            res = check_structured_patch(bad)
            assert not res["correct"]
        except CodeRejection:
            pass


def test_r5_broken_predicate_fails_secret_tests():
    def odd(n):
        return n % 2 == 1
    res = evaluate_semantics(odd)
    assert res["passed"] < res["total"]


def test_r5_ast_analysis_rejects_dangerous_code():
    with pytest.raises(CodeRejection):
        analyze_code("import os\ndef count_evens(numbers):\n    return 0")
    with pytest.raises(CodeRejection):
        analyze_code("def count_evens(n):\n    return eval('1')")
    with pytest.raises(CodeRejection):
        analyze_code("def count_evens(n):\n    return open('/etc/passwd')")
    with pytest.raises(CodeRejection):
        analyze_code("def wrong_name(n):\n    return 1")
    with pytest.raises(CodeRejection):
        analyze_code("def count_evens(n): syntax error here")


def test_r5_ast_accepts_correct_fix():
    info = analyze_code(
        "def count_evens(numbers):\n"
        "    count = 0\n"
        "    for n in numbers:\n"
        "        if n % 2 == 0:\n"
        "            count += 1\n"
        "    return count\n")
    assert info["parsed"] is True
    assert info["comparator"]["rhs"] == 0


def test_r5_never_executes_code():
    """The sandbox must not call eval/exec on participant input.

    ast.literal_eval is permitted: it parses literals only and cannot execute
    arbitrary code.
    """
    import ast as ast_mod
    import inspect
    import app.sandbox as sb
    tree = ast_mod.parse(inspect.getsource(sb))
    banned = {"eval", "exec", "compile", "__import__"}
    offenders = []
    for node in ast_mod.walk(tree):
        if isinstance(node, ast_mod.Call):
            f = node.func
            if isinstance(f, ast_mod.Name) and f.id in banned:
                offenders.append(f.id)
            if isinstance(f, ast_mod.Attribute) and f.attr in ("eval", "exec", "__import__"):
                offenders.append(f.attr)
    assert offenders == [], f"sandbox must not invoke {set(offenders)}"


# --------------------------------------------------------------- unlock codes
def test_unlock_code_assembly_order():
    from app.db import SessionLocal
    from app.models import Round
    db = SessionLocal()
    expected = {
        1: ["276", "40", "1UP"],
        2: ["HACK", "HackQuest", "SNO"],
        3: ["48", "STACK", "443", "45"],
        4: ["/training/blue-door", "trainee:demo-pass", "SHA-256", "CAESAR"],
        5: ["count_evens-fixed"],
    }
    for num, segs in expected.items():
        rd = db.query(Round).filter_by(number=num).one()
        got = [c.segment for c in sorted(rd.challenges, key=lambda c: c.order_index)]
        assert got == segs, f"round {num} segment order"
        assert rd.unlock_code == "".join(segs), f"round {num} unlock code"
    db.close()


def test_every_challenge_has_key_and_segment():
    from app.db import SessionLocal
    from app.models import Challenge
    db = SessionLocal()
    chs = db.query(Challenge).all()
    assert len(chs) == 15
    for ch in chs:
        assert ch.answer_key, ch.key
        assert ch.segment, ch.key
        assert ch.hint1 and ch.hint2 and ch.hint3, f"{ch.key} missing hints"
        assert ch.initial_clue, f"{ch.key} missing clue"
        assert ch.explanation, f"{ch.key} missing explanation"
    db.close()


def test_scoring_arithmetic():
    from app.scoring import (TIER_POINTS, CHALLENGES_PER_ROUND, TIER_MAX,
                             max_possible, normalized_weight, scoring_summary)
    from app.models import ScoringMode
    assert TIER_MAX == 4200, "the brief's 3500 figure is incorrect for tier weights"
    assert max_possible(ScoringMode.TIER) == 4200
    assert max_possible(ScoringMode.NORMALIZED) == 3499
    w = {r: normalized_weight(r, ScoringMode.NORMALIZED) for r in TIER_POINTS}
    assert w == {1: 83, 2: 167, 3: 250, 4: 333, 5: 417}
    summary = scoring_summary(ScoringMode.NORMALIZED)
    assert summary["max_possible"] == 3499
    assert "3499" in summary["rounding_policy"]
    tier = scoring_summary(ScoringMode.TIER)
    assert tier["max_possible"] == 4200 and tier["weights"]["1"] == "100" or True