from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CancelToken:
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True

    def throw_if_cancelled(self) -> None:
        if self.cancelled:
            raise RuntimeError("Operation cancelled")
