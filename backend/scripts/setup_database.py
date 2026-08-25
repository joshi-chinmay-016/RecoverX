"""Database Setup Script for RecoverX

Ensures the database exists, runs Alembic migrations, and seeds demo data.
"""

import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
from alembic.config import Config
from alembic import command

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.core.config import settings

def ensure_database():
    """Ensure the target database exists in PostgreSQL."""
    parsed = urlparse(settings.database_url)
    db_name = parsed.path.lstrip('/') or 'recoverx'
    user = parsed.username or 'postgres'
    password = parsed.password or ''
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432

    print(f"Connecting to PostgreSQL server at {host}:{port} as user '{user}'...")
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()

        if not exists:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✓ Database '{db_name}' created successfully.")
        else:
            print(f"✓ Database '{db_name}' already exists.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error ensuring database exists: {e}")

def run_migrations():
    """Run all alembic migrations up to head."""
    alembic_cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    cfg = Config(alembic_cfg_path)
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    print("Applying Alembic migrations...")
    command.upgrade(cfg, "head")
    print("✓ All migrations successfully applied.")

if __name__ == '__main__':
    ensure_database()
    run_migrations()
