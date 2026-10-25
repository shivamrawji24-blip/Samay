"""JSON serialization and loading for timetable problems."""
import json
from pathlib import Path
from .models import Subject, Batch, Room, Teacher, TimeStructure, TimetableProblem, TimetableSolution, SessionPlacement

def load_problem_from_json(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    subjects = {x["code"]: Subject(**x) for x in data["subjects"]}
    batches = {x["name"]: Batch(**x) for x in data["batches"]}
    rooms = {x["name"]: Room(**x) for x in data["rooms"]}
    teachers = {x["name"]: Teacher(**x) for x in data["teachers"]}
    ts = TimeStructure(**data["time_structure"])
    return TimetableProblem(subjects, batches, rooms, teachers, ts)

def problem_to_dict(problem):
    return {
        "subjects": [vars(x) for x in problem.subjects.values()],
        "batches": [vars(x) for x in problem.batches.values()],
        "rooms": [vars(x) for x in problem.rooms.values()],
        "teachers": [{"name": x.name, "subjects": x.subjects, "max_weekly_load": x.max_weekly_load, "unavailable": x.unavailable} for x in problem.teachers.values()],
        "time_structure": vars(problem.time_structure)
    }

def dict_to_solution(data):
    return TimetableSolution([SessionPlacement(**p) for p in data["placements"]], data.get("is_complete", True))

def solution_to_dict(solution):
    return {"is_complete": solution.is_complete, "placements": [vars(p) for p in solution.placements]}
