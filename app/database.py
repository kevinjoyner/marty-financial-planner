import os
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import declarative_base, sessionmaker

# Use env var for DB location, default to local (Dev-friendly)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./marty.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# --- Enable Foreign Key Support for SQLite ---
def _fk_pragma_on_connect(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')

listen(engine, 'connect', _fk_pragma_on_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
