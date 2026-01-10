from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


Op = Tuple[int, int]  # (machine_id, duration)


@dataclass(frozen=True)
class JobshopInstance:
    name: str
    jobs: List[List[Op]]

    @property
    def num_jobs(self) -> int:
        return len(self.jobs)

    @property
    def num_machines(self) -> int:
        m = 0
        for job in self.jobs:
            for machine_id, _ in job:
                m = max(m, machine_id + 1)
        return m


def instance_assignment_jobs() -> JobshopInstance:
    # README.md の課題1(1)に記載のジョブ
    jobs: List[List[Op]] = [
        [(0, 3), (1, 2), (2, 2)],  # job0
        [(0, 2), (2, 1), (1, 4)],  # job1
        [(1, 4), (2, 3)],  # job2
        [(1, 2), (0, 1), (2, 4)],  # job3
        [(2, 1), (0, 2), (1, 1)],  # job4
    ]
    return JobshopInstance(name="assignment_jobs", jobs=jobs)


def instance_custom_jobs() -> JobshopInstance:
    """
    課題1(3) 用に「各自で好きなジョブパターン」を1つ用意。
    - 機械(0,1,2)を使う
    - 長短の工程が混ざるようにして、競合が起きやすい構成
    """
    jobs: List[List[Op]] = [
        [(0, 2), (1, 5), (2, 2)],
        [(1, 2), (2, 4), (0, 2)],
        [(2, 3), (0, 4)],
        [(0, 3), (2, 1), (1, 2)],
        [(1, 4), (0, 1), (2, 3)],
    ]
    return JobshopInstance(name="custom_jobs", jobs=jobs)


def weight_patterns(num_jobs: int) -> List[Tuple[str, Sequence[int]]]:
    """
    課題1(2): ジョブ重みを3パターン
    - パターンA: 全て同じ（= makespan寄りの性格になりやすい）
    - パターンB: 先頭ジョブを重視
    - パターンC: 中盤ジョブを重視（例: job2, job3）
    """
    if num_jobs < 5:
        base = [1] * num_jobs
        return [
            ("A_uniform", base),
            ("B_front_heavy", [3] + [1] * (num_jobs - 1)),
            ("C_middle_heavy", [1] * num_jobs),
        ]

    wA = [1] * num_jobs
    wB = [5, 3, 1, 1, 1] + [1] * max(0, num_jobs - 5)
    wC = [1, 1, 5, 3, 1] + [1] * max(0, num_jobs - 5)
    return [
        ("A_uniform", wA),
        ("B_front_heavy", wB[:num_jobs]),
        ("C_middle_heavy", wC[:num_jobs]),
    ]


