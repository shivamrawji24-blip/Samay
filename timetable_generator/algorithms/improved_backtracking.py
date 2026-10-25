"""Algorithm B: Improved Backtracking CSP with MRV, Degree Heuristic, and Forward Checking."""

import time
import random
from typing import List, Dict, Tuple, Optional, Set
from timetable_generator.core.models import TimetableProblem, TimetableSolution, SessionPlacement
from timetable_generator.core.validator import validate_solution
from timetable_generator.algorithms.base_solver import SearchResult


class ImprovedBacktrackingSolver:
    def __init__(self, problem: TimetableProblem, max_nodes: int = 200000, max_time_seconds: float = 30.0):
        self.problem = problem
        self.max_nodes = max_nodes
        self.max_time_seconds = max_time_seconds
        self.nodes_expanded = 0
        self.backtracks = 0
        self.domain_prunings = 0

    def solve(self, seed: Optional[int] = None) -> SearchResult:
        if seed is not None:
            random.seed(seed)

        start_time = time.time()
        self.nodes_expanded = 0
        self.backtracks = 0
        self.domain_prunings = 0

        # Create session structures
        sessions = {}
        for b_name, batch in self.problem.batches.items():
            for s_code in batch.subjects:
                subj = self.problem.subjects.get(s_code)
                if not subj:
                    continue
                if subj.type == "lab":
                    num_labs = subj.weekly_hours // subj.lab_duration
                    for i in range(num_labs):
                        s_id = f"{b_name}_{s_code}_lab_{i+1}"
                        sessions[s_id] = {
                            "id": s_id, "batch": b_name, "subject": s_code,
                            "duration": subj.lab_duration, "type": "lab"
                        }
                else:
                    for i in range(subj.weekly_hours):
                        s_id = f"{b_name}_{s_code}_th_{i+1}"
                        sessions[s_id] = {
                            "id": s_id, "batch": b_name, "subject": s_code,
                            "duration": 1, "type": "theory"
                        }

        # Build initial domains
        domains: Dict[str, List[dict]] = {}
        for s_id, sess in sessions.items():
            b_name = sess["batch"]
            s_code = sess["subject"]
            subj = self.problem.subjects[s_code]
            batch = self.problem.batches[b_name]
            dur = sess["duration"]

            dom = []
            for day in self.problem.time_structure.working_days:
                for start_p in range(1, self.problem.time_structure.periods_per_day - dur + 2):
                    occ_periods = list(range(start_p, start_p + dur))
                    if batch.lunch_slot in occ_periods or any(bp in occ_periods for bp in self.problem.time_structure.break_periods):
                        continue

                    for r_name, room in self.problem.rooms.items():
                        if room.capacity < batch.strength:
                            continue
                        if subj.type == "lab" and room.type != "lab":
                            continue
                        if subj.type == "theory" and room.type != "classroom":
                            continue

                        for t_name, teacher in self.problem.teachers.items():
                            if s_code not in teacher.subjects:
                                continue
                            if any(not teacher.is_available(day, p) for p in occ_periods):
                                continue

                            dom.append({
                                "session_id": s_id,
                                "batch_name": b_name,
                                "subject_code": s_code,
                                "teacher_name": t_name,
                                "room_name": r_name,
                                "day": day,
                                "start_period": start_p,
                                "duration": dur
                            })
            domains[s_id] = dom

        assigned: Dict[str, dict] = {}
        unassigned: Set[str] = set(sessions.keys())

        # Degree calculation function
        def get_degree(var: str) -> int:
            sess_v = sessions[var]
            deg = 0
            for u in unassigned:
                if u == var:
                    continue
                sess_u = sessions[u]
                if sess_u["batch"] == sess_v["batch"]:
                    deg += 1
            return deg

        status = "INFEASIBLE_PROVEN"

        def backtrack() -> bool:
            nonlocal status
            self.nodes_expanded += 1

            if time.time() - start_time > self.max_time_seconds:
                status = "TIMEOUT"
                return False

            if self.nodes_expanded >= self.max_nodes:
                status = "MAX_NODES_REACHED"
                return False

            if not unassigned:
                status = "SUCCESS"
                return True

            # MRV Heuristic with Degree Heuristic Tie-Breaking
            var = min(unassigned, key=lambda v: (len(domains[v]), -get_degree(v)))
            unassigned.remove(var)

            for val in list(domains[var]):
                assigned[var] = val

                # Forward Checking with reversible pruning
                pruned = {}
                consistent = True
                occ_v = list(range(val["start_period"], val["start_period"] + val["duration"]))

                for u in list(unassigned):
                    pruned[u] = []
                    new_dom = []
                    for u_val in domains[u]:
                        occ_u = list(range(u_val["start_period"], u_val["start_period"] + u_val["duration"]))
                        # Check collision (Teacher, Batch, Room)
                        collision = (
                            (u_val["teacher_name"] == val["teacher_name"] and u_val["day"] == val["day"] and any(p in occ_v for p in occ_u)) or
                            (u_val["batch_name"] == val["batch_name"] and u_val["day"] == val["day"] and any(p in occ_v for p in occ_u)) or
                            (u_val["room_name"] == val["room_name"] and u_val["day"] == val["day"] and any(p in occ_v for p in occ_u))
                        )
                        if collision:
                            pruned[u].append(u_val)
                            self.domain_prunings += 1
                        else:
                            new_dom.append(u_val)

                    domains[u] = new_dom
                    if not domains[u]:
                        consistent = False
                        break

                if consistent and backtrack():
                    return True

                # Restore pruned domains
                for u, restored in pruned.items():
                    domains[u].extend(restored)

                del assigned[var]
                self.backtracks += 1

            unassigned.add(var)
            return False

        success = backtrack()
        elapsed = time.time() - start_time

        if success:
            placements = [
                SessionPlacement(
                    session_id=val["session_id"],
                    batch_name=val["batch_name"],
                    subject_code=val["subject_code"],
                    teacher_name=val["teacher_name"],
                    room_name=val["room_name"],
                    day=val["day"],
                    start_period=val["start_period"],
                    duration=val["duration"]
                )
                for val in assigned.values()
            ]
            sol = TimetableSolution(placements=placements, is_complete=True)
            v_res = validate_solution(self.problem, sol)
            return SearchResult(
                algorithm_name="Improved Backtracking CSP (MRV+FC)",
                solution=sol,
                is_feasible=v_res.is_feasible,
                runtime_seconds=elapsed,
                nodes_expanded=self.nodes_expanded,
                backtracks=self.backtracks,
                hard_violations=v_res.hard_violation_count,
                soft_penalty=v_res.soft_penalty_score,
                total_cost=v_res.total_cost,
                status=status
            )

        return SearchResult(
            algorithm_name="Improved Backtracking CSP (MRV+FC)",
            solution=None,
            is_feasible=False,
            runtime_seconds=elapsed,
            nodes_expanded=self.nodes_expanded,
            backtracks=self.backtracks,
            hard_violations=999,
            soft_penalty=999,
            total_cost=999000,
            status=status
        )
