"""Delete the local database and stored files, then re-seed. Demo/dev only."""
from __future__ import annotations

import shutil

from app.core.config import Settings


def main() -> None:
    s = Settings.from_env()
    if s.app_env == "prod":
        raise SystemExit("Refusing to reset in production.")
    for suffix in ("", "-wal", "-shm"):
        p = s.database_path.with_name(s.database_path.name + suffix)
        if p.exists():
            p.unlink()
    shutil.rmtree(s.storage_path, ignore_errors=True)
    print("Local data removed.")
    from scripts.seed import main as seed

    seed()


if __name__ == "__main__":
    main()
