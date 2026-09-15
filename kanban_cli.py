"""A small terminal-based Kanban task manager."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core import (
    DOD_CHECKLIST_ITEMS,
    DOR_CHECKLIST_ITEMS,
    ValidationError,
    add_retro_card,
    assign_task_to_sprint,
    complete_sprint,
    create_sprint,
    create_task as create_planner_task,
    load_state,
    save_state,
    set_blocked,
    set_checklist_item,
    set_story_points,
    set_task_status,
    show_state,
    start_sprint,
)


STATUSES = ("To Do", "In Progress", "Done")
IN_PROGRESS_LIMIT = 2


@dataclass
class Task:
    title: str
    description: str
    status: str = "To Do"

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.description = self.description.strip()


class KanbanBoard:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def add_task(self, title: str, description: str) -> str:
        clean_title = title.strip()
        clean_description = description.strip()

        if not clean_title:
            return "Task title cannot be empty. Please enter a short, unique title."

        if self.find_task(clean_title) is not None:
            return f"A task named '{clean_title}' already exists. Choose a unique title."

        self.tasks.append(Task(clean_title, clean_description))
        return f"Added '{clean_title}' to To Do."

    def find_task(self, title: str) -> Task | None:
        normalized_title = title.strip().casefold()
        for task in self.tasks:
            if task.title.casefold() == normalized_title:
                return task
        return None

    def move_task_forward(self, title: str) -> str:
        task = self.find_task(title)

        if task is None:
            return f"No task named '{title.strip()}' was found."

        current_index = STATUSES.index(task.status)
        if current_index == len(STATUSES) - 1:
            return f"'{task.title}' is already Done and cannot move forward."

        next_status = STATUSES[current_index + 1]
        if next_status == "In Progress" and self.in_progress_count() >= IN_PROGRESS_LIMIT:
            return (
                "In Progress is already at its WIP limit of "
                f"{IN_PROGRESS_LIMIT}. Finish or move a task before starting another."
            )

        task.status = next_status
        return f"Moved '{task.title}' to {next_status}."

    def in_progress_count(self) -> int:
        return sum(task.status == "In Progress" for task in self.tasks)

    def display(self) -> str:
        lines: list[str] = []
        for status in STATUSES:
            lines.append(f"\n{status}")
            lines.append("-" * len(status))

            tasks_in_column = [task for task in self.tasks if task.status == status]
            if not tasks_in_column:
                lines.append("  No tasks")
                continue

            for task in tasks_in_column:
                description = f" - {task.description}" if task.description else ""
                lines.append(f"  - {task.title}{description}")

        return "\n".join(lines).strip()


def print_help() -> None:
    print("Commands:")
    print("  add     Add a task")
    print("  move    Move a task to the next column")
    print("  board   Show the board")
    print("  sprint-create    Create a Planning sprint")
    print("  sprint-start     Start a sprint")
    print("  sprint-task      Add a task to an Active sprint")
    print("  backlog-task     Create an unassigned backlog task")
    print("  sprint-assign    Assign a backlog task to an Active sprint")
    print("  points           Assign Fibonacci story points")
    print("  dor              Mark a DoR checklist item complete")
    print("  dod              Mark a DoD checklist item complete")
    print("  status           Move a task to a new column")
    print("  block            Block a task")
    print("  unblock          Unblock a task")
    print("  sprint-complete  Complete a sprint")
    print("  retro-add        Add a retrospective card")
    print("  state            Show sprint state.json")
    print("  help    Show commands")
    print("  quit    Exit")


def prompt_checklist(items: tuple[str, ...], checklist_name: str) -> dict[str, bool]:
    print(f"{checklist_name} checklist items: {', '.join(items)}")
    return {
        item: input(f"Is '{item}' complete? (y/n): ").strip().casefold() == "y"
        for item in items
    }


def run_planner_command(command: str) -> None:
    try:
        state = load_state()

        if command == "sprint-create":
            sprint = create_sprint(state, input("Sprint name: "))
            save_state(state)
            print(f"Created {sprint['id']} in {sprint['status']}.")
            return

        if command == "sprint-start":
            sprint = start_sprint(state, input("Sprint ID: ").strip())
            save_state(state)
            print(f"Started {sprint['id']}.")
            return

        if command == "sprint-task":
            sprint_id = input("Sprint ID: ").strip()
            title = input("Task title: ")
            description = input("Task description: ")
            points = int(input("Story points (1, 2, 3, 5, 8, 13): ").strip())
            dor = prompt_checklist(DOR_CHECKLIST_ITEMS, "DoR")
            task = create_planner_task(
                state,
                title,
                description,
                sprint_id=sprint_id,
                story_points=points,
                dor=dor,
            )
            save_state(state)
            print(f"Added {task['id']} to {sprint_id}.")
            return

        if command == "backlog-task":
            title = input("Task title: ")
            description = input("Task description: ")
            task = create_planner_task(state, title, description)
            save_state(state)
            print(f"Created backlog task {task['id']}.")
            return

        if command == "sprint-assign":
            task = assign_task_to_sprint(
                state, input("Task ID: ").strip(), input("Sprint ID: ").strip()
            )
            save_state(state)
            print(f"Assigned {task['id']} to {task['sprint_id']}.")
            return

        if command == "points":
            points = int(input("Story points (1, 2, 3, 5, 8, 13): ").strip())
            task = set_story_points(state, input("Task ID: ").strip(), points)
            save_state(state)
            print(f"Set {task['id']} to {task['story_points']} points.")
            return

        if command == "dor":
            print(f"DoR items: {', '.join(DOR_CHECKLIST_ITEMS)}")
            task = set_checklist_item(
                state, input("Task ID: ").strip(), "dor", input("DoR item: ").strip(), True
            )
            save_state(state)
            print(f"Updated DoR for {task['id']}.")
            return

        if command == "dod":
            print(f"DoD items: {', '.join(DOD_CHECKLIST_ITEMS)}")
            task = set_checklist_item(
                state, input("Task ID: ").strip(), "dod", input("DoD item: ").strip(), True
            )
            save_state(state)
            print(f"Updated DoD for {task['id']}.")
            return

        if command == "status":
            task = set_task_status(state, input("Task ID: ").strip(), input("Status: ").strip())
            save_state(state)
            print(f"Set {task['id']} to {task['status']}.")
            return

        if command == "block":
            task = set_blocked(state, input("Task ID: ").strip(), True)
            save_state(state)
            print(f"Blocked {task['id']}.")
            return

        if command == "unblock":
            task = set_blocked(state, input("Task ID: ").strip(), False)
            save_state(state)
            print(f"Unblocked {task['id']}.")
            return

        if command == "sprint-complete":
            sprint = complete_sprint(state, input("Sprint ID: ").strip())
            save_state(state)
            print(f"Completed {sprint['id']}; unfinished work returned to backlog.")
            return

        if command == "retro-add":
            sprint_id = input("Sprint ID: ").strip()
            print("Categories: Went Well, To Improve, Action Item")
            category = input("Category: ").strip()
            text = input("Card text: ")
            card = add_retro_card(state, sprint_id, category, text)
            save_state(state)
            print(f"Added {card['id']} to {sprint_id}.")
            return

        if command == "state":
            print(show_state(state))
    except ValidationError as error:
        print(f"Error: {error}")


def main() -> None:
    board = KanbanBoard()
    print("Kanban CLI")
    print_help()

    while True:
        command = input("\nCommand: ").strip().casefold()

        if command in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        if command == "help":
            print_help()
            continue

        if command == "board":
            print(board.display())
            continue

        if command == "add":
            title = input("Title: ")
            description = input("Description: ")
            print(board.add_task(title, description))
            continue

        if command == "move":
            title = input("Task title: ")
            print(board.move_task_forward(title))
            continue

        if command in {
            "sprint-create",
            "sprint-start",
            "sprint-task",
            "backlog-task",
            "sprint-assign",
            "points",
            "dor",
            "dod",
            "status",
            "block",
            "unblock",
            "sprint-complete",
            "retro-add",
            "state",
        }:
            run_planner_command(command)
            continue

        print("Unknown command. Type 'help' to see available commands.")


if __name__ == "__main__":
    main()