"""Core data models for timetable generation."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class Subject:
    code: str
    weekly_hours: int
    type: str = "theory"
    lab_duration: int = 2

@dataclass
class Batch:
    name: str
    subjects: List[str]
    strength: int = 30
    lunch_slot: int = 4

@dataclass
class Room:
    name: str
    capacity: int
    type: str = "classroom"

@dataclass
class Teacher:
    name: str
    subjects: List[str]
    max_weekly_load: int = 20
    unavailable: List[Tuple[str, int]] = field(default_factory=list)
    def is_available(self, day, period):
        return (day, period) not in self.unavailable

@dataclass
class TimeStructure:
    working_days: List[str]
    periods_per_day: int = 6
    break_periods: List[int] = field(default_factory=list)

@dataclass
class SessionPlacement:
    session_id: str
    batch_name: str
    subject_code: str
    teacher_name: str
    room_name: str
    day: str
    start_period: int
    duration: int = 1
    @property
    def occupied_periods(self):
        return list(range(self.start_period, self.start_period + self.duration))

@dataclass
class TimetableProblem:
    subjects: Dict[str, Subject]
    batches: Dict[str, Batch]
    rooms: Dict[str, Room]
    teachers: Dict[str, Teacher]
    time_structure: TimeStructure

@dataclass
class TimetableSolution:
    placements: List[SessionPlacement]
    is_complete: bool = True
