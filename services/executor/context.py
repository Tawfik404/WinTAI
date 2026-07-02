from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ExecutionContext:
    tool_name: str = ""
    params: dict = field(default_factory=dict)
    timeout: float = 30.0
    on_complete: Callable | None = None
    on_error: Callable | None = None
