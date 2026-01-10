from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from task1.fcfs_sim import ScheduledOp


def schedule_to_dataframe(ops: Sequence[ScheduledOp]) -> pd.DataFrame:
    return pd.DataFrame([asdict(o) for o in ops]).sort_values(
        by=["machine_id", "start", "end", "job_id", "op_index"]
    )


def save_gantt(
    ops: Sequence[ScheduledOp],
    out_path: Path,
    *,
    title: str,
    num_machines: int,
    figsize: Tuple[int, int] = (10, 4),
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    by_machine: Dict[int, List[ScheduledOp]] = {}
    for op in ops:
        by_machine.setdefault(op.machine_id, []).append(op)
    for m in by_machine:
        by_machine[m].sort(key=lambda x: (x.start, x.end, x.job_id, x.op_index))

    fig, ax = plt.subplots(figsize=figsize)
    colors = plt.colormaps.get_cmap("tab10")

    y_ticks = []
    y_labels = []
    for m in range(num_machines):
        y = num_machines - 1 - m
        y_ticks.append(y)
        y_labels.append(f"M{m}")

        for op in by_machine.get(m, []):
            ax.barh(
                y=y,
                width=op.duration,
                left=op.start,
                height=0.6,
                color=colors(op.job_id % 10),
                edgecolor="black",
                linewidth=0.5,
            )
            ax.text(
                op.start + op.duration / 2,
                y,
                f"J{op.job_id}-{op.op_index}",
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("time")
    ax.set_title(title)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


