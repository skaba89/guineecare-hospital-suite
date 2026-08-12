from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.tenant import apply_tenant_context_after_begin, clear_tenant_context

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

# PostgreSQL set_config(..., true) is transaction-local. Routes frequently call
# db.commit(), so the trusted tenant context must be reinstalled every time the
# Session opens a new database transaction. The listener is harmless on SQLite.
event.listen(SessionLocal.class_, "after_begin", apply_tenant_context_after_begin)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # Session objects are normally short-lived, but explicitly clearing the
        # in-memory context makes accidental Session reuse fail closed as well.
        clear_tenant_context(db)
        db.close()
