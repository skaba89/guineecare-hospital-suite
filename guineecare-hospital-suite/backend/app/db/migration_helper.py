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
# Pour les colonnes nullable sans default, passer default=None.
# NOTE : utiliser TIMESTAMP au lieu de DATETIME pour compat PostgreSQL.
# SQLite accepte aussi TIMESTAMP.
MIGRATIONS = [
    # v1.7.1 — Patient medical fields
    ("patients", "blood_type", "VARCHAR(10)", "'NON_RENSEIGNE'"),
    ("patients", "allergies", "TEXT", "'Non renseigné'"),
    ("patients", "medical_history", "TEXT", "'Non renseigné'"),
    ("patients", "current_medication", "TEXT", "'Non renseigné'"),
    ("patients", "chronic_conditions", "TEXT", "'Non renseigné'"),
    # v2.2.0 — Phase 6 : session invalidation forte (last_disabled_at)
    ("users", "last_disabled_at", "TIMESTAMP", None),
    # v2.4.0 — Phase 4 : parcours métiers
    # Pharmacie : valorisation + traçabilité lot/péremption
    ("pharmacy_products", "unit_price", "FLOAT", "0"),
    ("pharmacy_stock", "batch_number", "VARCHAR(100)", None),
    ("pharmacy_stock", "expiry_date", "TIMESTAMP", None),
    ("stock_movements", "patient_id", "VARCHAR(36)", None),
    ("stock_movements", "prescription_id", "VARCHAR(36)", None),
    ("stock_movements", "admission_id", "VARCHAR(36)", None),
    # Facturation : annulation contrôlée
    ("invoices", "cancellation_reason", "VARCHAR(500)", None),
    ("invoices", "cancelled_at", "TIMESTAMP", None),
    ("invoices", "cancelled_by", "VARCHAR(36)", None),
    # v2.5.0 — Phase 5 : hiérarchie administrative Facility
    ("facilities", "commune", "VARCHAR(150)", None),
    # v2.8.2 — P0-7 fix : valeur numérique pour measurements (charts/FHIR)
    ("patient_measurements", "value_numeric", "FLOAT", None),
    # v2.8.3 — P2-2 : colonnes dédiées pour prélèvement labo
    ("lab_orders", "sample_id", "VARCHAR(100)", None),
    ("lab_orders", "collected_by", "VARCHAR(36)", None),
    ("lab_orders", "collected_at", "TIMESTAMP", None),
    # v2.6.0 — Phase 7 : lab_orders.test_id devient nullable (panels multi-tests)
    # NOTE : la table prescriptions et lab_order_tests sont créées par create_all
    # car elles sont nouvelles (pas d'ALTER nécessaire).
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
        if default is None:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
        else:
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


# Colonnes à modifier (ALTER COLUMN type) — pour les colonnes existantes
# avec un type trop petit
COLUMN_TYPE_MIGRATIONS = [
    ("patients", "blood_type", "VARCHAR(20)"),
]

# Colonnes à rendre nullable (ALTER COLUMN DROP NOT NULL)
# v2.6.0 — Phase 7 : lab_orders.test_id devient nullable pour les panels multi-tests
NULLABLE_MIGRATIONS = [
    ("lab_orders", "test_id"),
]


def run_column_type_migrations():
    """Modifie le type des colonnes existantes si elles sont trop petites."""
    inspector = inspect(engine)
    modified = 0
    
    for table, column, new_type in COLUMN_TYPE_MIGRATIONS:
        if table not in inspector.get_table_names():
            continue
        existing_columns = [c["name"] for c in inspector.get_columns(table)]
        if column not in existing_columns:
            continue
        
        sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {new_type}"
        logger.info("Modifying column type: %s", sql)
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            modified += 1
            print(f"  ✅ Modified {table}.{column} → {new_type}")
        except Exception as e:
            logger.warning("Failed to modify %s.%s: %s", table, column, e)
            print(f"  ⚠️ Failed {table}.{column}: {e}")
    
    if modified > 0:
        print(f"  ✅ {modified} column types modified")
    else:
        print("  ✅ All column types already correct")
    
    engine.dispose()


def run_nullable_migrations():
    """Rend les colonnes existantes nullable (DROP NOT NULL).

    v2.6.0 — Phase 7 : lab_orders.test_id devient nullable pour les panels
    multi-tests (1 commande = N tests via lab_order_tests).
    """
    inspector = inspect(engine)
    modified = 0

    for table, column in NULLABLE_MIGRATIONS:
        if table not in inspector.get_table_names():
            continue
        existing_columns = [c["name"] for c in inspector.get_columns(table)]
        if column not in existing_columns:
            continue

        # Vérifier si la colonne est déjà nullable
        col_info = next((c for c in inspector.get_columns(table) if c["name"] == column), None)
        if col_info and col_info.get("nullable", False):
            logger.info("Column %s.%s already nullable — skipping", table, column)
            continue

        # PostgreSQL : ALTER TABLE ... ALTER COLUMN ... DROP NOT NULL
        # SQLite : ne supporte pas ALTER COLUMN DROP NOT NULL directement
        # → on skip sur SQLite (le modèle SQLAlchemy gère le null côté Python)
        sql = f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"
        logger.info("Making nullable: %s", sql)
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            modified += 1
            print(f"  ✅ Made {table}.{column} nullable")
        except Exception as e:
            logger.warning("Failed to make %s.%s nullable: %s", table, column, e)
            print(f"  ⚠️ Failed {table}.{column} nullable: {e}")

    if modified > 0:
        print(f"  ✅ {modified} columns made nullable")
    else:
        print("  ✅ All nullable migrations already applied")

    engine.dispose()
