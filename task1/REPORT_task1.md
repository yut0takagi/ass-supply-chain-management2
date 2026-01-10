## 課題1（Jobshop: FCFS と OR-Tools最適化の比較）

この `REPORT_task1.md` は、同梱のコード（`task1/run_task1.py`）で出力される **表（CSV）・ガントチャート（PNG）** を貼り付けて最終レポートに転記できるようにするための雛形です。

### 実行方法

1) 依存関係インストール

```bash
python -m pip install -r requirements.txt
```

2) 実行（結果が `task1_outputs/` に出ます）

```bash
python -m task1.run_task1
```

### (1) 指定ジョブでの FCFS 結果と OR-Tools最適化結果

対象ジョブ（README記載）:
- job0: [(0, 3), (1, 2), (2, 2)]
- job1: [(0, 2), (2, 1), (1, 4)]
- job2: [(1, 4), (2, 3)]
- job3: [(1, 2), (0, 1), (2, 4)]
- job4: [(2, 1), (0, 2), (1, 1)]

出力先:
- まとめ表: `task1_outputs/assignment_jobs/assignment_jobs_summary.csv`
- FCFS:
  - 工程表: `task1_outputs/assignment_jobs/assignment_jobs_fcfs_ops.csv`
  - ガント: `task1_outputs/assignment_jobs/assignment_jobs_fcfs_gantt.png`
- OR-Tools（makespan最小）:
  - 工程表: `task1_outputs/assignment_jobs/assignment_jobs_opt_makespan_ops.csv`
  - ガント: `task1_outputs/assignment_jobs/assignment_jobs_opt_makespan_gantt.png`

（ここに結果を貼り付け）
- **FCFSのメイクスパン**:
- **OR-Tools最適化のメイクスパン**:
- **差分（改善量）**:

考察（例の観点）:
- FCFSでは「先に来た作業」が優先されるため、ある機械で短い作業が長い作業の後ろに並ぶなど、全体の遊休や待ちが増えやすい。
- OR-Tools（CP-SAT）は機械の競合（no-overlap）とジョブ内順序制約を満たしつつ、目的（makespan最小）を直接最適化するため、ボトルネック機械上の並び替えが起き、最大完了時刻が縮むことがある。

### (2) 重み付き（3パターン）での結果変化

目的: \(\sum_j w_j C_j\)（各ジョブの最終工程完了時刻 \(C_j\) の重み付き和）を最小化。

出力先:
- `task1_outputs/assignment_jobs/assignment_jobs_opt_weighted_A_uniform_*`
- `task1_outputs/assignment_jobs/assignment_jobs_opt_weighted_B_front_heavy_*`
- `task1_outputs/assignment_jobs/assignment_jobs_opt_weighted_C_middle_heavy_*`

（ここに結果を貼り付け）
- **A（均一）**: 目的値 / makespan / 各Cj
- **B（先頭重視）**: 目的値 / makespan / 各Cj
- **C（中盤重視）**: 目的値 / makespan / 各Cj

考察（例の観点）:
- 重みを大きくしたジョブほど \(C_j\) を早める並びになりやすい一方、他ジョブの完了が遅れたり makespan が増えることもある（トレードオフ）。
- makespan最小と重み付き目的最小は一致しないことが多く、目的関数の違いがスケジュールの形を変える。

### (3) 自作ジョブパターンでの確認・考察

自作ジョブは `task1/jobshop_data.py` の `instance_custom_jobs()` に定義。

出力先:
- まとめ表: `task1_outputs/custom_jobs/custom_jobs_summary.csv`
- ガント/工程表: `task1_outputs/custom_jobs/` 以下

（ここに結果を貼り付け）
- **FCFS vs makespan最小 vs 重み付き** の違い:

考察:
- 自作パターンで競合が強い機械（ボトルネック）がどれか
- FCFSで待ちが連鎖する箇所、最適化で解消される箇所


