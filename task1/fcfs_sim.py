from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Dict, List, Optional, Tuple

from task1.jobshop_data import JobshopInstance


@dataclass(frozen=True)
class ScheduledOp:
    job_id: int
    op_index: int
    machine_id: int
    start: int
    end: int
    duration: int


@dataclass(frozen=True)
class FCFSSchedule:
    instance_name: str
    ops: List[ScheduledOp]
    makespan: int
    job_completion: List[int]

    def by_machine(self) -> Dict[int, List[ScheduledOp]]:
        out: Dict[int, List[ScheduledOp]] = {}
        for op in self.ops:
            out.setdefault(op.machine_id, []).append(op)
        for m in out:
            out[m].sort(key=lambda x: (x.start, x.end, x.job_id, x.op_index))
        return out


def simulate_fcfs(instance: JobshopInstance) -> FCFSSchedule:
    """
    FCFS: 各機械の待ち行列に「到着した順」で処理を割り当てる。
    - 到着時刻 = 前工程が終わって次工程の機械に入った時刻
    - 同一到着時刻のタイブレーク: job_id, op_index
    実装は離散イベントシミュレーション（工程完了イベント）で行う。
    """

    num_jobs = instance.num_jobs
    num_machines = instance.num_machines

    # 次に処理すべき工程インデックス（各ジョブ）
    next_op = [0] * num_jobs

    # 機械の空き時刻
    machine_free = [0] * num_machines

    # 機械ごとの待ち行列: (arrival_time, job_id, op_index)
    queues: List[List[Tuple[int, int, int]]] = [[] for _ in range(num_machines)]

    # 完了イベント: (end_time, machine_id, job_id, op_index, start_time)
    events: List[Tuple[int, int, int, int, int]] = []

    scheduled: List[ScheduledOp] = []
    job_completion = [0] * num_jobs

    def enqueue_if_available(job_id: int, arrival_time: int) -> None:
        oi = next_op[job_id]
        if oi >= len(instance.jobs[job_id]):
            return
        machine_id, _dur = instance.jobs[job_id][oi]
        heappush(queues[machine_id], (arrival_time, job_id, oi))

    # 初期投入: 各ジョブの先頭工程が時刻0に到着
    for j in range(num_jobs):
        enqueue_if_available(j, 0)

    # 時刻tで空いている機械に割り当てを試みる
    def try_dispatch(now: int) -> None:
        for m in range(num_machines):
            if machine_free[m] > now:
                continue
            if not queues[m]:
                continue

            arrival_time, job_id, oi = heappop(queues[m])
            # 実開始は「機械が空く時刻」と「到着時刻」のmax
            start = max(machine_free[m], arrival_time)
            machine_id, dur = instance.jobs[job_id][oi]
            end = start + dur

            machine_free[m] = end
            heappush(events, (end, m, job_id, oi, start))

            scheduled.append(
                ScheduledOp(
                    job_id=job_id,
                    op_index=oi,
                    machine_id=machine_id,
                    start=start,
                    end=end,
                    duration=dur,
                )
            )

    # 初回ディスパッチ
    try_dispatch(0)

    # メインループ
    last_time = 0
    while events:
        end_time, m, job_id, oi, _start_time = heappop(events)
        last_time = end_time

        # ジョブの次工程を投入
        next_op[job_id] = oi + 1
        if next_op[job_id] >= len(instance.jobs[job_id]):
            job_completion[job_id] = end_time
        else:
            enqueue_if_available(job_id, end_time)

        # この時刻で割当を進める
        try_dispatch(end_time)

        # ここで「空いている機械があるが、到着時刻が未来のジョブしかない」ケースがありうる
        # events を進めれば自然に now が進むため追加処理は不要（start=maxで吸収）

    makespan = max(job_completion) if job_completion else 0

    # 念のため（シミュレーションの整合）
    makespan = max(makespan, last_time)

    return FCFSSchedule(
        instance_name=instance.name,
        ops=sorted(scheduled, key=lambda x: (x.start, x.machine_id, x.job_id, x.op_index)),
        makespan=makespan,
        job_completion=job_completion,
    )


