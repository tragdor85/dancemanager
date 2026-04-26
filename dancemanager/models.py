"""Core data models / schemas for Dance Manager.

These dicts define the structure of every collection and serve as the
single source of truth for data validation.
"""

from typing import Any, Dict

DEFAULT_STORE_SCHEMA: Dict[str, Any] = {
    "version": "1.0.0",
    "dancers": [],
    "teams": [],
    "classes": [],
    "instructors": [],
    "dances": [],
    "recitals": [],
    "schedules": [],
    "studios": [],
}


def make_dancer_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for a dancer."""
    return name.strip().lower().replace(" ", "-")


def make_team_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for a team."""
    return name.strip().lower().replace(" ", "-")


def make_class_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for a class."""
    return name.strip().lower().replace(" ", "-")


def make_instructor_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for an instructor."""
    return name.strip().lower().replace(" ", "-")


def make_dance_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for a dance."""
    return name.strip().lower().replace(" ", "-")


def make_recital_id(name: str) -> str:
    """Return a deterministic, human-friendly ID for a recital."""
    return name.strip().lower().replace(" ", "-")
