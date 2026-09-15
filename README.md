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
add              Add a Kanban task
move             Move a Kanban task to the next column
board            Show the Kanban board
sprint-create    Create a Planning sprint
sprint-start     Start a sprint
sprint-task      Add a task to an Active sprint
sprint-complete  Complete a sprint
retro-add        Add a retrospective card
state            Show sprint state.json
help             Show commands
quit             Exit
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

Scrum lifecycle flow:

```text
Command: sprint-create
Sprint name: Sprint 1

Command: sprint-start
Sprint ID: sprint-1

Command: sprint-task
Sprint ID: sprint-1
Task title: Build booking flow
Task description: Let users reserve a desk

Command: sprint-complete
Sprint ID: sprint-1

Command: retro-add
Sprint ID: sprint-1
Category: Went Well
Card text: The sprint goal was clear
```

## Scrum Lifecycle Core

The sprint lifecycle validation rules are implemented in `planner_core.py`, with the initial persisted schema shown in `state.json`. These features are available from the main `kanban_cli.py` menu and can also be run directly from `planner_core.py`.

Run the planner with:

```bash
python planner_core.py
```

This opens a terminal menu for the five sprint and retrospective actions from the workshop:

```text
1. Create a sprint
2. Start a sprint
3. Add a task to an active sprint
4. Complete a sprint
5. Add a retrospective card
```

The planner enforces these rules:

- starting a second sprint is blocked while another sprint is Active
- unfinished tasks return to the backlog when a sprint is completed
- retro cards are rejected before completion and accepted after completion

You can run the showcase demo with:

```bash
python planner_core.py demo
```

You can also run each lifecycle step directly:

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