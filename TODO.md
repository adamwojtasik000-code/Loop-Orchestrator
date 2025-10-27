## Developer TODO — Loop Orchestrator

This file is a developer-focused checklist for short-term work on the Loop Orchestrator project. Keep items small, actionable, and mark checkboxes as you complete them. Include short notes or commands where helpful.

### High priority

- [x] Time tracking enforcement
	- Note: original: "Time Tracking: Max time for task is to 3600s. Change tasks that are in..."
	- Action: Ensure tasks have a sane max runtime (default 3600s). Find tasks with timeouts > 3600s and decide whether to reduce, document, or allow exceptions.
	- Acceptance: automated check exists or a short doc entry explains the 3600s default.
	- Completed: 3600s default enforced with runtime guards and automated checks

### Implementation tasks

- [x] Audit task definitions for excessive timeouts
	- Files to check: search repository for `timeout`, `max_time`, or similar config fields.
	- Deliverable: list of tasks needing changes or justification.
	- Completed: No current config violations found, one historical task exceeded 3600s (26766s)

- [x] Add/adjust runtime enforcement
	- Implement a guard in the orchestrator that fails or warns when a task exceeds the configured global max (3600s) unless explicitly opt-out.
	- Tests: unit test simulating a long-running task and confirming enforcement behavior.
	- Completed: Runtime guard implemented with warnings and failure mechanisms

- [ ] Add automated CI check (optional)
	- CI step that scans configs for timeout values > 3600s and fails with instructions, or prints a warning with a review exemption link.

- [ ] Rewrite orchestrator.md to integrate with TODO.md system
	- Action: Update e:\Loop-Orchestrator-1\orchestrator.md to treat TODO.md as a core component: add TODO integration sections, document conventions (including the 3600s default), CI/test guidance, and ensure all references align with the TODO.md-centric workflow. Only modify orchestrator.md; do not change other files or folders.
	- Reason: Centralize runtime policy and developer workflow around TODO.md so the orchestrator can validate and reference documented exceptions.
	- Owner: @maintainer
	- Acceptance: PR updates only e:\Loop-Orchestrator-1\orchestrator.md; reviewers confirm the new TODO-centric sections exist, include 3600s default, and CI/tests reference TODO.md. Automated check or reviewer note present in PR description.


- [ ] Python based mcp server with full integration of roocode project.
