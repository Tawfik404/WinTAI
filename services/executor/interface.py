from typing import Protocol


class ExecutorService(Protocol):
    """Placeholder interface for future Windows command execution."""

    async def execute(self, command: str, args: list[str]) -> dict: ...
