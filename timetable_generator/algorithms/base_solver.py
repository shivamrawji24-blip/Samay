"""Base data structures and interface for all timetable search algorithms."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from timetable_generator.core.models import TimetableProblem, TimetableSolution


@dataclass
class SearchResult:
    algorithm_name: str
    solution: Optional[TimetableSolution]
    is_feasible: bool
    runtime_seconds: float
    nodes_expanded: int
    backtracks: int
    hard_violations: int
    soft_penalty: int
    total_cost: int
    status: str  # "SUCCESS", "INFEASIBLE_PROVEN", "TIMEOUT", "MAX_ITERATIONS"
    cost_history: List[int] = field(default_factory=list)
