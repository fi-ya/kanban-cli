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
backlog-task     Create an unassigned backlog task
sprint-assign    Assign a backlog task to an Active sprint
points           Assign Fibonacci story points
dor              Mark a DoR checklist item complete
dod              Mark a DoD checklist item complete
status           Move a task to a new column
block            Block a task
unblock          Unblock a task
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
Story points (1, 2, 3, 5, 8, 13): 5
Is 'clear_user_story' complete? (y/n): y
Is 'acceptance_criteria' complete? (y/n): y
Is 'small_enough' complete? (y/n): y

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
- story points must be Fibonacci values: `1`, `2`, `3`, `5`, `8`, or `13`
- backlog tasks cannot enter a sprint until story points and every DoR item are complete
- blocked tasks cannot move columns until they are manually unblocked
- tasks cannot move to `Done` until every DoD item is complete

You can run the showcase demo with:

```bash
python planner_core.py demo
```

You can also run each lifecycle step directly:

```bash
python planner_core.py create-sprint "Sprint 1"
python planner_core.py start-sprint sprint-1
python planner_core.py create-task "Build booking flow" "Let users reserve a desk"
python planner_core.py set-points task-1 5
python planner_core.py mark-dor task-1 clear_user_story
python planner_core.py mark-dor task-1 acceptance_criteria
python planner_core.py mark-dor task-1 small_enough
python planner_core.py assign-task task-1 sprint-1
python planner_core.py block-task task-1
python planner_core.py unblock-task task-1
python planner_core.py set-task-status task-1 "In Progress"
python planner_core.py mark-dod task-1 code_complete
python planner_core.py mark-dod task-1 tests_pass
python planner_core.py mark-dod task-1 reviewed
python planner_core.py set-task-status task-1 "Done"
python planner_core.py complete-sprint sprint-1
python planner_core.py add-retro sprint-1 "Went Well" "The sprint goal was clear"
python planner_core.py show
```

Tasks can only be added directly to an Active sprint after passing the same estimation and DoR checks. Retrospective categories must be exactly `Went Well`, `To Improve`, or `Action Item`.

## Task Quality Gates

Each task stored in `state.json` can include:

```json
{
	"id": "task-1",
	"title": "Build booking flow",
	"description": "Let users reserve a desk",
	"status": "To Do",
	"sprint_id": null,
	"story_points": 5,
	"blocked": false,
	"dor": {
		"clear_user_story": true,
		"acceptance_criteria": true,
		"small_enough": true
	},
	"dod": {
		"code_complete": true,
		"tests_pass": true,
		"reviewed": true
	}
}
```