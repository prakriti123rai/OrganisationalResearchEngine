from app.graph.enums import EntityLabel, GraphRelationshipType

__all__ = ["EntityLabel", "GraphRelationshipType", "initialize_graph_schema"]


def __getattr__(name: str):
    if name == "initialize_graph_schema":
        from app.graph.schema import initialize_graph_schema

        return initialize_graph_schema
    raise AttributeError(name)
