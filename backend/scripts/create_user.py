"""CLI utility to create an initial user securely in production or staging.

Run: python -m scripts.create_user --email admin@agency.gov.in --name "Administrator" --role admin
"""
from __future__ import annotations

import argparse
import getpass
import sys

from app.container import build_services
from app.core.config import Settings
from app.core.db import new_id, utcnow
from app.core.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new VeriScope user securely.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--name", required=True, help="User full name")
    parser.add_argument("--role", choices=["applicant", "reviewer", "admin"], required=True, help="User role")
    args = parser.parse_args()

    password = getpass.getpass("Password (min 12 chars): ")
    if len(password) < 12:
        print("Error: Password must be at least 12 characters.", file=sys.stderr)
        sys.exit(1)

    svc = build_services(Settings.from_env())
    existing = svc.db.one("SELECT id FROM users WHERE email = ?", (args.email.lower().strip(),))
    if existing:
        print(f"Error: User with email '{args.email}' already exists.", file=sys.stderr)
        sys.exit(1)

    user_id = new_id()
    svc.db.insert(
        "users",
        {
            "id": user_id,
            "email": args.email.lower().strip(),
            "name": args.name.strip(),
            "role": args.role,
            "password_hash": hash_password(password),
            "created_at": utcnow(),
        },
    )
    print(f"User '{args.email}' ({args.role}) successfully created with ID {user_id}.")


if __name__ == "__main__":
    main()
