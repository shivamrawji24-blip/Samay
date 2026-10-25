"""Algorithm C: Min-Conflicts Local Search with Plateau Escape and Reproducible Seeds."""

import time
import random
from typing import List, Dict, Tuple, Optional
from timetable_generator.core.models import TimetableProblem, TimetableSolution, SessionPlacement
from timetable_generator.core.constraints import count_hard_violations
from timetable_generator.core.scoring import calculate_cost, total_soft_penalty
from timetable_generator.core.validator import validate_solution
from timetable_generator.algorithms.base_solver import SearchResult


class MinConflictsSolver:
    def __init__(self, problem: TimetableProblem, max_iterations: int = 1500, random_walk_prob: float = 0.1):
        self.problem = problem
        self.max_iterations = max_iterations
        self.random_walk_prob = random_walk_prob

    def solve(self, seed: Optional[int] = None) -> SearchResult:
        if seed is not None:
            random.seed(seed)

        start_time = time.time()
        cost_history = []

        # Build sessions and candidate domains
        sessions = []
        domains = {}

        for b_name, batch in self.problem.batches.items():
            for s_code in batch.subjects:
                subj = self.problem.subjects.get(s_code)
                if not subj:
                    continue
                if subj.type == "lab":
                    num_labs = subj.weekly_hours // subj.lab_duration
                    for i in range(num_labs):
                        s_id = f"{b_name}_{s_code}_lab_{i+1}"
                        sessions.append({"id": s_id, "batch": b_name, "subject": s_code, "duration": subj.lab_duration})
                else:
                    for i in range(subj.weekly_hours):
                        s_id = f"{b_name}_{s_code}_th_{i+1}"
                        sessions.append({"id": s_id, "batch": b_name, "subject": s_code, "duration": 1})

        for sess in sessions:
            s_id = sess["id"]
            b_name = sess["batch"]
            s_code = sess["subject"]
            subj = self.problem.subjects[s_code]
            batch = self.problem.batches[b_name]
            dur = sess["duration"]

            dom = []
            for day in self.problem.time_structure.working_days:
                for start_p in range(1, self.problem.time_structure.periods_per_day - dur + 2):
                    occ = list(range(start_p, start_p + dur))
                    if batch.lunch_slot in occ or any(bp in occ for bp in self.problem.time_structure.break_periods):
                        continue
                    for r_name, room in self.problem.rooms.items():
                        if room.capacity < batch.strength or (subj.type == "lab" and room.type != "lab") or (subj.type == "theory" and room.type != "classroom"):
                            continue
                        for t_name, teacher in self.problem.teachers.items():
                            if s_code not in teacher.subjects or any(not teacher.is_available(day, p) for p in occ):
                                continue
                            dom.append({
                                "session_id": s_id, "batch_name": b_name, "subject_code": s_code,
                                "teacher_name": t_name, "room_name": r_name, "day": day,
                                "start_period": start_p, "duration": dur
                            })
            domains[s_id] = dom

        # Complete initial random assignment
        current_assignment: Dict[str, dict] = {}
        for sess in sessions:
            s_id = sess["id"]
            current_assignment[s_id] = random.choice(domains[s_id])

        def to_solution(assign_map: Dict[str, dict]) -> TimetableSolution:
            placements = [
                SessionPlacement(
                    session_id=v["session_id"], batch_name=v["batch_name"], subject_code=v["subject_code"],
                    teacher_name=v["teacher_name"], room_name=v["room_name"], day=v["day"],
                    start_period=v["start_period"], duration=v["duration"]
                )
                for v in assign_map.values()
            ]
            return TimetableSolution(placements=placements, is_complete=True)

        best_sol = to_solution(current_assignment)
        best_cost = calculate_cost(self.problem, best_sol)
        cost_history.append(best_cost)

        for step in range(self.max_iterations):
            curr_sol = to_solution(current_assignment)
            h_count = count_hard_violations(self.problem, curr_sol)
            curr_cost = calculate_cost(self.problem, curr_sol)
            cost_history.append(curr_cost)

            if h_count == 0:
                elapsed = time.time() - start_time
                v_res = validate_solution(self.problem, curr_sol)
                return SearchResult(
                    algorithm_name="Min-Conflicts Local Search", solution=curr_sol, is_feasible=True,
                    runtime_seconds=elapsed, nodes_expanded=step, backtracks=0,
                    hard_violations=0, soft_penalty=v_res.soft_penalty_score, total_cost=v_res.total_cost,
                    status="SUCCESS", cost_history=cost_history
                )

            # Pick a conflicted variable
            conflicted = []
            vals = list(current_assignment.values())
            for i, v1 in enumerate(vals):
                occ1 = list(range(v1["start_period"], v1["start_period"] + v1["duration"]))
                for j, v2 in enumerate(vals):
                    if i >= j: continue
                    occ2 = list(range(v2["start_period"], v2["start_period"] + v2["duration"]))
                    if v1["day"] == v2["day"] and any(p in occ1 for p in occ2):
                        if v1["teacher_name"] == v2["teacher_name"] or v1["batch_name"] == v2["batch_name"] or v1["room_name"] == v2["room_name"]:
                            conflicted.append(v1["session_id"])
                            break

            if not conflicted:
                conflicted = list(current_assignment.keys())

            chosen_var = random.choice(conflicted)

            # Random walk plateau escape
            if random.random() < self.random_walk_prob:
                current_assignment[chosen_var] = random.choice(domains[chosen_var])
            else:
                # Value selection minimizing cost
                best_val = current_assignment[chosen_var]
                min_v_cost = float('inf')

                for val in domains[chosen_var]:
                    current_assignment[chosen_var] = val
                    test_sol = to_solution(current_assignment)
                    c = calculate_cost(self.problem, test_sol)
                    if c < min_v_cost:
                        min_v_cost = c
                        best_val = val

                current_assignment[chosen_var] = best_val

            if curr_cost < best_cost:
                best_cost = curr_cost
                best_sol = curr_sol

        elapsed = time.time() - start_time
        v_res = validate_solution(self.problem, best_sol)
        return SearchResult(
            algorithm_name="Min-Conflicts Local Search", solution=best_sol, is_feasible=v_res.is_feasible,
            runtime_seconds=elapsed, nodes_expanded=self.max_iterations, backtracks=0,
            hard_violations=v_res.hard_violation_count, soft_penalty=v_res.soft_penalty_score,
            total_cost=v_res.total_cost, status="MAX_ITERATIONS" if not v_res.is_feasible else "SUCCESS",
            cost_history=cost_history
        )
