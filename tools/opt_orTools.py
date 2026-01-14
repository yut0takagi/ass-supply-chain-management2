import simpy
from ortools.sat.python import cp_model

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors



def opt_orTools(jobs_data, job_priorities, num_machines):
    # ジョブの優先度（高い数値が高い優先度）
    # [100, 2, 1] などにすることで最優先のようにすることも可能
    job_priorities = job_priorities
    # モデルとソルバーの初期化
    model = cp_model.CpModel()

    # 変数と制約の定義
    tasks = {}
    ends = []
    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine, duration = task
            start_var = model.NewIntVar(0, 1000, f'start_{job_id}_{task_id}')
            end_var = model.NewIntVar(0, 1000, f'end_{job_id}_{task_id}')
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{job_id}_{task_id}')
            tasks[job_id, task_id] = (start_var, end_var, interval_var)
            if task_id == len(job) - 1:
                ends.append(end_var)

    # 同一機械での非重複制約
    machines = {i: [] for i in range(3)}
    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine, _ = task
            machines[machine].append(tasks[job_id, task_id][2])
    for machine_intervals in machines.values():
        model.AddNoOverlap(machine_intervals)

    # 同一ジョブ内の順序制約
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.Add(tasks[job_id, task_id][1] <= tasks[job_id, task_id + 1][0])

    # 目的関数（優先度に応じたペナルティを含む完了時間の最小化）
    weighted_ends = [end * job_priorities[job_id] for job_id, end in enumerate(ends)]
    model.Minimize(sum(weighted_ends))

    # ソルバーの実行
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 結果の出力
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                start = solver.Value(tasks[job_id, task_id][0])
                end = solver.Value(tasks[job_id, task_id][1])
                print(f'ジョブ {job_id} タスク {task_id} 開始: {start}, 終了: {end}')
    else:
        print('最適解が見つかりませんでした。')

    # 結果の解析とグラフ用のデータの作成
    machines_schedule = {m: [] for m in range(num_machines)}
    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine = task[0]
            start = solver.Value(tasks[job_id, task_id][0])
            end = solver.Value(tasks[job_id, task_id][1])
            machines_schedule[machine].append((start, end, f'Job {job_id}'))

    # グラフの描画
    fig, ax = plt.subplots()
    colors = list(mcolors.TABLEAU_COLORS.values())  # カラーパレット
    for machine, machine_schedule in machines_schedule.items():
        for job_num, (start, end, job_label) in enumerate(machine_schedule):
            ax.barh(machine, end - start, left=start, height=0.4, color=colors[job_num % len(colors)], edgecolor='black')
            ax.text((start + end) / 2, machine, job_label, ha='center', va='center')

    ax.set_xlabel('Time')
    ax.set_ylabel('Machine')
    ax.set_title('Job Shop Scheduling Result')
    plt.show()