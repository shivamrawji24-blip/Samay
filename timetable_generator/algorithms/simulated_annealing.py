"""Bonus Algorithm: Simulated Annealing Local Search."""

import time
import math
import random
from typing import List, Dict, Optional
from timetable_generator.core.models import TimetableProblem, TimetableSolution, SessionPlacement
from timetable_generator.core.scoring import calculate_cost
from timetable_generator.core.validator import validate_solution
from timetable_generator.algorithms.base_solver import SearchResult
from timetable_generator.algorithms.min_conflicts import MinConflictsSolver


class SimulatedAnnealingSolver:
    def __init__(self, problem: TimetableProblem, initial_temp: float = 500.0, cooling_rate: float = 0.98, max_steps: int = 1000):
        self.problem = problem
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.max_steps = max_steps

    def solve(self, seed: Optional[int] = None) -> SearchResult:
        if seed is not None:
            random.seed(seed)

        start_time = time.time()
        # Initialize using Min-Conflicts logic
        mc = MinConflictsSolver(self.problem, max_iterations=50)
        init_res = mc.solve(seed=seed)
        current_sol = init_res.solution

        current_cost = calculate_cost(self.problem, current_sol)
        best_sol = current_sol
        best_cost = current_cost
        temp = self.initial_temp
        cost_history = [current_cost]

        for step in range(self.max_steps):
            if best_cost == 0:
                break

            # Neighborhood move: swap two placements' slots
            placements = list(current_sol.placements)
            idx1, idx2 = random.sample(range(len(placements)), 2)

            p1, p2 = placements[idx1], placements[idx2]
            # Swap day, start_period, room
            new_p1 = SessionPlacement(p1.session_id, p1.batch_name, p1.subject_code, p1.teacher_name, p2.room_name, p2.day, p2.start_period, p1.duration)
            new_p2 = SessionPlacement(p2.session_id, p2.batch_name, p2.subject_code, p2.teacher_name, p1.room_name, p1.day, p1.start_period, p2.duration)

            placements[idx1] = new_p1
            placements[idx2] = new_p2
            cand_sol = TimetableSolution(placements=placements, is_complete=True)
            cand_cost = calculate_cost(self.problem, cand_sol)

            diff = cand_cost - current_cost
            if diff < 0 or random.random() < math.exp(-diff / max(temp, 1e-5)):
                current_sol = cand_sol
                current_cost = cand_cost
                if current_cost < best_cost:
                    best_sol = current_sol
                    best_cost = current_cost

            temp *= self.cooling_rate
            cost_history.append(current_cost)

        elapsed = time.time() - start_time
        v_res = validate_solution(self.problem, best_sol)
        return SearchResult(
            algorithm_name="Simulated Annealing", solution=best_sol, is_feasible=v_res.is_feasible,
            runtime_seconds=elapsed, nodes_expanded=self.max_steps, backtracks=0,
            hard_violations=v_res.hard_violation_count, soft_penalty=v_res.soft_penalty_score,
            total_cost=v_res.total_cost, status="SUCCESS" if v_res.is_feasible else "SUBOPTIMAL",
            cost_history=cost_history
        )
