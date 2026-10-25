"""Soft-constraint scoring; lower is better."""
from collections import defaultdict
from .constraints import count_hard_violations

def total_soft_penalty(problem, solution):
    by_batch_day = defaultdict(list)
    by_subject_day = defaultdict(set)
    for p in solution.placements:
        by_batch_day[(p.batch_name,p.day)].extend(p.occupied_periods)
        by_subject_day[(p.batch_name,p.subject_code)].add(p.day)
    penalty = 0
    for periods in by_batch_day.values():
        periods = sorted(set(periods))
        if periods:
            penalty += max(0, periods[-1]-periods[0]+1-len(periods))
    for days in by_subject_day.values():
        if len(days) < 2: penalty += 2
    return penalty

def calculate_cost(problem, solution):
    return 1000 * count_hard_violations(problem, solution) + total_soft_penalty(problem, solution)
