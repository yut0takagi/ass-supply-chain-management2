from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pandas as pd

from task1.fcfs_sim import FCFSSchedule, simulate_fcfs
from task1.jobshop_data import (
    JobshopInstance,
    instance_assignment_jobs,
    instance_custom_jobs,
    weight_patterns,
)
from task1.ortools_jobshop import OrtoolsResult, solve_makespan, solve_weighted_completion_sum
from task1.viz import save_gantt, schedule_to_dataframe


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    schedule_type: str  # "fcfs" | "opt_makespan" | "opt_weighted"
    objective: str
    objective_value: int
    makespan: int
    job_completion: List[int]
    ops_df: pd.DataFrame


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _summarize(schedule_type: str, objective: str, objective_value: int, makespan: int, job_completion: List[int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "schedule_type": schedule_type,
                "objective": objective,
                "objective_value": objective_value,
                "makespan": makespan,
                **{f"C_job{j}": c for j, c in enumerate(job_completion)},
            }
        ]
    )


def run_instance(instance: JobshopInstance, out_dir: Path, *, time_limit_s: float = 10.0) -> Dict[str, ScenarioResult]:
    _ensure_dir(out_dir)
    results: Dict[str, ScenarioResult] = {}

    # FCFS
    fcfs = simulate_fcfs(instance)
    df_fcfs = schedule_to_dataframe(fcfs.ops)
    df_fcfs.to_csv(out_dir / f"{instance.name}_fcfs_ops.csv", index=False)
    save_gantt(
        fcfs.ops,
        out_dir / f"{instance.name}_fcfs_gantt.png",
        title=f"{instance.name}: FCFS (makespan={fcfs.makespan})",
        num_machines=instance.num_machines,
    )
    results["fcfs"] = ScenarioResult(
        name=instance.name,
        schedule_type="fcfs",
        objective="makespan (derived)",
        objective_value=fcfs.makespan,
        makespan=fcfs.makespan,
        job_completion=fcfs.job_completion,
        ops_df=df_fcfs,
    )

    # OR-Tools: makespan minimize
    opt_ms = solve_makespan(instance, time_limit_s=time_limit_s)
    df_ms = schedule_to_dataframe(opt_ms.ops)
    df_ms.to_csv(out_dir / f"{instance.name}_opt_makespan_ops.csv", index=False)
    save_gantt(
        opt_ms.ops,
        out_dir / f"{instance.name}_opt_makespan_gantt.png",
        title=f"{instance.name}: OR-Tools makespan-min (makespan={opt_ms.makespan})",
        num_machines=instance.num_machines,
    )
    results["opt_makespan"] = ScenarioResult(
        name=instance.name,
        schedule_type="opt_makespan",
        objective=opt_ms.objective_name,
        objective_value=opt_ms.objective_value,
        makespan=opt_ms.makespan,
        job_completion=opt_ms.job_completion,
        ops_df=df_ms,
    )

    # OR-Tools: weighted completion sum (3 patterns)
    for label, weights in weight_patterns(instance.num_jobs):
        opt_w = solve_weighted_completion_sum(instance, weights, time_limit_s=time_limit_s)
        df_w = schedule_to_dataframe(opt_w.ops)
        df_w.to_csv(out_dir / f"{instance.name}_opt_weighted_{label}_ops.csv", index=False)
        save_gantt(
            opt_w.ops,
            out_dir / f"{instance.name}_opt_weighted_{label}_gantt.png",
            title=f"{instance.name}: OR-Tools weighted ({label}) (obj={opt_w.objective_value}, makespan={opt_w.makespan})",
            num_machines=instance.num_machines,
        )
        results[f"opt_weighted_{label}"] = ScenarioResult(
            name=instance.name,
            schedule_type=f"opt_weighted_{label}",
            objective=f"{opt_w.objective_name} weights={list(weights)}",
            objective_value=opt_w.objective_value,
            makespan=opt_w.makespan,
            job_completion=opt_w.job_completion,
            ops_df=df_w,
        )

    # Summary CSV
    summary_rows = []
    for k, r in results.items():
        summary_rows.append(
            _summarize(
                schedule_type=r.schedule_type,
                objective=r.objective,
                objective_value=r.objective_value,
                makespan=r.makespan,
                job_completion=r.job_completion,
            )
        )
    pd.concat(summary_rows, ignore_index=True).to_csv(out_dir / f"{instance.name}_summary.csv", index=False)

    return results


def main() -> None:
    base_out = Path("task1_outputs")
    _ensure_dir(base_out)

    for inst in [instance_assignment_jobs(), instance_custom_jobs()]:
        out_dir = base_out / inst.name
        run_instance(inst, out_dir, time_limit_s=10.0)

    print(f"Saved outputs under: {base_out.resolve()}")


if __name__ == "__main__":
    main()


