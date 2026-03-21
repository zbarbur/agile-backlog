"""BacklogItem Pydantic model and helpers for agile-backlog."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
    goal: str = ""
    complexity: Literal["S", "M", "L"] | None = None
    technical_specs: list[str] = Field(default_factory=list)
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    test_plan: list[str] = Field(default_factory=list)
    notes: str = ""
    phase: Literal["plan", "build", "review"] | None = None
    design_reviewed: bool = False
    code_reviewed: bool = False

    @model_validator(mode="before")
    @classmethod
    def migrate_old_phases(cls, data):
        """Map old 8-value phase enum to new 3-value enum on load."""
        if isinstance(data, dict):
            old_phase = data.get("phase")
            if old_phase and old_phase not in ("plan", "build", "review"):
                phase_map = {
                    "scoping": "plan",
                    "spec": "plan",
                    "spec-review": "plan",
                    "design": "plan",
                    "design-review": "plan",
                    "coding": "build",
                    "code-review": "review",
                    "testing": "review",
                }
                data["phase"] = phase_map.get(old_phase, "plan")
        return data

    def to_yaml_dict(self) -> dict:
        """Serialize to dict for YAML output, excluding id (derived from filename)."""
        d = self.model_dump()
        d.pop("id")
        return d
