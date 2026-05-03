from sqlalchemy import create_engine, inspect

from app.data.db import Base


def test_database_schema_contains_core_tables():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {"orders", "escalations", "conversation_logs"} <= table_names
