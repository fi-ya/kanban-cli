"""A small terminal-based Kanban task manager."""

from __future__ import annotations

from dataclasses import dataclass


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
    print("  help    Show commands")
    print("  quit    Exit")


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

        print("Unknown command. Type 'help' to see available commands.")


if __name__ == "__main__":
    main()