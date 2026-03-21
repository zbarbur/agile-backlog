"""BacklogItem Pydantic model and helpers for agile-backlog."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


def slugify(title: str) -> str:
    """Convert a title to a URL-friendly slug ID."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


class BacklogItem(BaseModel):
    """A single backlog item."""

    id: str
    title: str
    status: Literal["backlog", "doing", "done"] = "backlog"
    priority: Literal["P1", "P2", "P3"]
    category: str
    sprint_target: int | None = None
    created: date = Field(default_factory=date.today)
    updated: date = Field(default_factory=date.today)
    depends_on: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    notes: str = ""
    phase: (
        Literal["scoping", "spec", "spec-review", "design", "design-review", "coding", "code-review", "testing"] | None
    ) = None

    def to_yaml_dict(self) -> dict:
        """Serialize to dict for YAML output, excluding id (derived from filename)."""
        d = self.model_dump()
        d.pop("id")
        return d
