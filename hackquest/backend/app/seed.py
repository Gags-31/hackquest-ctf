"""Seed the 15 challenges, 5 rounds and private answer keys.

Answer keys are verified by backend/tests/test_answer_keys.py.
"""
import string

from .db import SessionLocal, init_db
from .models import Challenge, Round, RoundState, ScoringMode, AppSetting
from .scoring import TIER_POINTS, CHALLENGES_PER_ROUND
from .sandbox import challenge_segment

ROUNDS = [
    (1, "round1", "Logic Labyrinth",
     "Three computational puzzles. Every answer is expressed in base-36."),
    (2, "round2", "Cipher Vault",
     "Three classical ciphers: Caesar, Base64 and a reversed ROT13."),
    (3, "round3", "Tech Riddles",
     "Four riddles spanning mathematics, data structures and networking."),
    (4, "round4", "Capture The Flag",
     "Four web-security questions inside a self-contained fictional training lab."),
    (5, "final", "The Debug Sprint",
     "Repair a broken Python function so every test passes."),
]

# key, round, order, title, category, difficulty, description, answer_format,
# clue, h1, h2, h3, answer, segment, explanation
CHALLENGES = [
    ("hq_r1_c1", 1, 1, "Arithmetic Accumulator", "Mathematics", "Easy",
     "Calculate the sum of all integers from 1 through 75. Submit the result in base 36 using uppercase digits 0-9 and A-Z.",
     "Uppercase base-36 string, e.g. 276",
     "The series formula saves you a long loop.",
     "Use the arithmetic-series formula: sum = n x (n + 1) / 2.",
     "First calculate the decimal sum. Then repeatedly divide by 36 and collect the remainders from last to first.",
     "A base-36 answer uses digits 0-9 followed by letters A-Z.",
     "2850", "276",
     "n(n+1)/2 with n=75 gives 75 x 76 / 2 = 2850. Converting 2850 to base 36: 2850 / 1296 = 2 (remainder 258); 258 / 36 = 7 (remainder 6). So the digits are 2, 7, 6 -> 276."),

    ("hq_r1_c2", 1, 2, "Fibonacci Signal", "Algorithms", "Easy",
     "Calculate Fibonacci term F(12), where F(0) = 0, F(1) = 1 and each subsequent term is the sum of the previous two. Submit the answer in base 36.",
     "Uppercase base-36 string",
     "Index carefully: the sequence starts at F(0) = 0, not F(1) = 0.",
     "Write down the first two terms before calculating further.",
     "Each new term is the sum of the previous two; use a table to avoid skipping a term.",
     "Convert the final decimal value to base 36 using repeated division.",
     "144", "40",
     "The sequence is 0,1,1,2,3,5,8,13,21,34,55,89,144. F(12) = 144. In base 36, 144 = 4 x 36, giving the two digits 4, 0 -> 40."),

    ("hq_r1_c3", 1, 3, "Exponent Engine", "Mathematics", "Easy",
     "Calculate 7^4 and submit the result in base 36.",
     "Uppercase base-36 string",
     "Exponentiation is repeated multiplication.",
     "Exponentiation means repeated multiplication, not multiplication by the exponent.",
     "Calculate 7 x 7 x 7 x 7.",
     "Convert the decimal result to base 36.",
     "2401", "1UP",
     "7^4 = 2401. In base 36: 2401 / 1296 = 1 (remainder 1105); 1105 / 36 = 30 (remainder 25). The digit 30 is 'U' and 25 is 'P', giving 1UP."),

    ("hq_r2_c4", 2, 1, "Caesar Lock", "Classical Cryptography", "Medium",
     "Decode KDFN using a Caesar cipher with an encryption shift of +3.",
     "Uppercase plaintext",
     "Encryption moves letters forward, so decryption moves them backward.",
     "Encryption moves each letter forward.",
     "Decryption moves each letter backward.",
     "Shift each letter three positions backward, wrapping around the alphabet if necessary.",
     "HACK", "HACK",
     "Subtracting 3 from each letter: K->H, D->A, F->C, N->K, giving HACK."),

    ("hq_r2_c5", 2, 2, "Encoded Transmission", "Encoding", "Medium",
     "Decode the Base64 string SGFja1F1ZXN0.",
     "The decoded plaintext text",
     "Base64 is an encoding scheme, not encryption.",
     "Base64 encodes bytes using a 64-character alphabet.",
     "It is an encoding scheme, not encryption.",
     "Use a standard Base64 decoder and interpret the resulting bytes as UTF-8.",
     "HackQuest", "HackQuest",
     "Decoding SGFja1F1ZXN0 yields the ASCII text 'HackQuest'. Note that Base64 provides no confidentiality."),

    ("hq_r2_c6", 2, 3, "Reversed Signal", "Classical Cryptography", "Medium",
     "Decode BAF by reversing the string first and then applying ROT13.",
     "Uppercase plaintext",
     "The order of operations matters here.",
     "Reverse the character order before applying ROT13.",
     "ROT13 shifts letters by 13 positions.",
     "Apply the two transformations in the specified order.",
     "SNO", "SNO",
     "Reversing BAF gives FAB. ROT13 then maps F->S, A->N, B->O, giving SNO. This round mixes three distinct ideas: substitution (Caesar/ROT13), reordering (reversal) and encoding (Base64)."),

    ("hq_r3_c7", 3, 1, "The Missing Number", "Mathematics", "Medium",
     "A sequence follows a consistent pattern: 3, 8, 15, 24, 35, ? Find the next number.",
     "An integer",
     "Look at the gaps, not the terms.",
     "Calculate the differences between adjacent terms.",
     "Examine whether the differences themselves form a pattern.",
     "Compare the sequence with products of consecutive integers.",
     "48", "48",
     "The terms are n^2 + 2n = n(n+2): 3, 8, 15, 24, 35. The next is 6 x 8 = 48. The successive differences (5, 7, 9, 11) grow by 2 each time."),

    ("hq_r3_c8", 3, 2, "The Memory Keeper", "Data Structures", "Medium",
     "Which data structure follows Last In, First Out (LIFO)?",
     "A single word",
     "Think of a stack of plates.",
     "Think about a stack of plates.",
     "The last item added is the first one removed.",
     "Choose between common data structures such as stack, queue, tree and graph.",
     "STACK", "STACK",
     "A stack is last-in first-out. A queue is first-in first-out, which is the opposite."),

    ("hq_r3_c9", 3, 3, "Port Detective", "Networking", "Medium",
     "Which standard TCP port is commonly used by HTTPS?",
     "A three-digit port number",
     "Recall the default transport-layer port assigned to HTTPS.",
     "HTTPS is the secure form of HTTP.",
     "Recall the default transport-layer port assigned to HTTPS.",
     "The expected answer is a three-digit port number.",
     "443", "443",
     "HTTPS uses TCP port 443 by default; HTTP uses port 80."),

    ("hq_r3_c10", 3, 4, "Binary Whisper", "Number Systems", "Medium",
     "Convert binary 101101 into decimal.",
     "An integer",
     "The rightmost bit has weight 2^0.",
     "Start with the rightmost bit at position zero.",
     "Each bit contributes its value multiplied by a power of two.",
     "Add the contributions of all bits set to 1.",
     "45", "45",
     "1x32 + 0x16 + 1x8 + 1x4 + 0x2 + 1x1 = 32 + 8 + 4 + 1 = 45."),

    ("hq_r4_c11", 4, 1, "Hidden Configuration", "Information Disclosure", "Hard",
     "Inspect this fictional training configuration snippet:\n\nPUBLIC_PATH=/training/blue-door\nAPP_MODE=demo\nDEBUG=false\n\nWhat is the disclosed training path?",
     "The exact value of PUBLIC_PATH",
     "Look for the variable whose name suggests a URL path.",
     "Look for a variable whose name suggests a URL path.",
     "Distinguish paths from application settings.",
     "Submit the value of PUBLIC_PATH exactly.",
     "/training/blue-door", "/training/blue-door",
     "Real applications leak exactly this kind of information through debug endpoints, config files and error pages. This snippet is fictional training material."),

    ("hq_r4_c12", 4, 2, "Login Logic", "Authentication Logic", "Hard",
     "Review this fictional training pseudocode:\n\nif username == \"trainee\" AND token == \"demo-pass\": grant_demo_access\n\nWhich username and token pair satisfies the condition?",
     "username:token",
     "Both comparisons must hold because the operator is AND.",
     "Both comparisons must be true because the operator is AND.",
     "Read the quoted strings literally.",
     "Submit the username and token in the documented format.",
     "trainee:demo-pass", "trainee:demo-pass",
     "Because the operator is AND, both quoted values must match exactly. This is a toy logic exercise; real authentication bypass exploits and hard-coded secrets are outside the scope of this training round."),

    ("hq_r4_c13", 4, 3, "Hash Hunter", "Cryptography", "Hard",
     "Which cryptographic hash family produces a 256-bit digest and belongs to the SHA-2 family?",
     "Name and output length, e.g. SHA-256",
     "The output length is the giveaway.",
     "It belongs to the Secure Hash Algorithm family.",
     "Its output length is 256 bits.",
     "Its standard name includes the family name and output length.",
     "SHA-256", "SHA-256",
     "SHA-256 is the SHA-2 family member with a 256-bit digest. MD5 is 128 bits and is not considered collision resistant."),

    ("hq_r4_c14", 4, 4, "Rotation Station", "Classical Cryptography", "Hard",
     "Which classical substitution cipher rotates each letter by a fixed number of positions in the alphabet?",
     "A single word",
     "The alphabet wraps around at the end.",
     "Each letter is shifted by a constant amount.",
     "The alphabet wraps around at its end.",
     "It is named after a Roman leader.",
     "CAESAR", "CAESAR",
     "The Caesar cipher is named after Julius Caesar and shifts every letter by a fixed amount. This round uses a fictional training lab only; no real systems were targeted."),
]

R5_CHALLENGE = {
    "key": "hq_r5_c15", "round": 5, "order": 1,
    "title": "Broken Counter", "category": "Debugging", "difficulty": "Hard",
    "description": (
        "This function is supposed to count the even integers in a list, but it counts odds.\n\n"
        "```python\n"
        "def count_evens(numbers):\n"
        "    count = 0\n"
        "    for n in numbers:\n"
        "        if n % 2 == 1:\n"
        "            count += 1\n"
        "    return count\n"
        "```\n\n"
        "Required tests:\n\n"
        "```python\n"
        "assert count_evens([]) == 0\n"
        "assert count_evens([1, 3, 5]) == 0\n"
        "assert count_evens([2, 4, 6]) == 3\n"
        "assert count_evens([0, 1, 2]) == 2\n"
        "assert count_evens([-2, -1, 0, 3, 4]) == 3\n"
        "```\n\n"
        "**Submission options (choose one)**\n\n"
        "1. *Structured fix* - declare the fix as JSON, e.g. "
        "`{\"comparator\": 0}` or `{\"divisor\": 2, \"remainder\": 0}`. "
        "This is evaluated safely by the server and is the recommended path.\n"
        "2. *Pasted code* - paste the corrected function. Your code is parsed and "
        "analysed but never executed on the competition server."
    ),
    "answer_format": 'JSON such as {"comparator": 0}, or your corrected function',
    "initial_clue": "The function is testing for the wrong parity.",
    "hint1": "Check the meaning of the remainder operator %.",
    "hint2": "An integer is even when its remainder after division by two is zero.",
    "hint3": "Examine the condition inside the if statement.",
    "answer": '{"comparator": 0}',
    "segment": challenge_segment(),
    "explanation": ("The remainder operator % yields the remainder of division. An integer n is even "
                    "when n % 2 == 0, so the condition must compare against 0 rather than 1. "
                    "Zero counts as even (0 % 2 == 0) and negative even integers behave correctly "
                    "under the same rule."),
}

# A canonical, valid submission for each challenge.
#
# This is NOT the answer key - it is the exact text a participant types. For the
# base-36 challenges the typed value is the base-36 segment, not the decimal
# result; for the Base64 challenge the typed value is the encoded string, not the
# decoded word; for the cipher challenges it is the ciphertext. Verification
# tooling must use these rather than the stored keys.
SAMPLE_SUBMISSIONS = {
    "hq_r1_c1": "276",
    "hq_r1_c2": "40",
    "hq_r1_c3": "1UP",
    "hq_r2_c4": "HACK",
    "hq_r2_c5": "SGFja1F1ZXN0",
    "hq_r2_c6": "BAF",
    "hq_r3_c7": "48",
    "hq_r3_c8": "STACK",
    "hq_r3_c9": "443",
    "hq_r3_c10": "101101",
    "hq_r4_c11": "/training/blue-door",
    "hq_r4_c12": "trainee:demo-pass",
    "hq_r4_c13": "SHA-256",
    "hq_r4_c14": "CAESAR",
    "hq_r5_c15": '{"comparator": 0}',
}


def run() -> dict:
    init_db()
    db = SessionLocal()
    created = {"rounds": 0, "challenges": 0}

    for num, slug, name, blurb in ROUNDS:
        rd = db.query(Round).filter_by(number=num).first()
        if not rd:
            rd = Round(number=num, slug=slug, name=name, blurb=blurb,
                       state=RoundState.LOCKED, unlock_code="")
            db.add(rd)
            created["rounds"] += 1
        db.flush()

    for c in CHALLENGES:
        key, rnd, order, title, cat, diff, desc, fmt, clue, h1, h2, h3, ans, seg, expl = c
        if db.query(Challenge).filter_by(key=key).first():
            continue
        rd = db.query(Round).filter_by(number=rnd).one()
        db.add(Challenge(
            round_id=rd.id, key=key, order_index=order, title=title,
            category=cat, difficulty=diff, description=desc,
            answer_format=fmt, initial_clue=clue,
            hint1=h1, hint2=h2, hint3=h3,
            answer_key=ans, segment=seg, explanation=expl,
            is_code_challenge=False,
        ))
        created["challenges"] += 1

    if not db.query(Challenge).filter_by(key=R5_CHALLENGE["key"]).first():
        rd = db.query(Round).filter_by(number=5).one()
        db.add(Challenge(
            round_id=rd.id, key=R5_CHALLENGE["key"], order_index=1,
            title=R5_CHALLENGE["title"], category=R5_CHALLENGE["category"],
            difficulty=R5_CHALLENGE["difficulty"], description=R5_CHALLENGE["description"],
            answer_format=R5_CHALLENGE["answer_format"],
            initial_clue=R5_CHALLENGE["initial_clue"],
            hint1=R5_CHALLENGE["hint1"], hint2=R5_CHALLENGE["hint2"],
            hint3=R5_CHALLENGE["hint3"],
            answer_key=R5_CHALLENGE["answer"], segment=R5_CHALLENGE["segment"],
            explanation=R5_CHALLENGE["explanation"],
            is_code_challenge=True,
            hidden_tests="server-only",
        ))
        created["challenges"] += 1

    # Server-generated unlock codes: concatenation of segments in defined order.
    db.flush()  # ensure every challenge is visible on the relationship before assembling
    db.expire_all()  # drop stale identity-map caches on Round.challenges
    for rd in db.query(Round).order_by(Round.number).all():
        segs = [ch.segment for ch in sorted(rd.challenges, key=lambda c: c.order_index)]
        rd.unlock_code = "".join(segs)

    for key, val in [
        ("scoring_mode", ScoringMode.TIER.value),
        ("hint_penalty", "0"),
        ("registration_open", "1"),
        ("competition_state", "pending"),
        ("event_datetime", ""),
        ("event_timezone", "Asia/Kolkata"),
        ("results_frozen", "0"),
        ("results_published", "0"),
    ]:
        if not db.query(AppSetting).filter_by(key=key).first():
            db.add(AppSetting(key=key, value=val))

    db.commit()
    db.close()
    return created


if __name__ == "__main__":
    print(run())