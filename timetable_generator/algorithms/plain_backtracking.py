"""Algorithm A: Plain Backtracking CSP without search heuristics."""

import time
import random
from typing import List, Dict, Tuple, Optional
from timetable_generator.core.models import TimetableProblem, TimetableSolution, SessionPlacement
from timetable_generator.core.validator import validate_solution
from timetable_generator.algorithms.base_solver import SearchResult


class PlainBacktrackingSolver:
    def __init__(self, problem: TimetableProblem, max_nodes: int = 100000, max_time_seconds: float = 30.0):
        self.problem = problem
        self.max_nodes = max_nodes
        self.max_time_seconds = max_time_seconds
        self.nodes_expanded = 0
        self.backtracks = 0

    def solve(self, seed: Optional[int] = None) -> SearchResult:
        if seed is not None:
            random.seed(seed)

        start_time = time.time()
        self.nodes_expanded = 0
        self.backtracks = 0

        # Build variable session list
        sessions = []
        for b_name, batch in self.problem.batches.items():
            for s_code in batch.subjects:
                subj = self.problem.subjects.get(s_code)
                if not subj:
                    continue
                if subj.type == "lab":
                    num_labs = subj.weekly_hours // subj.lab_duration
                    for i in range(num_labs):
                        sessions.append({
                            "id": f"{b_name}_{s_code}_lab_{i+1}",
                            "batch": b_name,
                            "subject": s_code,
                            "duration": subj.lab_duration,
                            "type": "lab"
                        })
                else:
                    for i in range(subj.weekly_hours):
                        sessions.append({
                            "id": f"{b_name}_{s_code}_th_{i+1}",
                            "batch": b_name,
                            "subject": s_code,
                            "duration": 1,
                            "type": "theory"
                        })

        # Static variable ordering (no heuristics)
        # Static domain generation (no MRV / no FC)
        domains = {}
        for sess in sessions:
            b_name = sess["batch"]
            s_code = sess["subject"]
            subj = self.problem.subjects[s_code]
            batch = self.problem.batches[b_name]
            dur = sess["duration"]

            dom = []
            for day in self.problem.time_structure.working_days:
                for start_p in range(1, self.problem.time_structure.periods_per_day - dur + 2):
                    occ_periods = list(range(start_p, start_p + dur))
                    if batch.lunch_slot in occ_periods:
                        continue
                    if any(bp in occ_periods for bp in self.problem.time_structure.break_periods):
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
                                "session_id": sess["id"],
                                "batch_name": b_name,
                                "subject_code": s_code,
                                "teacher_name": t_name,
                                "room_name": r_name,
                                "day": day,
                                "start_period": start_p,
                                "duration": dur
                            })
            domains[sess["id"]] = dom

        teacher_busy = set()
        batch_busy = set()
        room_busy = set()
        teacher_hours = {t: 0 for t in self.problem.teachers}

        assignment = []
        status = "INFEASIBLE_PROVEN"

        def backtrack(idx: int) -> bool:
            nonlocal status
            self.nodes_expanded += 1

            if time.time() - start_time > self.max_time_seconds:
                status = "TIMEOUT"
                return False

            if self.nodes_expanded >= self.max_nodes:
                status = "MAX_NODES_REACHED"
                return False

            if idx == len(sessions):
                status = "SUCCESS"
                return True

            sess_id = sessions[idx]["id"]
            dur = sessions[idx]["duration"]

            for val in domains[sess_id]:
                t_name = val["teacher_name"]
                b_name = val["batch_name"]
                r_name = val["room_name"]
                day = val["day"]
                start_p = val["start_period"]
                occ_periods = list(range(start_p, start_p + dur))

                if teacher_hours[t_name] + dur > self.problem.teachers[t_name].max_weekly_load:
                    continue

                if any((t_name, day, p) in teacher_busy or
                       (b_name, day, p) in batch_busy or
                       (r_name, day, p) in room_busy for p in occ_periods):
                    continue

                # Make assignment
                for p in occ_periods:
                    teacher_busy.add((t_name, day, p))
                    batch_busy.add((b_name, day, p))
                    room_busy.add((r_name, day, p))
                teacher_hours[t_name] += dur

                placement = SessionPlacement(
                    session_id=sess_id,
                    batch_name=b_name,
                    subject_code=val["subject_code"],
                    teacher_name=t_name,
                    room_name=r_name,
                    day=day,
                    start_period=start_p,
                    duration=dur
                )
                assignment.append(placement)

                if backtrack(idx + 1):
                    return True

                # Undo assignment
                assignment.pop()
                teacher_hours[t_name] -= dur
                for p in occ_periods:
                    teacher_busy.remove((t_name, day, p))
                    batch_busy.remove((b_name, day, p))
                    room_busy.remove((r_name, day, p))
                self.backtracks += 1

            return False

        success = backtrack(0)
        elapsed = time.time() - start_time

        solution = TimetableSolution(placements=assignment, is_complete=success) if success else None
        if solution:
            v_res = validate_solution(self.problem, solution)
            return SearchResult(
                algorithm_name="Plain Backtracking CSP",
                solution=solution,
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
            algorithm_name="Plain Backtracking CSP",
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
