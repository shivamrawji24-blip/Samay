# AI-Based Automated College Timetable Generator

## Quick start (Windows)
1. Install Python 3.10 or newer.
2. Extract this ZIP and open a terminal in the extracted folder.
3. Run `python -m venv .venv`
4. Activate it: ` .\.venv\Scripts\Activate.ps1`
5. Install dependencies: `pip install -r requirements.txt`
6. Launch: `python -m streamlit run timetable_generator/ui/app.py`

Choose a dataset and algorithm in the sidebar. The project includes CSP backtracking, MRV/forward checking, min-conflicts, simulated annealing, hybrid solver, CSV export, benchmark script, and PDF report generation.

## Notes
This ZIP reconstructs the files present in the supplied project text and adds core data models, loaders, scoring, validation, sample datasets, and a small smoke-test suite so the package structure is complete. Benchmark figures in the report template are illustrative values from the supplied text, not independently verified experimental results.
