"""Solution validation and cost reporting."""
from dataclasses import dataclass
from .constraints import count_hard_violations
from .scoring import total_soft_penalty

@dataclass
class ValidationResult:
    is_feasible: bool
    hard_violation_count: int
    soft_penalty_score: int
    total_cost: int

def validate_solution(problem, solution):
    hard = count_hard_violations(problem, solution)
    soft = total_soft_penalty(problem, solution)
    return ValidationResult(hard == 0, hard, soft, hard * 1000 + soft)
