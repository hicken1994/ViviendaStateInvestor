"""Bootstrap: recreate real_estate.db from compressed seed on fresh deploys."""

import gzip
import logging
import os
import shutil
import sqlite3

logger = logging.getLogger(__name__)

SEED_PATH = os.path.join(os.path.dirname(__file__), "_seed.db.gz")
DB_PATH = "real_estate.db"


def needs_bootstrap() -> bool:
    if not os.path.isfile(DB_PATH):
        return True
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()
        conn.close()
        return row is None or row[0] == 0
    except Exception:
        return True


def bootstrap():
    if not os.path.isfile(SEED_PATH):
        logger.warning("Seed file %s not found — skipping bootstrap", SEED_PATH)
        return
    if not needs_bootstrap():
        return

    logger.info("Bootstrapping database from seed…")
    try:
        with gzip.open(SEED_PATH, "rb") as f_in:
            with open(DB_PATH, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info("Database restored from seed (%d bytes)", os.path.getsize(DB_PATH))
    except Exception as e:
        logger.error("Bootstrap failed: %s", e)
        raise
