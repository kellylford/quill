# Runtime model

This baseline reflects the current implementation and the near-term PRD-aligned execution model.

## Current runtime

- Single UI thread (`wx.App` main loop) owns all widget interaction.
- Command execution is synchronous on the UI thread.
- Status announcements funnel through `platform.windows.sr_announce`.

## Planned runtime alignment (next phases)

- Background I/O tasks for open/save/backups/autosave.
- Compute pool for heavier operations (outline/statistics/spell-check on large documents).
- `wx.CallAfter` marshalling for all cross-thread UI updates.
- Async network operations for optional AI and URL ingestion behind explicit consent.

## Cancellation model

- `core.events.CancelToken` is the shared cancellation primitive.
- Long-running tasks should accept and check a token at safe boundaries.
