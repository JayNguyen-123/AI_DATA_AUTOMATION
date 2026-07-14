from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
#from app.config import settings

# Engine setup optimizer for high-concurrency connection workloads
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,          # Keeps 20 permanent sockets open
    max_overflow=10,       # ALLOWS spikes up to 30 parallel requests
    pool_pre_ping=True,    # Guard against dead/stale DB connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
  """Dependency injector providing session isolation per web request."""
  db = SessionLocal()

  try:
    yield db
  finally:
    db.close()
