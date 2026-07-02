from typing import Protocol


class ExecutorService(Protocol):
    def execute(self, tool_name: str, params: dict) -> dict: ...
