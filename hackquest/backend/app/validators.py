"""Server-side answer normalisation and validation.

Every answer is validated on the server. No key or expected unlock code is ever
returned to a participant-facing endpoint.
"""
import base64
import codecs
import re
import string
from typing import Callable

B36_DIGITS = string.digits + string.ascii_uppercase


# ---------------------------------------------------------------- normalisers
def norm_upper_strip(v: str) -> str:
    return re.sub(r"\s+", "", (v or "").strip().upper())


def norm_loose(v: str) -> str:
    """Uppercase, collapse whitespace, drop punctuation."""
    return re.sub(r"[^A-Z0-9/]+", "", (v or "").upper())


def norm_int(v: str):
    m = re.search(r"-?\d+", (v or "").replace(",", ""))
    return int(m.group()) if m else None


def b36_to_int(s: str):
    s = (s or "").strip().upper()
    if not s or any(c not in B36_DIGITS for c in s):
        return None
    try:
        return int(s, 36)
    except ValueError:
        return None


# ---------------------------------------------------------------- transforms
def caesar_decrypt(text: str, shift: int) -> str:
    out = []
    for c in text:
        if c.isupper():
            out.append(chr((ord(c) - 65 - shift) % 26 + 65))
        elif c.islower():
            out.append(chr((ord(c) - 97 - shift) % 26 + 97))
        else:
            out.append(c)
    return "".join(out)


def rot13(text: str) -> str:
    return codecs.encode(text, "rot_13")


def b64_decode(text: str):
    try:
        pad = "=" * (-len(text) % 4)
        return base64.b64decode(text + pad).decode("utf-8")
    except Exception:
        return None


# ---------------------------------------------------------------- validators
# Each validator receives the normalised submission and returns (ok, canonical)
# `canonical` is the accepted segment used to build the unlock code.

VALIDATORS: dict[str, Callable[[str], tuple[bool, str]]] = {}


def validator(key: str):
    def wrap(fn):
        VALIDATORS[key] = fn
        return fn
    return wrap


@validator("hq_r1_c1")
def v_r1_c1(sub: str):
    v = b36_to_int(sub)
    if v is None:
        return False, ""
    expected = sum(range(1, 76))          # 2850
    return v == expected, "276"


@validator("hq_r1_c2")
def v_r1_c2(sub: str):
    v = b36_to_int(sub)
    if v is None:
        return False, ""
    f = [0, 1]
    for _ in range(2, 13):
        f.append(f[-1] + f[-2])
    return v == f[12], "40"                # F(12) = 144


@validator("hq_r1_c3")
def v_r1_c3(sub: str):
    v = b36_to_int(sub)
    if v is None:
        return False, ""
    return v == 7 ** 4, "1UP"              # 2401


@validator("hq_r2_c4")
def v_r2_c4(sub: str):
    return norm_upper_strip(sub) == "HACK", "HACK"


@validator("hq_r2_c5")
def v_r2_c5(sub: str):
    # Base64 is case-SENSITIVE: strip whitespace only, never change case.
    dec = b64_decode(re.sub(r"\s+", "", sub or ""))
    if dec is None:
        return False, ""
    return norm_loose(dec) == norm_loose("HackQuest"), "HackQuest"


@validator("hq_r2_c6")
def v_r2_c6(sub: str):
    s = norm_upper_strip(sub)
    plain = rot13(s[::-1])
    return norm_upper_strip(plain) == "SNO", "SNO"


@validator("hq_r3_c7")
def v_r3_c7(sub: str):
    n = norm_int(sub)
    return n == 48, "48"


@validator("hq_r3_c8")
def v_r3_c8(sub: str):
    return norm_loose(sub) == "STACK", "STACK"


@validator("hq_r3_c9")
def v_r3_c9(sub: str):
    n = norm_int(sub)
    return n == 443, "443"


@validator("hq_r3_c10")
def v_r3_c10(sub: str):
    # The question asks for the DECIMAL value of 101101, so an integer is expected.
    s = norm_upper_strip(sub)
    # Accept a binary-form submission too, since some teams submit the source form.
    if len(s) == 6 and all(c in "01" for c in s):
        return int(s, 2) == 45, "45"
    n = norm_int(sub)
    if n is None:
        return False, ""
    return n == 45, "45"


@validator("hq_r4_c11")
def v_r4_c11(sub: str):
    s = (sub or "").strip()
    return s == "/training/blue-door", "/training/blue-door"


@validator("hq_r4_c12")
def v_r4_c12(sub: str):
    s = norm_loose(sub)
    return s == norm_loose("trainee:demo-pass"), "trainee:demo-pass"


@validator("hq_r4_c13")
def v_r4_c13(sub: str):
    return norm_loose(sub) == norm_loose("SHA-256"), "SHA-256"


@validator("hq_r4_c14")
def v_r4_c14(sub: str):
    return norm_loose(sub) == "CAESAR", "CAESAR"


def validate(key: str, submission: str) -> tuple[bool, str]:
    fn = VALIDATORS.get(key)
    if not fn:
        return False, ""
    try:
        return fn(submission or "")
    except Exception:
        return False, ""