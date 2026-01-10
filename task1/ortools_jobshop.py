from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from ortools.sat.python import cp_model

from task1.fcfs_sim import ScheduledOp
from task1.jobshop_data import JobshopInstance


@dataclass(frozen=True)
class OrtoolsResult:
    instance_name: str
    ops: List[ScheduledOp]
    objective_name: str
    objective_value: int
    makespan: int
    job_completion: List[int]
    status: str


def _horizon(instance: JobshopInstance) -> int:
    return sum(d for job in instance.jobs for _m, d in job)


def solve_makespan(
    instance: JobshopInstance,
    *,
    time_limit_s: float = 10.0,
) -> OrtoolsResult:
    """メイクスパン最小のジョブショップ最適化（CP-SAT）。"""
    model = cp_model.CpModel()
    horizon = _horizon(instance)

    # Variables
    starts: List[List[cp_model.IntVar]] = []
    ends: List[List[cp_model.IntVar]] = []
    intervals: List[List[cp_model.IntervalVar]] = []

    for j, job in enumerate(instance.jobs):
        s_row: List[cp_model.IntVar] = []
        e_row: List[cp_model.IntVar] = []
        i_row: List[cp_model.IntervalVar] = []
        for o, (_m, dur) in enumerate(job):
            s = model.new_int_var(0, horizon, f"s_{j}_{o}")
            e = model.new_int_var(0, horizon, f"e_{j}_{o}")
            itv = model.new_interval_var(s, dur, e, f"int_{j}_{o}")
            s_row.append(s)
            e_row.append(e)
            i_row.append(itv)
        starts.append(s_row)
        ends.append(e_row)
        intervals.append(i_row)

    # Precedence constraints (within each job)
    for j, job in enumerate(instance.jobs):
        for o in range(len(job) - 1):
            model.add(starts[j][o + 1] >= ends[j][o])

    # Machine no-overlap constraints
    machine_to_intervals: List[List[cp_model.IntervalVar]] = [[] for _ in range(instance.num_machines)]
    for j, job in enumerate(instance.jobs):
        for o, (m, _dur) in enumerate(job):
            machine_to_intervals[m].append(intervals[j][o])
    for m in range(instance.num_machines):
        model.add_no_overlap(machine_to_intervals[m])

    # Makespan variable
    makespan = model.new_int_var(0, horizon, "makespan")
    job_completion_vars: List[cp_model.IntVar] = []
    for j, job in enumerate(instance.jobs):
        c = ends[j][len(job) - 1]
        job_completion_vars.append(c)
    model.add_max_equality(makespan, job_completion_vars)
    model.minimize(makespan)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)

    status_name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return OrtoolsResult(
            instance_name=instance.name,
            ops=[],
            objective_name="makespan",
            objective_value=-1,
            makespan=-1,
            job_completion=[],
            status=status_name,
        )

    ops: List[ScheduledOp] = []
    job_completion: List[int] = []
    for j, job in enumerate(instance.jobs):
        for o, (m, dur) in enumerate(job):
            s = int(solver.value(starts[j][o]))
            e = int(solver.value(ends[j][o]))
            ops.append(ScheduledOp(job_id=j, op_index=o, machine_id=m, start=s, end=e, duration=dur))
        job_completion.append(int(solver.value(ends[j][len(job) - 1])))

    return OrtoolsResult(
        instance_name=instance.name,
        ops=sorted(ops, key=lambda x: (x.start, x.machine_id, x.job_id, x.op_index)),
        objective_name="makespan",
        objective_value=int(solver.value(makespan)),
        makespan=int(solver.value(makespan)),
        job_completion=job_completion,
        status=status_name,
    )


def solve_weighted_completion_sum(
    instance: JobshopInstance,
    weights: Sequence[int],
    *,
    time_limit_s: float = 10.0,
) -> OrtoolsResult:
    """
    重み付き完了時刻和（Σ w_j * C_j）最小の最適化。
    ※ Jobshopなので「各ジョブの最終工程の終了時刻」を C_j とする。
    """
    if len(weights) != instance.num_jobs:
        raise ValueError("weights length must equal number of jobs")

    model = cp_model.CpModel()
    horizon = _horizon(instance)

    starts: List[List[cp_model.IntVar]] = []
    ends: List[List[cp_model.IntVar]] = []
    intervals: List[List[cp_model.IntervalVar]] = []

    for j, job in enumerate(instance.jobs):
        s_row: List[cp_model.IntVar] = []
        e_row: List[cp_model.IntVar] = []
        i_row: List[cp_model.IntervalVar] = []
        for o, (_m, dur) in enumerate(job):
            s = model.new_int_var(0, horizon, f"s_{j}_{o}")
            e = model.new_int_var(0, horizon, f"e_{j}_{o}")
            itv = model.new_interval_var(s, dur, e, f"int_{j}_{o}")
            s_row.append(s)
            e_row.append(e)
            i_row.append(itv)
        starts.append(s_row)
        ends.append(e_row)
        intervals.append(i_row)

    for j, job in enumerate(instance.jobs):
        for o in range(len(job) - 1):
            model.add(starts[j][o + 1] >= ends[j][o])

    machine_to_intervals: List[List[cp_model.IntervalVar]] = [[] for _ in range(instance.num_machines)]
    for j, job in enumerate(instance.jobs):
        for o, (m, _dur) in enumerate(job):
            machine_to_intervals[m].append(intervals[j][o])
    for m in range(instance.num_machines):
        model.add_no_overlap(machine_to_intervals[m])

    job_completion_vars: List[cp_model.IntVar] = []
    weighted_terms: List[cp_model.LinearExpr] = []
    for j, job in enumerate(instance.jobs):
        c = ends[j][len(job) - 1]
        job_completion_vars.append(c)
        weighted_terms.append(int(weights[j]) * c)

    obj = sum(weighted_terms)
    model.minimize(obj)

    # 参考として makespan も計算して返す
    makespan = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(makespan, job_completion_vars)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)

    status_name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return OrtoolsResult(
            instance_name=instance.name,
            ops=[],
            objective_name="weighted_completion_sum",
            objective_value=-1,
            makespan=-1,
            job_completion=[],
            status=status_name,
        )

    ops: List[ScheduledOp] = []
    job_completion: List[int] = []
    for j, job in enumerate(instance.jobs):
        for o, (m, dur) in enumerate(job):
            s = int(solver.value(starts[j][o]))
            e = int(solver.value(ends[j][o]))
            ops.append(ScheduledOp(job_id=j, op_index=o, machine_id=m, start=s, end=e, duration=dur))
        job_completion.append(int(solver.value(ends[j][len(job) - 1])))

    return OrtoolsResult(
        instance_name=instance.name,
        ops=sorted(ops, key=lambda x: (x.start, x.machine_id, x.job_id, x.op_index)),
        objective_name="weighted_completion_sum",
        objective_value=int(solver.value(obj)),
        makespan=int(solver.value(makespan)),
        job_completion=job_completion,
        status=status_name,
    )


