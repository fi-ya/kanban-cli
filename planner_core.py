"""Core Scrum lifecycle rules for the CoSpace planner."""

from __future__ import annotations

import argparse
import json
import sys
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

    for sprint in normalized["sprints"]:
        sprint.setdefault("task_ids", [])
        if not isinstance(sprint["task_ids"], list):
            raise ValidationError("Each sprint must have a task_ids list.")

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
        "task_ids": [],
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
        if sprint.get("status") != SPRINT_ACTIVE:
            raise ValidationError("Tasks can only be added directly to an Active sprint.")

    task = {
        "id": next_id(normalized["tasks"], "task"),
        "title": clean_title,
        "description": description.strip(),
        "status": TASK_TODO,
        "sprint_id": sprint_id,
    }
    normalized["tasks"].append(task)
    if sprint_id is not None:
        sprint["task_ids"].append(task["id"])
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
    sprint = get_sprint(state, sprint_id)
    for task in state["tasks"]:
        if task.get("sprint_id") == sprint_id and task.get("status") != TASK_DONE:
            task["sprint_id"] = None
            task["status"] = TASK_TODO
            if task.get("id") in sprint["task_ids"]:
                sprint["task_ids"].remove(task["id"])


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


def set_task_status(state: dict[str, Any], task_id: str, status: str) -> dict[str, Any]:
    if status not in TASK_STATUSES:
        allowed_statuses = ", ".join(TASK_STATUSES)
        raise ValidationError(f"Task status must be one of: {allowed_statuses}.")

    for task in normalize_state(state)["tasks"]:
        if task.get("id") == task_id:
            task["status"] = status
            return task

    raise ValidationError(f"Task '{task_id}' does not exist.")


def show_state(state: dict[str, Any]) -> str:
    return json.dumps(normalize_state(state), indent=2)


def run_interactive() -> None:
    while True:
        print("\nCoSpace Planner")
        print("1. Create a sprint")
        print("2. Start a sprint")
        print("3. Add a task to an active sprint")
        print("4. Complete a sprint")
        print("5. Add a retrospective card")
        print("6. Show state")
        print("7. Quit")

        choice = input("Choose an option: ").strip()
        if choice == "7":
            print("Goodbye.")
            return

        try:
            state = load_state()

            if choice == "1":
                sprint = create_sprint(state, input("Sprint name: "))
                save_state(state)
                print(f"Created {sprint['id']} in {sprint['status']}.")
            elif choice == "2":
                sprint = start_sprint(state, input("Sprint ID: ").strip())
                save_state(state)
                print(f"Started {sprint['id']}.")
            elif choice == "3":
                sprint_id = input("Sprint ID: ").strip()
                title = input("Task title: ")
                description = input("Task description: ")
                task = create_task(state, title, description, sprint_id=sprint_id)
                save_state(state)
                print(f"Added {task['id']} to {sprint_id}.")
            elif choice == "4":
                sprint = complete_sprint(state, input("Sprint ID: ").strip())
                save_state(state)
                print(f"Completed {sprint['id']}; unfinished work returned to backlog.")
            elif choice == "5":
                sprint_id = input("Sprint ID: ").strip()
                print("Categories: Went Well, To Improve, Action Item")
                category = input("Category: ").strip()
                text = input("Card text: ")
                card = add_retro_card(state, sprint_id, category, text)
                save_state(state)
                print(f"Added {card['id']} to {sprint_id}.")
            elif choice == "6":
                print(show_state(state))
            else:
                print("Choose a number from 1 to 7.")
        except ValidationError as error:
            print(f"Error: {error}")


def run_demo() -> None:
    state = deepcopy(DEFAULT_STATE)

    sprint_one = create_sprint(state, "Sprint 1")
    sprint_two = create_sprint(state, "Sprint 2")
    start_sprint(state, sprint_one["id"])
    unfinished_task = create_task(state, "Build booking flow", sprint_id=sprint_one["id"])
    done_task = create_task(state, "Draft booking policy", sprint_id=sprint_one["id"])
    set_task_status(state, done_task["id"], TASK_DONE)

    print("1. Block starting a second active sprint")
    try:
        start_sprint(state, sprint_two["id"])
    except ValidationError as error:
        print(f"Blocked: {error}")

    print("\n2. Block retro cards before sprint completion")
    try:
        add_retro_card(state, sprint_one["id"], "Went Well", "Strong collaboration")
    except ValidationError as error:
        print(f"Blocked: {error}")

    print("\n3. Complete sprint and return unfinished work to backlog")
    complete_sprint(state, sprint_one["id"])
    print(
        f"{unfinished_task['title']} now has sprint_id={unfinished_task['sprint_id']} "
        f"and status={unfinished_task['status']}"
    )

    print("\n4. Allow retro cards after completion")
    card = add_retro_card(state, sprint_one["id"], "Went Well", "The sprint goal was clear")
    print(f"Added retro card: {card['category']}")

    print("\nFinal demo state")
    print(show_state(state))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage CoSpace Planner sprint state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-sprint", help="Create a Planning sprint")
    create_parser.add_argument("name")

    start_parser = subparsers.add_parser("start-sprint", help="Start a Planning sprint")
    start_parser.add_argument("sprint_id")

    task_parser = subparsers.add_parser("add-task", help="Add a task to an Active sprint")
    task_parser.add_argument("sprint_id")
    task_parser.add_argument("title")
    task_parser.add_argument("description", nargs="?", default="")

    status_parser = subparsers.add_parser("set-task-status", help="Update a task status")
    status_parser.add_argument("task_id")
    status_parser.add_argument("status", choices=TASK_STATUSES)

    complete_parser = subparsers.add_parser("complete-sprint", help="Complete an Active sprint")
    complete_parser.add_argument("sprint_id")

    retro_parser = subparsers.add_parser("add-retro", help="Add a retro card to a Completed sprint")
    retro_parser.add_argument("sprint_id")
    retro_parser.add_argument("category", choices=RETRO_CATEGORIES)
    retro_parser.add_argument("text")

    subparsers.add_parser("show", help="Print the current state.json contents")
    subparsers.add_parser("demo", help="Run the sprint lifecycle showcase without changing state.json")
    return parser


def main() -> None:
    if len(sys.argv) == 1:
        run_interactive()
        return

    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "demo":
            run_demo()
            return

        state = load_state()

        if args.command == "create-sprint":
            sprint = create_sprint(state, args.name)
            save_state(state)
            print(f"Created {sprint['id']} in {sprint['status']}.")
        elif args.command == "start-sprint":
            sprint = start_sprint(state, args.sprint_id)
            save_state(state)
            print(f"Started {sprint['id']}.")
        elif args.command == "add-task":
            task = create_task(state, args.title, args.description, sprint_id=args.sprint_id)
            save_state(state)
            print(f"Added {task['id']} to {args.sprint_id}.")
        elif args.command == "set-task-status":
            task = set_task_status(state, args.task_id, args.status)
            save_state(state)
            print(f"Set {task['id']} to {task['status']}.")
        elif args.command == "complete-sprint":
            sprint = complete_sprint(state, args.sprint_id)
            save_state(state)
            print(f"Completed {sprint['id']}; unfinished work returned to backlog.")
        elif args.command == "add-retro":
            card = add_retro_card(state, args.sprint_id, args.category, args.text)
            save_state(state)
            print(f"Added {card['id']} to {args.sprint_id}.")
        elif args.command == "show":
            print(show_state(state))
    except ValidationError as error:
        parser.exit(1, f"Error: {error}\n")


def next_id(items: list[dict[str, Any]], prefix: str) -> str:
    return f"{prefix}-{len(items) + 1}"


if __name__ == "__main__":
    main()