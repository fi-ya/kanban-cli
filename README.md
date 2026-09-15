# Kanban CLI

A simple terminal-based Kanban task manager for the CoSpace planning exercise.

## Requirements

- Python 3
- No external packages are required

## Run The App

From this project folder, run:

```bash
python kanban_cli.py
```

If your machine uses `python3` instead of `python`, run:

```bash
python3 kanban_cli.py
```

## Commands

Once the app starts, type one of these commands:

```text
add     Add a task
move    Move a task to the next column
board   Show the Kanban board
help    Show available commands
quit    Exit the app
```

## Example

```text
Command: add
Title: Book a desk
Description: Let users reserve a workspace

Command: board

Command: move
Task title: Book a desk

Command: board

Command: quit
```

## Kanban Rules

- New tasks start in `To Do`.
- Tasks move forward one column at a time: `To Do` -> `In Progress` -> `Done`.
- Tasks cannot skip columns.
- Tasks cannot move backward.
- Empty task titles are rejected.
- Duplicate task titles are rejected.
- The `In Progress` column has a WIP limit of two tasks.