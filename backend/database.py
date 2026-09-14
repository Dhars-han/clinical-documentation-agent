import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Support DATABASE_URL for hosted Postgres (e.g. Neon, Supabase)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # SQLAlchemy requires postgresql:// instead of legacy postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # On Vercel / AWS Lambda, the root deployment directory (/var/task) is read-only.
    # SQLite requires write access for locking and WAL/journal files.
    # We copy the database to /tmp where SQLite has full read/write permissions.
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        import shutil
        tmp_db = "/tmp/clinical.db"
        bundled_db = os.path.join(PROJECT_ROOT, "clinical.db")
        if not os.path.exists(tmp_db) and os.path.exists(bundled_db):
            try:
                shutil.copy2(bundled_db, tmp_db)
            except Exception as e:
                print(f"Warning: Failed to copy {bundled_db} to {tmp_db}: {e}")
        DB_PATH = tmp_db
    else:
        DB_PATH = os.path.join(PROJECT_ROOT, "clinical.db")

    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()