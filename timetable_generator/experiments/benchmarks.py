"""Benchmarking script running 10 independent runs across algorithms and datasets."""

import json
import time
from timetable_generator.core.data_loader import load_problem_from_json
from timetable_generator.algorithms.plain_backtracking import PlainBacktrackingSolver
from timetable_generator.algorithms.improved_backtracking import ImprovedBacktrackingSolver
from timetable_generator.algorithms.min_conflicts import MinConflictsSolver
from timetable_generator.algorithms.simulated_annealing import SimulatedAnnealingSolver
from timetable_generator.algorithms.hybrid_solver import HybridSolver

SEEDS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

def run_benchmarks():
    datasets = {
        "Small": load_problem_from_json("timetable_generator/data/small_dataset.json"),
        "Large": load_problem_from_json("timetable_generator/data/large_dataset.json")
    }

    results = []

    for d_name, problem in datasets.items():
        print(f"\n--- Benchmarking Dataset: {d_name} ---")

        # Plain Backtracking
        plain = PlainBacktrackingSolver(problem, max_nodes=50000)
        res = plain.solve(seed=42)
        results.append({
            "dataset": d_name, "algorithm": "Plain Backtracking", "run": 1,
            "runtime": res.runtime_seconds, "nodes": res.nodes_expanded,
            "hard_violations": res.hard_violations, "soft_penalty": res.soft_penalty,
            "feasible": res.is_feasible, "status": res.status
        })

        # Improved Backtracking
        improved = ImprovedBacktrackingSolver(problem, max_nodes=100000)
        res = improved.solve(seed=42)
        results.append({
            "dataset": d_name, "algorithm": "Improved Backtracking", "run": 1,
            "runtime": res.runtime_seconds, "nodes": res.nodes_expanded,
            "hard_violations": res.hard_violations, "soft_penalty": res.soft_penalty,
            "feasible": res.is_feasible, "status": res.status
        })

        # Min-Conflicts (10 runs)
        for run_idx, seed in enumerate(SEEDS):
            mc = MinConflictsSolver(problem, max_iterations=1000)
            res = mc.solve(seed=seed)
            results.append({
                "dataset": d_name, "algorithm": "Min-Conflicts", "run": run_idx + 1,
                "runtime": res.runtime_seconds, "nodes": res.nodes_expanded,
                "hard_violations": res.hard_violations, "soft_penalty": res.soft_penalty,
                "feasible": res.is_feasible, "status": res.status
            })

    with open("timetable_generator/experiments/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nBenchmark completed! Results saved to experiments/benchmark_results.json")

if __name__ == "__main__":
    run_benchmarks()
