import os
import sys
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

if getattr(sys, 'frozen', False):
    USER_DATA_DIR = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), 
        "SistemaHOLASA"
    )
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    USER_DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(USER_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(USER_DATA_DIR, "HOLASA-DB.sqlite3")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()