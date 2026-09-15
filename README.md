# Kanban CLI

A local terminal-based Kanban task manager for the CoSpace planning exercise.

## How to Run

From the project folder, run:

```bash
python kanban_cli.py
```

If your machine uses `python3` instead of `python`, run:

```bash
python3 kanban_cli.py
```

## CLI Commands

Once the app starts, use these commands:

```text
add     Add a task
move    Move a task to the next column
board   Show the board
help    Show commands
quit    Exit
```

Example flow:

```text
Command: add
Title: Book a desk
Description: Let users reserve a workspace

Command: board

Command: move
Task title: Book a desk

Command: board
```

## Scrum Lifecycle Core

The sprint lifecycle validation rules are implemented in `planner_core.py`, with the initial persisted schema shown in `state.json`.