from timetable_generator.core.data_loader import load_problem_from_json
from timetable_generator.core.validator import validate_solution
from timetable_generator.core.models import TimetableSolution

def test_load_small_dataset():
    problem = load_problem_from_json("timetable_generator/data/small_dataset.json")
    assert len(problem.batches) == 3
    assert problem.time_structure.periods_per_day > 0

def test_empty_solution_is_not_feasible():
    problem = load_problem_from_json("timetable_generator/data/small_dataset.json")
    result = validate_solution(problem, TimetableSolution([], False))
    assert not result.is_feasible
