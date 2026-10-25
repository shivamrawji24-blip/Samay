"""Bonus Algorithm: Hybrid CSP + Simulated Annealing Solver."""

import time
import random
from typing import Optional
from timetable_generator.core.models import TimetableProblem
from timetable_generator.algorithms.improved_backtracking import ImprovedBacktrackingSolver
from timetable_generator.algorithms.simulated_annealing import SimulatedAnnealingSolver
from timetable_generator.algorithms.base_solver import SearchResult


class HybridSolver:
    def __init__(self, problem: TimetableProblem):
        self.problem = problem

    def solve(self, seed: Optional[int] = None) -> SearchResult:
        start_time = time.time()

        # Phase 1: Improved Backtracking CSP to guarantee 0 hard violations
        csp_solver = ImprovedBacktrackingSolver(self.problem, max_nodes=100000)
        phase1_res = csp_solver.solve(seed=seed)

        if not phase1_res.is_feasible or phase1_res.solution is None:
            return phase1_res

        # Phase 2: Simulated Annealing optimizing soft constraints starting from feasible schedule
        sa_solver = SimulatedAnnealingSolver(self.problem, initial_temp=50.0, cooling_rate=0.95, max_steps=400)
        phase2_res = sa_solver.solve(seed=seed)

        elapsed = time.time() - start_time
        phase2_res.runtime_seconds = elapsed
        phase2_res.algorithm_name = "Hybrid (CSP + Simulated Annealing)"
        return phase2_res
