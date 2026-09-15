"""Core Scrum lifecycle rules for the CoSpace planner."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


STATE_FILE = Path("state.json")

SPRINT_PLANNING = "Planning"
SPRINT_ACTIVE = "Active"
SPRINT_COMPLETED = "Completed"
SPRINT_STATUSES = (SPRINT_PLANNING, SPRINT_ACTIVE, SPRINT_COMPLETED)

TASK_TODO = "To Do"
TASK_IN_PROGRESS = "In Progress"
TASK_DONE = "Done"
TASK_STATUSES = (TASK_TODO, TASK_IN_PROGRESS, TASK_DONE)

RETRO_CATEGORIES = ("Went Well", "To Improve", "Action Item")

DEFAULT_STATE: dict[str, Any] = {
    "schema_version": 1,
    "tasks": [],
    "sprints": [],
    "retro_cards": [],
}


class ValidationError(ValueError):
    """Raised when a Scrum lifecycle action would create invalid state."""


def load_state(path: Path = STATE_FILE) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return deepcopy(DEFAULT_STATE)

    try:
        raw_state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(
            f"Could not read {path}. Delete the file or replace it with valid JSON."
        ) from error

    if not isinstance(raw_state, dict):
        raise ValidationError("Planner state must be a JSON object.")

    return normalize_state(raw_state)


def save_state(state: dict[str, Any], path: Path = STATE_FILE) -> None:
    normalized_state = normalize_state(state)
    path.write_text(json.dumps(normalized_state, indent=2) + "\n", encoding="utf-8")


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(DEFAULT_STATE)
    normalized.update(state)

    for key in ("tasks", "sprints", "retro_cards"):
        if not isinstance(normalized.get(key), list):
            raise ValidationError(f"'{key}' must be a list in planner state.")

    return normalized


def create_sprint(state: dict[str, Any], name: str) -> dict[str, Any]:
    clean_name = name.strip()
    if not clean_name:
        raise ValidationError("Sprint name cannot be empty.")

    normalized = normalize_state(state)
    sprint = {
        "id": next_id(normalized["sprints"], "sprint"),
        "name": clean_name,
        "status": SPRINT_PLANNING,
    }
    normalized["sprints"].append(sprint)
    return sprint


def start_sprint(state: dict[str, Any], sprint_id: str) -> dict[str, Any]:
    normalized = normalize_state(state)
    sprint = get_sprint(normalized, sprint_id)
    validate_sprint_can_start(normalized, sprint)
    sprint["status"] = SPRINT_ACTIVE
    return sprint


def complete_sprint(state: dict[str, Any], sprint_id: str) -> dict[str, Any]:
    normalized = normalize_state(state)
    sprint = get_sprint(normalized, sprint_id)

    if sprint.get("status") != SPRINT_ACTIVE:
        raise ValidationError("Only an Active sprint can be completed.")

    sprint["status"] = SPRINT_COMPLETED
    move_unfinished_tasks_to_backlog(normalized, sprint_id)
    return sprint


def create_task(
    state: dict[str, Any], title: str, description: str = "", sprint_id: str | None = None
) -> dict[str, Any]:
    clean_title = title.strip()
    if not clean_title:
        raise ValidationError("Task title cannot be empty.")

    normalized = normalize_state(state)
    if sprint_id is not None:
        sprint = get_sprint(normalized, sprint_id)
        if sprint.get("status") == SPRINT_COMPLETED:
            raise ValidationError("Cannot assign new work to a Completed sprint.")

    task = {
        "id": next_id(normalized["tasks"], "task"),
        "title": clean_title,
        "description": description.strip(),
        "status": TASK_TODO,
        "sprint_id": sprint_id,
    }
    normalized["tasks"].append(task)
    return task


def add_retro_card(
    state: dict[str, Any], sprint_id: str, category: str, text: str
) -> dict[str, Any]:
    normalized = normalize_state(state)
    sprint = get_sprint(normalized, sprint_id)
    validate_retro_card(sprint, category, text)

    card = {
        "id": next_id(normalized["retro_cards"], "retro"),
        "sprint_id": sprint_id,
        "category": category,
        "text": text.strip(),
    }
    normalized["retro_cards"].append(card)
    return card


def validate_sprint_can_start(state: dict[str, Any], sprint: dict[str, Any]) -> None:
    if sprint.get("status") != SPRINT_PLANNING:
        raise ValidationError("Only a Planning sprint can be started.")

    active_sprint = find_active_sprint(state)
    if active_sprint is not None:
        raise ValidationError(
            "Cannot start a new sprint while "
            f"'{active_sprint.get('name', active_sprint['id'])}' is Active."
        )


def validate_retro_card(sprint: dict[str, Any], category: str, text: str) -> None:
    if sprint.get("status") != SPRINT_COMPLETED:
        raise ValidationError("Retrospective cards can only be added to Completed sprints.")

    if category not in RETRO_CATEGORIES:
        allowed_categories = ", ".join(RETRO_CATEGORIES)
        raise ValidationError(f"Retro category must be one of: {allowed_categories}.")

    if not text.strip():
        raise ValidationError("Retro card text cannot be empty.")


def move_unfinished_tasks_to_backlog(state: dict[str, Any], sprint_id: str) -> None:
    for task in state["tasks"]:
        if task.get("sprint_id") == sprint_id and task.get("status") != TASK_DONE:
            task["sprint_id"] = None
            task["status"] = TASK_TODO


def get_sprint(state: dict[str, Any], sprint_id: str) -> dict[str, Any]:
    for sprint in state["sprints"]:
        if sprint.get("id") == sprint_id:
            return sprint
    raise ValidationError(f"Sprint '{sprint_id}' does not exist.")


def find_active_sprint(state: dict[str, Any]) -> dict[str, Any] | None:
    for sprint in state["sprints"]:
        if sprint.get("status") == SPRINT_ACTIVE:
            return sprint
    return None


def next_id(items: list[dict[str, Any]], prefix: str) -> str:
    return f"{prefix}-{len(items) + 1}"