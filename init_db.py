#!/usr/bin/env python3
"""Database initialization script for Error Analyzer PoC"""

from app.database.connection import engine
from app.database.models import init_db

if __name__ == "__main__":
    print("Initializing Error Analyzer database...")
    init_db(engine)
    print("✅ Database initialized successfully!")
    print("You can now run: python run.py")