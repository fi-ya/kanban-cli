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

VALID_STORY_POINTS = (1, 2, 3, 5, 8, 13)
DOR_CHECKLIST_ITEMS = (
    "clear_user_story",
    "acceptance_criteria",
    "small_enough",
)
DOD_CHECKLIST_ITEMS = (
    "code_complete",
    "tests_pass",
    "reviewed",
)
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

    for task in normalized["tasks"]:
        task.setdefault("story_points", 0)
        task.setdefault("blocked", False)
        task["dor"] = normalize_checklist(task.get("dor"), DOR_CHECKLIST_ITEMS)
        task["dod"] = normalize_checklist(task.get("dod"), DOD_CHECKLIST_ITEMS)

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
    state: dict[str, Any],
    title: str,
    description: str = "",
    sprint_id: str | None = None,
    story_points: int = 0,
    dor: dict[str, bool] | None = None,
    dod: dict[str, bool] | None = None,
) -> dict[str, Any]:
    clean_title = title.strip()
    if not clean_title:
        raise ValidationError("Task title cannot be empty.")

    normalized = normalize_state(state)
    if story_points != 0:
        validate_story_points(story_points)

    task = {
        "id": next_id(normalized["tasks"], "task"),
        "title": clean_title,
        "description": description.strip(),
        "status": TASK_TODO,
        "sprint_id": None,
        "story_points": story_points,
        "blocked": False,
        "dor": normalize_checklist(dor, DOR_CHECKLIST_ITEMS),
        "dod": normalize_checklist(dod, DOD_CHECKLIST_ITEMS),
    }

    if sprint_id is not None:
        sprint = get_sprint(normalized, sprint_id)
        if sprint.get("status") != SPRINT_ACTIVE:
            raise ValidationError("Tasks can only be added directly to an Active sprint.")
        validate_ready_for_sprint(task)
        task["sprint_id"] = sprint_id

    normalized["tasks"].append(task)
    if sprint_id is not None:
        sprint["task_ids"].append(task["id"])
    return task


def assign_task_to_sprint(state: dict[str, Any], task_id: str, sprint_id: str) -> dict[str, Any]:
    normalized = normalize_state(state)
    task = get_task(normalized, task_id)
    sprint = get_sprint(normalized, sprint_id)

    if task.get("sprint_id") is not None:
        raise ValidationError("Only Product Backlog tasks can be assigned to a sprint.")
    if sprint.get("status") != SPRINT_ACTIVE:
        raise ValidationError("Tasks can only be assigned to an Active sprint.")

    validate_ready_for_sprint(task)
    task["sprint_id"] = sprint_id
    sprint["task_ids"].append(task_id)
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


def validate_story_points(story_points: int) -> None:
    if story_points not in VALID_STORY_POINTS:
        allowed_points = ", ".join(str(point) for point in VALID_STORY_POINTS)
        raise ValidationError(f"Story points must be one of: {allowed_points}.")


def validate_ready_for_sprint(task: dict[str, Any]) -> None:
    story_points = task.get("story_points", 0)
    if story_points <= 0:
        raise ValidationError("Task must have story points before it can enter a sprint.")
    validate_story_points(story_points)

    if not checklist_complete(task.get("dor", {}), DOR_CHECKLIST_ITEMS):
        raise ValidationError("Task cannot enter a sprint until every DoR item is complete.")


def validate_ready_for_done(task: dict[str, Any]) -> None:
    if not checklist_complete(task.get("dod", {}), DOD_CHECKLIST_ITEMS):
        raise ValidationError("Task cannot move to Done until every DoD item is complete.")


def normalize_checklist(
    checklist: dict[str, bool] | None, required_items: tuple[str, ...]
) -> dict[str, bool]:
    normalized = {item: False for item in required_items}
    if checklist is None:
        return normalized
    if not isinstance(checklist, dict):
        raise ValidationError("Checklist values must be JSON objects.")

    for item, complete in checklist.items():
        if item in normalized:
            normalized[item] = bool(complete)
    return normalized


def checklist_complete(checklist: dict[str, bool], required_items: tuple[str, ...]) -> bool:
    return all(bool(checklist.get(item)) for item in required_items)


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


def get_task(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in state["tasks"]:
        if task.get("id") == task_id:
            return task
    raise ValidationError(f"Task '{task_id}' does not exist.")


def find_active_sprint(state: dict[str, Any]) -> dict[str, Any] | None:
    for sprint in state["sprints"]:
        if sprint.get("status") == SPRINT_ACTIVE:
            return sprint
    return None


def set_task_status(state: dict[str, Any], task_id: str, status: str) -> dict[str, Any]:
    if status not in TASK_STATUSES:
        allowed_statuses = ", ".join(TASK_STATUSES)
        raise ValidationError(f"Task status must be one of: {allowed_statuses}.")

    task = get_task(normalize_state(state), task_id)
    if task.get("blocked") and task.get("status") != status:
        raise ValidationError("Blocked tasks cannot move columns. Unblock the task first.")
    if status == TASK_DONE and task.get("status") != TASK_DONE:
        validate_ready_for_done(task)

    task["status"] = status
    return task


def set_story_points(state: dict[str, Any], task_id: str, story_points: int) -> dict[str, Any]:
    validate_story_points(story_points)
    task = get_task(normalize_state(state), task_id)
    task["story_points"] = story_points
    return task


def set_blocked(state: dict[str, Any], task_id: str, blocked: bool) -> dict[str, Any]:
    task = get_task(normalize_state(state), task_id)
    task["blocked"] = blocked
    return task


def set_checklist_item(
    state: dict[str, Any], task_id: str, checklist_name: str, item: str, complete: bool
) -> dict[str, Any]:
    task = get_task(normalize_state(state), task_id)
    if checklist_name == "dor":
        required_items = DOR_CHECKLIST_ITEMS
    elif checklist_name == "dod":
        required_items = DOD_CHECKLIST_ITEMS
    else:
        raise ValidationError("Checklist must be 'dor' or 'dod'.")

    if item not in required_items:
        allowed_items = ", ".join(required_items)
        raise ValidationError(f"{checklist_name.upper()} item must be one of: {allowed_items}.")

    task[checklist_name][item] = complete
    return task


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
        print("6. Create a backlog task")
        print("7. Assign story points")
        print("8. Mark a DoR item complete")
        print("9. Mark a DoD item complete")
        print("10. Assign backlog task to sprint")
        print("11. Set task status")
        print("12. Block a task")
        print("13. Unblock a task")
        print("14. Show state")
        print("15. Quit")

        choice = input("Choose an option: ").strip()
        if choice == "15":
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
                points = int(input("Story points: ").strip())
                dor = {item: True for item in DOR_CHECKLIST_ITEMS}
                task = create_task(
                    state,
                    title,
                    description,
                    sprint_id=sprint_id,
                    story_points=points,
                    dor=dor,
                )
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
                task = create_task(state, input("Task title: "), input("Task description: "))
                save_state(state)
                print(f"Created backlog task {task['id']}.")
            elif choice == "7":
                task_id = input("Task ID: ").strip()
                points = int(input("Story points: ").strip())
                task = set_story_points(state, task_id, points)
                save_state(state)
                print(f"Set {task['id']} to {task['story_points']} points.")
            elif choice == "8":
                print("DoR items: clear_user_story, acceptance_criteria, small_enough")
                task = set_checklist_item(
                    state,
                    input("Task ID: ").strip(),
                    "dor",
                    input("DoR item: ").strip(),
                    True,
                )
                save_state(state)
                print(f"Updated DoR for {task['id']}.")
            elif choice == "9":
                print("DoD items: code_complete, tests_pass, reviewed")
                task = set_checklist_item(
                    state,
                    input("Task ID: ").strip(),
                    "dod",
                    input("DoD item: ").strip(),
                    True,
                )
                save_state(state)
                print(f"Updated DoD for {task['id']}.")
            elif choice == "10":
                task = assign_task_to_sprint(
                    state, input("Task ID: ").strip(), input("Sprint ID: ").strip()
                )
                save_state(state)
                print(f"Assigned {task['id']} to {task['sprint_id']}.")
            elif choice == "11":
                task = set_task_status(
                    state, input("Task ID: ").strip(), input("Status: ").strip()
                )
                save_state(state)
                print(f"Set {task['id']} to {task['status']}.")
            elif choice == "12":
                task = set_blocked(state, input("Task ID: ").strip(), True)
                save_state(state)
                print(f"Blocked {task['id']}.")
            elif choice == "13":
                task = set_blocked(state, input("Task ID: ").strip(), False)
                save_state(state)
                print(f"Unblocked {task['id']}.")
            elif choice == "14":
                print(show_state(state))
            else:
                print("Choose a number from 1 to 15.")
        except ValidationError as error:
            print(f"Error: {error}")


def run_demo() -> None:
    state = deepcopy(DEFAULT_STATE)

    sprint_one = create_sprint(state, "Sprint 1")
    sprint_two = create_sprint(state, "Sprint 2")
    start_sprint(state, sprint_one["id"])
    ready_dor = {item: True for item in DOR_CHECKLIST_ITEMS}
    unfinished_task = create_task(
        state,
        "Build booking flow",
        sprint_id=sprint_one["id"],
        story_points=5,
        dor=ready_dor,
    )
    done_task = create_task(
        state,
        "Draft booking policy",
        sprint_id=sprint_one["id"],
        story_points=2,
        dor=ready_dor,
        dod={item: True for item in DOD_CHECKLIST_ITEMS},
    )
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
    task_parser.add_argument("story_points", type=int)
    task_parser.add_argument(
        "--dor-ready",
        action="store_true",
        help="Mark all DoR items complete for this task",
    )

    backlog_parser = subparsers.add_parser("create-task", help="Create a Product Backlog task")
    backlog_parser.add_argument("title")
    backlog_parser.add_argument("description", nargs="?", default="")

    assign_parser = subparsers.add_parser("assign-task", help="Assign a backlog task to a sprint")
    assign_parser.add_argument("task_id")
    assign_parser.add_argument("sprint_id")

    points_parser = subparsers.add_parser("set-points", help="Assign Fibonacci story points")
    points_parser.add_argument("task_id")
    points_parser.add_argument("story_points", type=int)

    dor_parser = subparsers.add_parser("mark-dor", help="Mark one DoR item complete")
    dor_parser.add_argument("task_id")
    dor_parser.add_argument("item", choices=DOR_CHECKLIST_ITEMS)

    dod_parser = subparsers.add_parser("mark-dod", help="Mark one DoD item complete")
    dod_parser.add_argument("task_id")
    dod_parser.add_argument("item", choices=DOD_CHECKLIST_ITEMS)

    status_parser = subparsers.add_parser("set-task-status", help="Update a task status")
    status_parser.add_argument("task_id")
    status_parser.add_argument("status", choices=TASK_STATUSES)

    block_parser = subparsers.add_parser("block-task", help="Freeze a task from moving columns")
    block_parser.add_argument("task_id")

    unblock_parser = subparsers.add_parser("unblock-task", help="Allow a blocked task to move again")
    unblock_parser.add_argument("task_id")

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
            dor = {item: args.dor_ready for item in DOR_CHECKLIST_ITEMS}
            task = create_task(
                state,
                args.title,
                args.description,
                sprint_id=args.sprint_id,
                story_points=args.story_points,
                dor=dor,
            )
            save_state(state)
            print(f"Added {task['id']} to {args.sprint_id}.")
        elif args.command == "create-task":
            task = create_task(state, args.title, args.description)
            save_state(state)
            print(f"Created backlog task {task['id']}.")
        elif args.command == "assign-task":
            task = assign_task_to_sprint(state, args.task_id, args.sprint_id)
            save_state(state)
            print(f"Assigned {task['id']} to {task['sprint_id']}.")
        elif args.command == "set-points":
            task = set_story_points(state, args.task_id, args.story_points)
            save_state(state)
            print(f"Set {task['id']} to {task['story_points']} points.")
        elif args.command == "mark-dor":
            task = set_checklist_item(state, args.task_id, "dor", args.item, True)
            save_state(state)
            print(f"Updated DoR for {task['id']}.")
        elif args.command == "mark-dod":
            task = set_checklist_item(state, args.task_id, "dod", args.item, True)
            save_state(state)
            print(f"Updated DoD for {task['id']}.")
        elif args.command == "set-task-status":
            task = set_task_status(state, args.task_id, args.status)
            save_state(state)
            print(f"Set {task['id']} to {task['status']}.")
        elif args.command == "block-task":
            task = set_blocked(state, args.task_id, True)
            save_state(state)
            print(f"Blocked {task['id']}.")
        elif args.command == "unblock-task":
            task = set_blocked(state, args.task_id, False)
            save_state(state)
            print(f"Unblocked {task['id']}.")
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