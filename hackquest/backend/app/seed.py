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
     "Use the arithmetic-series formula: sum = n x (n + 1) / 2 with n = 75. No long addition is needed.",
     "Convert the decimal total to base 36 by repeatedly dividing by 36 and reading the remainders from last to first. The total is under 3000, so expect three base-36 digits.",
     "The three base-36 digits are 2, then 7, then 6. Type them together as one string with no spaces.",
     "2850", "276",
     "n(n+1)/2 with n=75 gives 75 x 76 / 2 = 2850. Converting 2850 to base 36: 2850 / 1296 = 2 (remainder 258); 258 / 36 = 7 (remainder 6). So the digits are 2, 7, 6 -> 276."),

    ("hq_r1_c2", 1, 2, "Fibonacci Signal", "Algorithms", "Easy",
     "Calculate Fibonacci term F(12), where F(0) = 0, F(1) = 1 and each subsequent term is the sum of the previous two. Submit the answer in base 36.",
     "Uppercase base-36 string",
     "Index carefully: the sequence starts at F(0) = 0, not F(1) = 0.",
     "Start at F(0) = 0 and F(1) = 1, then keep adding the previous two terms until you reach index 12.",
     "The terms run 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55 ... you need just one more term.",
     "That next term is one hundred and forty-four. Divide it by 36: quotient 4, remainder 0. Those two values are the base-36 digits, in that order.",
     "144", "40",
     "The sequence is 0,1,1,2,3,5,8,13,21,34,55,89,144. F(12) = 144. In base 36, 144 = 4 x 36, giving the two digits 4, 0 -> 40."),

    ("hq_r1_c3", 1, 3, "Exponent Engine", "Mathematics", "Easy",
     "Calculate 7^4 and submit the result in base 36.",
     "Uppercase base-36 string",
     "Exponentiation is repeated multiplication.",
     "7^4 means 7 x 7 x 7 x 7. Multiply in stages: first 49, then multiply by 7 twice more.",
     "The decimal result is a little over 2400. Divide it by 1296 for the first base-36 digit; the remainder is 1105.",
     "1105 = 30 x 36 + 25. In base 36, digit 30 is the letter U and digit 25 is P. Put the leading 1 in front of them.",
     "2401", "1UP",
     "7^4 = 2401. In base 36: 2401 / 1296 = 1 (remainder 1105); 1105 / 36 = 30 (remainder 25). The digit 30 is 'U' and 25 is 'P', giving 1UP."),

    ("hq_r2_c4", 2, 1, "Caesar Lock", "Classical Cryptography", "Medium",
     "Decode KDFN using a Caesar cipher with an encryption shift of +3.",
     "Uppercase plaintext",
     "Encryption moves letters forward, so decryption moves them backward.",
     "Encryption moved letters forward by 3, so to decode, move each letter backward by 3.",
     "Do it one letter at a time: K becomes H, D becomes A, F becomes C, N becomes K.",
     "Read the four results in the original order. Together they spell a four-letter word for breaking into a system.",
     "HACK", "HACK",
     "Subtracting 3 from each letter: K->H, D->A, F->C, N->K, giving HACK."),

    ("hq_r2_c5", 2, 2, "Encoded Transmission", "Encoding", "Medium",
     "Decode the Base64 string SGFja1F1ZXN0.",
     "The decoded plaintext text",
     "Base64 is an encoding scheme, not encryption.",
     "Base64 is an encoding, not encryption - no key or password is needed.",
     "Feed the string to any standard Base64 decoder and read the resulting bytes as UTF-8 text.",
     "The decoded text is this event's own name written as two joined words: 'Hack' + 'Quest', with the capital Q.",
     "HackQuest", "HackQuest",
     "Decoding SGFja1F1ZXN0 yields the ASCII text 'HackQuest'. Note that Base64 provides no confidentiality."),

    ("hq_r2_c6", 2, 3, "Reversed Signal", "Classical Cryptography", "Medium",
     "Decode BAF by reversing the string first and then applying ROT13.",
     "Uppercase plaintext",
     "The order of operations matters here.",
     "Follow the order stated in the question: reverse first, ROT13 second. Swapping them gives a different result.",
     "BAF reversed is FAB. ROT13 swaps A with N, B with O and F with S.",
     "Apply those three swaps to F, A and B in that order, then write the three letters together.",
     "SNO", "SNO",
     "Reversing BAF gives FAB. ROT13 then maps F->S, A->N, B->O, giving SNO. This round mixes three distinct ideas: substitution (Caesar/ROT13), reordering (reversal) and encoding (Base64)."),

    ("hq_r3_c7", 3, 1, "The Missing Number", "Mathematics", "Medium",
     "A sequence follows a consistent pattern: 3, 8, 15, 24, 35, ? Find the next number.",
     "An integer",
     "Look at the gaps, not the terms.",
     "Look at the gaps between adjacent terms: 8-3=5, 15-8=7, 24-15=9, 35-24=11.",
     "The gaps go up by 2 each time, so the next gap is 13. Add that gap to the last term, 35.",
     "Equivalently the terms are n x (n+2): 1x3, 2x4, 3x5, 4x6, 5x7 ... continue with 6x8.",
     "48", "48",
     "The terms are n^2 + 2n = n(n+2): 3, 8, 15, 24, 35. The next is 6 x 8 = 48. The successive differences (5, 7, 9, 11) grow by 2 each time."),

    ("hq_r3_c8", 3, 2, "The Memory Keeper", "Data Structures", "Medium",
     "Which data structure follows Last In, First Out (LIFO)?",
     "A single word",
     "Think of a stack of plates.",
     "LIFO means the newest item is removed first. Which everyday structure works that way?",
     "Picture a pile of plates: the last plate you put on top is the first one you take off.",
     "A queue is FIFO, the opposite. The answer is the five-letter name of the plate-pile structure.",
     "STACK", "STACK",
     "A stack is last-in first-out. A queue is first-in first-out, which is the opposite."),

    ("hq_r3_c9", 3, 3, "Port Detective", "Networking", "Medium",
     "Which standard TCP port is commonly used by HTTPS?",
     "A three-digit port number",
     "Recall the default transport-layer port assigned to HTTPS.",
     "Plain HTTP uses port 80. The secure version uses another well-known port.",
     "It is the standard TLS port for web traffic and it sits in the 400s.",
     "It is the HTTPS default, written as three digits: 4, 4, 3.",
     "443", "443",
     "HTTPS uses TCP port 443 by default; HTTP uses port 80."),

    ("hq_r3_c10", 3, 4, "Binary Whisper", "Number Systems", "Medium",
     "Convert binary 101101 into decimal.",
     "An integer",
     "The rightmost bit has weight 2^0.",
     "Write the place values under the bits, starting at the right: 1, 2, 4, 8, 16, 32.",
     "Only bits equal to 1 count. In 101101 the leftmost bit, the 8-bit, the 4-bit and the rightmost bit are set.",
     "Add 32 + 8 + 4 + 1 to get the decimal value.",
     "45", "45",
     "1x32 + 0x16 + 1x8 + 1x4 + 0x2 + 1x1 = 32 + 8 + 4 + 1 = 45."),

    ("hq_r4_c11", 4, 1, "Hidden Configuration", "Information Disclosure", "Hard",
     "Inspect this fictional training configuration snippet:\n\nPUBLIC_PATH=/training/blue-door\nAPP_MODE=demo\nDEBUG=false\n\nWhat is the disclosed training path?",
     "The exact value of PUBLIC_PATH",
     "Look for the variable whose name suggests a URL path.",
     "Each line is a KEY=VALUE pair. The question asks for a value, not a variable name.",
     "APP_MODE and DEBUG are settings; only one key names a path.",
     "Copy everything after the equals sign on the PUBLIC_PATH line, including the leading slash and the hyphen.",
     "/training/blue-door", "/training/blue-door",
     "Real applications leak exactly this kind of information through debug endpoints, config files and error pages. This snippet is fictional training material."),

    ("hq_r4_c12", 4, 2, "Login Logic", "Authentication Logic", "Hard",
     "Review this fictional training pseudocode:\n\nif username == \"trainee\" AND token == \"demo-pass\": grant_demo_access\n\nWhich username and token pair satisfies the condition?",
     "username:token",
     "Both comparisons must hold because the operator is AND.",
     "The operator is AND, so both comparisons must be true at the same time.",
     "Take the username from the first quoted string and the token from the second quoted string.",
     "Join them with a colon, username first and token second, exactly as the answer format describes.",
     "trainee:demo-pass", "trainee:demo-pass",
     "Because the operator is AND, both quoted values must match exactly. This is a toy logic exercise; real authentication bypass exploits and hard-coded secrets are outside the scope of this training round."),

    ("hq_r4_c13", 4, 3, "Hash Hunter", "Cryptography", "Hard",
     "Which cryptographic hash family produces a 256-bit digest and belongs to the SHA-2 family?",
     "Name and output length, e.g. SHA-256",
     "The output length is the giveaway.",
     "The family is SHA, the Secure Hash Algorithm. The digest length is in the name.",
     "MD5 produces 128 bits and SHA-1 produces 160 bits. You want the SHA-2 member with a 256-bit digest.",
     "Write the family name, then a hyphen, then 256.",
     "SHA-256", "SHA-256",
     "SHA-256 is the SHA-2 family member with a 256-bit digest. MD5 is 128 bits and is not considered collision resistant."),

    ("hq_r4_c14", 4, 4, "Rotation Station", "Classical Cryptography", "Hard",
     "Which classical substitution cipher rotates each letter by a fixed number of positions in the alphabet?",
     "A single word",
     "The alphabet wraps around at the end.",
     "Every letter is shifted by the same amount and the alphabet wraps around at Z.",
     "It is the earliest known substitution cipher, named after a Roman general.",
     "Six letters, beginning with C and ending with R.",
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
    "hint1": "The loop tests n % 2 == 1, which counts odd numbers. You need to count even numbers instead.",
    "hint2": "An even number leaves remainder 0 when divided by 2, so change the value the remainder is compared against.",
    "hint3": "For the JSON option put 0 in the comparator field: { \"comparator\": <zero> }. For pasted code, the condition becomes n % 2 == 0.",
    "answer": '{"comparator": 0}',
    "segment": challenge_segment(),
    "explanation": ("The remainder operator % yields the remainder of division. An integer n is even "
                    "when n % 2 == 0, so the condition must compare against 0 rather than 1. "
                    "Zero counts as even (0 % 2 == 0) and negative even integers behave correctly "
                    "under the same rule."),
}

def hint_updates() -> dict:
    """Canonical (clue, hint1, hint2, hint3) for all 15 challenges.

    This is the single source of truth used both when seeding a fresh database
    and when refreshing hint text in a database that already has challenges.
    """
    out = {c[0]: (c[8], c[9], c[10], c[11]) for c in CHALLENGES}
    out[R5_CHALLENGE["key"]] = (
        R5_CHALLENGE["initial_clue"],
        R5_CHALLENGE["hint1"],
        R5_CHALLENGE["hint2"],
        R5_CHALLENGE["hint3"],
    )
    return out


def refresh_hints(db=None) -> int:
    """Update clue/hint text on existing challenges.

    Deliberately touches ONLY the four participant-facing explanatory fields.
    Answer keys, segments, unlock codes, round state, scores and submissions
    are never modified, so this is safe to run against a live event database.

    Returns the number of challenge rows whose hint text changed.
    """
    owns_session = db is None
    db = db or SessionLocal()
    changed = 0
    try:
        for key, (clue, h1, h2, h3) in hint_updates().items():
            ch = db.query(Challenge).filter_by(key=key).first()
            if ch is None:
                continue
            if (ch.initial_clue, ch.hint1, ch.hint2, ch.hint3) != (clue, h1, h2, h3):
                ch.initial_clue, ch.hint1, ch.hint2, ch.hint3 = clue, h1, h2, h3
                changed += 1
        if changed:
            db.commit()
    finally:
        if owns_session:
            db.close()
    return changed


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

    # Carry the new beginner-friendly hint text into a database that already
    # has challenges. Safe on a live event: no answer keys, scores or state.
    created["hints_updated"] = refresh_hints(db)

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