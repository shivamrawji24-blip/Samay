"""Hard-constraint checking utilities."""
from collections import Counter

def count_hard_violations(problem, solution):
    violations = 0
    seen = set()
    teacher_hours = Counter()
    sessions = set()
    for p in solution.placements:
        if p.subject_code not in problem.subjects or p.batch_name not in problem.batches:
            violations += 1
            continue
        batch = problem.batches[p.batch_name]
        subj = problem.subjects[p.subject_code]
        room = problem.rooms.get(p.room_name)
        teacher = problem.teachers.get(p.teacher_name)
        if room is None or teacher is None:
            violations += 1
            continue
        if room.capacity < batch.strength: violations += 1
        if subj.type == "lab" and room.type != "lab": violations += 1
        if subj.type == "theory" and room.type != "classroom": violations += 1
        if p.start_period < 1 or p.start_period + p.duration - 1 > problem.time_structure.periods_per_day: violations += 1
        if batch.lunch_slot in p.occupied_periods: violations += 1
        if any(bp in p.occupied_periods for bp in problem.time_structure.break_periods): violations += 1
        if any(not teacher.is_available(p.day, period) for period in p.occupied_periods): violations += 1
        teacher_hours[p.teacher_name] += p.duration
        if p.session_id in sessions: violations += 1
        sessions.add(p.session_id)
        for period in p.occupied_periods:
            for resource in (("teacher", p.teacher_name), ("batch", p.batch_name), ("room", p.room_name)):
                key = (resource, p.day, period)
                if key in seen: violations += 1
                seen.add(key)
    for name, hours in teacher_hours.items():
        if hours > problem.teachers[name].max_weekly_load: violations += 1
    # Verify weekly session hours are represented.
    expected = {}
    for b_name, batch in problem.batches.items():
        for code in batch.subjects:
            subj = problem.subjects.get(code)
            if subj:
                expected[(b_name, code)] = subj.weekly_hours
    actual = Counter()
    for p in solution.placements: actual[(p.batch_name, p.subject_code)] += p.duration
    for key, hours in expected.items():
        if actual[key] != hours: violations += 1
    return violations
