from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# v2.8.9 — Optimisation connection pool pour Neon PostgreSQL
# Neon serverless a des latences variables (cold start ~800ms).
# On garde un pool de 5 connexions + 5 overflow pour éviter de
# rouvrir des connexions à chaque requête.
engine_kwargs = {
    "pool_pre_ping": True,  # vérifie que la connexion est alive avant usage
    "pool_size": 5,         # 5 connexions persistantes
    "max_overflow": 5,      # +5 connexions temporaires sous charge
    "pool_recycle": 1800,   # recycle les connexions après 30 min (Neon timeout)
    "pool_timeout": 10,     # attend max 10s pour obtenir une connexion
}

if settings.database_url.startswith("sqlite"):
    # SQLite : pas de pool (StaticPool = 1 connexion partagée)
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
