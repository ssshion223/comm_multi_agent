from dataclasses import dataclass
from typing import Any, TypedDict
@dataclass
class WorkflowState(TypedDict):
    ops_snapshot: Any
    route_result: Any
    error: str | None
    action: str

@dataclass(frozen=True)
class Decision:
    action: str