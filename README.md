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

Run the showcase demo with:

```bash
python planner_core.py demo
```

The demo shows:

- starting a second sprint is blocked while another sprint is Active
- unfinished tasks return to the backlog when a sprint is completed
- retro cards are rejected before completion and accepted after completion

You can also run each lifecycle step yourself:

```bash
python planner_core.py create-sprint "Sprint 1"
python planner_core.py start-sprint sprint-1
python planner_core.py add-task sprint-1 "Build booking flow" "Let users reserve a desk"
python planner_core.py set-task-status task-1 "Done"
python planner_core.py complete-sprint sprint-1
python planner_core.py add-retro sprint-1 "Went Well" "The sprint goal was clear"
python planner_core.py show
```

Tasks can only be added directly to an Active sprint. Retrospective categories must be exactly `Went Well`, `To Improve`, or `Action Item`.