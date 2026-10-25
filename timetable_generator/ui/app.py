"""Streamlit Web Application for AI-Based Automated College Timetable Generator."""

import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt

from timetable_generator.core.data_loader import load_problem_from_json, problem_to_dict, dict_to_solution, solution_to_dict
from timetable_generator.core.validator import validate_solution
from timetable_generator.algorithms.plain_backtracking import PlainBacktrackingSolver
from timetable_generator.algorithms.improved_backtracking import ImprovedBacktrackingSolver
from timetable_generator.algorithms.min_conflicts import MinConflictsSolver
from timetable_generator.algorithms.simulated_annealing import SimulatedAnnealingSolver
from timetable_generator.algorithms.hybrid_solver import HybridSolver

st.set_page_config(page_title="AI Timetable Generator", page_icon="📅", layout="wide")

st.title("🤖 AI-Based Automated College Timetable Generator")
st.markdown("### Powered by Constraint Satisfaction Search & Local Search Algorithms")

# Sidebar - Dataset and Configuration
st.sidebar.header("1. Dataset Selection")
dataset_choice = st.sidebar.selectbox("Choose Dataset", ["Small Dataset (3 Classes)", "Large Dataset (8 Classes)", "Upload JSON File"])

if dataset_choice == "Small Dataset (3 Classes)":
    problem = load_problem_from_json("timetable_generator/data/small_dataset.json")
elif dataset_choice == "Large Dataset (8 Classes)":
    problem = load_problem_from_json("timetable_generator/data/large_dataset.json")
else:
    uploaded = st.sidebar.file_uploader("Upload JSON Config", type=["json"])
    if uploaded:
        data = json.load(uploaded)
        problem = load_problem_from_json("timetable_generator/data/small_dataset.json")
    else:
        problem = load_problem_from_json("timetable_generator/data/small_dataset.json")

st.sidebar.header("2. Algorithm & Parameters")
algo_name = st.sidebar.selectbox("Select Algorithm", [
    "Plain Backtracking CSP",
    "Improved Backtracking CSP (MRV+FC)",
    "Min-Conflicts Local Search",
    "Simulated Annealing (Bonus)",
    "Hybrid (CSP + Simulated Annealing)"
])

random_seed = st.sidebar.number_input("Random Seed", value=42, step=1)
run_btn = st.sidebar.button("🚀 Generate Timetable", type="primary")

# Initialize Session State
if "solution" not in st.session_state:
    st.session_state.solution = None
if "history" not in st.session_state:
    st.session_state.history = []
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []

if run_btn:
    with st.spinner(f"Running {algo_name}..."):
        if algo_name == "Plain Backtracking CSP":
            solver = PlainBacktrackingSolver(problem)
        elif algo_name == "Improved Backtracking CSP (MRV+FC)":
            solver = ImprovedBacktrackingSolver(problem)
        elif algo_name == "Min-Conflicts Local Search":
            solver = MinConflictsSolver(problem)
        elif algo_name == "Simulated Annealing (Bonus)":
            solver = SimulatedAnnealingSolver(problem)
        else:
            solver = HybridSolver(problem)

        result = solver.solve(seed=int(random_seed))

        if result.solution:
            st.session_state.solution = result.solution
            st.session_state.history = result.cost_history
            st.session_state.undo_stack = []
            st.success(f"Generation Complete! Status: {result.status} | Runtime: {result.runtime_seconds:.2f}s")
        else:
            st.error(f"Failed to generate timetable. Status: {result.status}")

# Results Display
if st.session_state.solution:
    solution = st.session_state.solution
    v_res = validate_solution(problem, solution)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", "FEASIBLE" if v_res.is_feasible else "INFEASIBLE")
    col2.metric("Hard Violations", v_res.hard_violation_count)
    col3.metric("Soft Penalty", v_res.soft_penalty_score)
    col4.metric("Total Cost", v_res.total_cost)

    if st.session_state.history:
        st.subheader("📈 Convergence Curve (Cost vs. Iterations)")
        fig, ax = plt.subplots(figsize=(8, 2.5))
        ax.plot(st.session_state.history, color="#1f77b4", lw=2)
        ax.set_xlabel("Iterations")
        ax.set_ylabel("Cost")
        st.pyplot(fig)

    st.markdown("---")
    st.header("📅 Timetable Grid Views")
    view_type = st.radio("View By:", ["Class / Batch", "Teacher", "Room"], horizontal=True)

    days = problem.time_structure.working_days
    periods = list(range(1, problem.time_structure.periods_per_day + 1))

    # Grid Display
    placements = solution.placements
    if view_type == "Class / Batch":
        b_sel = st.selectbox("Select Class", list(problem.batches.keys()))
        grid = pd.DataFrame(index=periods, columns=days)
        for d in days:
            for p in periods:
                match = [pl for pl in placements if pl.batch_name == b_sel and pl.day == d and p in pl.occupied_periods]
                grid.loc[p, d] = f"{match[0].subject_code} ({match[0].teacher_name})" if match else "Free"
        st.dataframe(grid, use_container_width=True)

    elif view_type == "Teacher":
        t_sel = st.selectbox("Select Teacher", list(problem.teachers.keys()))
        grid = pd.DataFrame(index=periods, columns=days)
        for d in days:
            for p in periods:
                match = [pl for pl in placements if pl.teacher_name == t_sel and pl.day == d and p in pl.occupied_periods]
                grid.loc[p, d] = f"{match[0].subject_code} [{match[0].batch_name}]" if match else "Free"
        st.dataframe(grid, use_container_width=True)

    else:
        r_sel = st.selectbox("Select Room", list(problem.rooms.keys()))
        grid = pd.DataFrame(index=periods, columns=days)
        for d in days:
            for p in periods:
                match = [pl for pl in placements if pl.room_name == r_sel and pl.day == d and p in pl.occupied_periods]
                grid.loc[p, d] = f"{match[0].subject_code} [{match[0].batch_name}]" if match else "Free"
        st.dataframe(grid, use_container_width=True)

    # Interactive Manual Editing
    st.markdown("---")
    st.header("✏️ Interactive Session Editor & Real-Time Validator")

    col_edit1, col_edit2 = st.columns([3, 1])

    with col_edit1:
        with st.form("edit_form"):
            sess_ids = [pl.session_id for pl in solution.placements]
            sel_sess_id = st.selectbox("Select Session to Reposition", sess_ids)
            curr_pl = next(pl for pl in solution.placements if pl.session_id == sel_sess_id)

            st.write(f"Current Placement: **{curr_pl.subject_code}** ({curr_pl.batch_name}) on **{curr_pl.day}**, Period **{curr_pl.start_period}** in **{curr_pl.room_name}**")

            new_day = st.selectbox("New Day", days, index=days.index(curr_pl.day))
            new_period = st.selectbox("New Start Period", periods, index=periods.index(curr_pl.start_period))
            new_room = st.selectbox("New Room", list(problem.rooms.keys()), index=list(problem.rooms.keys()).index(curr_pl.room_name))

            apply_edit = st.form_submit_button("Move Session & Audit Constraints")

            if apply_edit:
                # Save state for Undo
                st.session_state.undo_stack.append([p for p in solution.placements])

                # Update placement
                new_placements = []
                for pl in solution.placements:
                    if pl.session_id == sel_sess_id:
                        new_placements.append(type(pl)(
                            session_id=pl.session_id, batch_name=pl.batch_name, subject_code=pl.subject_code,
                            teacher_name=pl.teacher_name, room_name=new_room, day=new_day,
                            start_period=new_period, duration=pl.duration
                        ))
                    else:
                        new_placements.append(pl)

                st.session_state.solution.placements = new_placements
                st.rerun()

    with col_edit2:
        if st.button("↩️ Undo Last Edit", disabled=len(st.session_state.undo_stack) == 0):
            st.session_state.solution.placements = st.session_state.undo_stack.pop()
            st.rerun()

    # Exports
    st.markdown("---")
    st.header("📥 Export Options")
    export_df = pd.DataFrame([
        {
            "Session ID": pl.session_id, "Batch": pl.batch_name, "Subject": pl.subject_code,
            "Teacher": pl.teacher_name, "Room": pl.room_name, "Day": pl.day,
            "Start Period": pl.start_period, "Duration": pl.duration
        }
        for pl in solution.placements
    ])
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Schedule as CSV", csv_data, "timetable_schedule.csv", "text/csv")
