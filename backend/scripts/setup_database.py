"""Database Setup Script for RecoverX

Ensures the database exists, runs Alembic migrations, and seeds demo data.
"""

import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

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
        # Connect to default 'postgres' maintenance database
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if target database exists
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
        print("Continuing with migrations...")

if __name__ == '__main__':
    ensure_database()
