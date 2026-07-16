from neo4j import GraphDatabase

from app.config import get_settings
from app.graph.enums import EntityLabel, GraphRelationshipType


def _constraint_name(label: EntityLabel) -> str:
    return f"ore_{label.value.lower()}_id"


def _relationship_index_name(relationship_type: GraphRelationshipType) -> str:
    return f"ore_{relationship_type.value.lower()}_relationship_id"


def initialize_graph_schema() -> None:
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        with driver.session() as session:
            for label in EntityLabel:
                session.run(
                    f"CREATE CONSTRAINT {_constraint_name(label)} IF NOT EXISTS "
                    f"FOR (n:{label.value}) REQUIRE n.id IS UNIQUE"
                )

            for relationship_type in GraphRelationshipType:
                session.run(
                    f"CREATE INDEX {_relationship_index_name(relationship_type)} IF NOT EXISTS "
                    f"FOR ()-[r:{relationship_type.value}]-() ON (r.id)"
                )
    finally:
        driver.close()


if __name__ == "__main__":
    initialize_graph_schema()
