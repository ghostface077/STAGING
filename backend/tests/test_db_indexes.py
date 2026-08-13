"""Vérifie que les index de performance attendus (correctif #08) sont bien
déclarés au niveau des modèles SQLAlchemy — et donc présents à la fois sur le
schéma de test (créé via Base.metadata.create_all, indépendamment d'Alembic)
et sur le schéma réel (créé via la migration 0002_indexes)."""
from sqlalchemy import inspect

EXPECTED_INDEXES: dict[str, set[frozenset[str]]] = {
    "tickets": {
        frozenset({"status_id"}),
        frozenset({"technician_id"}),
        frozenset({"requester_id"}),
        frozenset({"category_id"}),
        frozenset({"priority_id"}),
        frozenset({"created_at"}),
        frozenset({"status_id", "created_at"}),
    },
    "comments": {frozenset({"ticket_id"})},
    "ticket_history": {frozenset({"ticket_id"})},
    "notifications": {frozenset({"user_id"})},
}


def _indexed_column_sets(db_session, table_name: str) -> set[frozenset[str]]:
    inspector = inspect(db_session.get_bind())
    return {frozenset(idx["column_names"]) for idx in inspector.get_indexes(table_name)}


def test_expected_indexes_exist_on_all_tables(db_session):
    for table_name, expected in EXPECTED_INDEXES.items():
        actual = _indexed_column_sets(db_session, table_name)
        missing = expected - actual
        assert not missing, f"Index manquant sur {table_name} pour les colonnes {missing}"


def test_satisfaction_ratings_ticket_id_not_redundantly_indexed(db_session):
    """satisfaction_ratings.ticket_id ne doit PAS avoir d'index dédié : sa
    contrainte UNIQUE en crée déjà un implicitement (voir migration 0002)."""
    inspector = inspect(db_session.get_bind())
    named_indexes = {idx["name"] for idx in inspector.get_indexes("satisfaction_ratings")}
    assert "ix_satisfaction_ratings_ticket_id" not in named_indexes
    # La contrainte UNIQUE, elle, doit bien exister (index implicite).
    unique_columns = {frozenset(c["column_names"]) for c in inspector.get_unique_constraints("satisfaction_ratings")}
    assert frozenset({"ticket_id"}) in unique_columns


def test_attachments_ticket_id_not_indexed(db_session):
    """attachments.ticket_id n'est jamais filtré/joint dans l'application :
    volontairement non indexé (voir justification dans la migration 0002)."""
    inspector = inspect(db_session.get_bind())
    indexed = _indexed_column_sets(db_session, "attachments")
    assert frozenset({"ticket_id"}) not in indexed
