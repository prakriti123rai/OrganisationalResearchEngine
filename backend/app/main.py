import socket
from contextlib import closing
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.actions import router as actions_router
from app.api.dashboard import router as dashboard_router
from app.api.evidence import router as evidence_router
from app.api.execution import router as execution_router
from app.api.graph import router as graph_router
from app.api.reasoning import router as reasoning_router
from app.api.reasoning_context import router as reasoning_context_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evidence_router)
app.include_router(graph_router)
app.include_router(reasoning_context_router)
app.include_router(reasoning_router)
app.include_router(actions_router)
app.include_router(execution_router)
app.include_router(dashboard_router)


def _tcp_reachable(host: str, port: int, timeout_seconds: float = 1.0) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout_seconds)):
            return True
    except OSError:
        return False


@app.get("/health")
def health() -> dict[str, Any]:
    postgres = _tcp_reachable(settings.postgres_host, settings.postgres_port)
    neo4j = _tcp_reachable(settings.neo4j_host, settings.neo4j_bolt_port)

    return {
        "status": "ok" if postgres and neo4j else "degraded",
        "service": "backend",
        "version": settings.app_version,
        "dependencies": {
            "postgres": {
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "reachable": postgres,
            },
            "neo4j": {
                "host": settings.neo4j_host,
                "port": settings.neo4j_bolt_port,
                "reachable": neo4j,
            },
        },
    }
