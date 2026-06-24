"""Script de migration manuelle — ajoute les colonnes manquantes aux tables existantes.

Utilisé par render_start.sh après alembic stamp head, car stamp head marque
les migrations comme appliquées sans exécuter le SQL. Les colonnes ajoutées
par les migrations (ex: blood_type sur patients) doivent être créées manuellement.

Ce script est idempotent — il vérifie si la colonne existe avant de l'ajouter.
"""
import logging
from sqlalchemy import inspect, text
from app.db.session import engine

logger = logging.getLogger("guineecare.migration_helper")

# Colonnes à ajouter : (table, column, SQL type, default)
MIGRATIONS = [
    # v1.7.1 — Patient medical fields
    ("patients", "blood_type", "VARCHAR(10)", "'NON_RENSEIGNE'"),
    ("patients", "allergies", "TEXT", "'Non renseigné'"),
    ("patients", "medical_history", "TEXT", "'Non renseigné'"),
    ("patients", "current_medication", "TEXT", "'Non renseigné'"),
    ("patients", "chronic_conditions", "TEXT", "'Non renseigné'"),
]


def run_manual_migrations():
    """Ajoute les colonnes manquantes aux tables existantes."""
    inspector = inspect(engine)
    added = 0
    
    for table, column, col_type, default in MIGRATIONS:
        # Vérifier si la table existe
        if table not in inspector.get_table_names():
            logger.info("Table %s doesn't exist — skipping", table)
            continue
        
        # Vérifier si la colonne existe déjà
        existing_columns = [c["name"] for c in inspector.get_columns(table)]
        if column in existing_columns:
            logger.info("Column %s.%s already exists — skipping", table, column)
            continue
        
        # Ajouter la colonne
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} NOT NULL DEFAULT {default}"
        logger.info("Adding column: %s", sql)
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            added += 1
            print(f"  ✅ Added {table}.{column}")
        except Exception as e:
            logger.warning("Failed to add %s.%s: %s", table, column, e)
            print(f"  ⚠️ Failed {table}.{column}: {e}")
    
    if added > 0:
        print(f"  ✅ {added} columns added successfully")
    else:
        print("  ✅ All columns already exist — nothing to do")
    
    engine.dispose()


if __name__ == "__main__":
    run_manual_migrations()
