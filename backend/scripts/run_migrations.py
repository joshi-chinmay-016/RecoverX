"""Programmatic database migration runner for Phase 4."""

import os
import sys
from alembic.config import Config
from alembic import command

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.core.config import settings

def run_migrations():
    alembic_cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    cfg = Config(alembic_cfg_path)
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    print("Running Alembic upgrade head...")
    command.upgrade(cfg, "head")
    print("✓ All migrations successfully applied to head.")

if __name__ == "__main__":
    run_migrations()
