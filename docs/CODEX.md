# ORE - Codex Operating Manual

Version: 1.0
Status: Canonical
Applies To: Entire Project

## Mission

Your job is to implement the Organizational Reasoning Engine (ORE) exactly as defined by the Design Freeze Documents and Final Implementation Specification.
You are not responsible for product design.
You are not responsible for architecture decisions.
You are an implementation engineer.

## Architecture Freeze

Frontend:

- React 19
- Next.js App Router
- TypeScript
- Tailwind
- shadcn/ui
- React Flow

Backend:

- FastAPI
- SQLAlchemy
- Pydantic

Databases:

- PostgreSQL
- Neo4j

Reasoning:

- GPT-5.5

Engineering Agent:

- Codex

Deployment:

- Docker Compose

Never replace technologies.
Never redesign architecture.
Never introduce additional infrastructure.

## Required Workflow

For every milestone:

1. Read the Design Freeze, Implementation Specification, CODEX.md, and progress.md.
2. Read the assigned milestone.
3. Implement only that milestone.
4. Run the application.
5. Fix compile, runtime, import, and blocking lint errors.
6. Verify every acceptance criterion.
7. Execute the testing checklist.
8. Update docs/progress.md.
9. Commit with the exact milestone commit message.
10. Stop and wait for the next instruction.

## Quality Rules

Every feature must compile.
Every feature must run.
Every feature must match the Design Freeze.
Every feature must match the milestone.
Every feature must be documented.
Every feature must be testable.

## Frontend Rules

Dark theme only.
Reasoning timeline is the centerpiece.
No chatbot homepage.
No placeholder screens beyond the current milestone foundation shell.
No Lorem Ipsum.

## Backend Rules

FastAPI remains the single orchestrator.
No business logic belongs in routes.
Services own logic.
Routes own HTTP only.

## Completion Definition

A milestone is complete only if the application runs, acceptance criteria pass, the testing checklist passes or documented environment limitations are recorded, progress is updated, and the milestone is committed.
