"""Local administration CLI: seed data and issue organiser credentials."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db import init_db  # noqa: E402
from app.seed import bootstrap_organizers, run  # noqa: E402
from app.security import new_temp_password  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="HACKQUEST CTF 2026 admin CLI")
    parser.add_argument("command", choices=["seed", "organizers"])
    args = parser.parse_args()
    init_db()
    if args.command == "seed":
        result = run(refresh=True)
        print("Database seeded: 4 rounds, 48 challenges, 20 riddles, memes and settings.")
        if result["issued_passwords"]:
            print("\nTEMPORARY ORGANISER PASSWORDS (change at first login):")
            for user, pw in result["issued_passwords"].items():
                print(f"  {user}: {pw}")
    else:
        from app.db import SessionLocal
        db = SessionLocal()
        passwords = {
            "pragyan_lead": new_temp_password(),
            "ieee_lead": new_temp_password(),
        }
        issued = bootstrap_organizers(db, passwords)
        db.commit()
        db.close()
        print("TEMPORARY ORGANISER PASSWORDS (single-use handover):")
        for user, pw in issued.items():
            print(f"  {user}: {pw}")
        print("\nAccounts already existing keep their current password; reset them from the dashboard.")


if __name__ == "__main__":
    main()
