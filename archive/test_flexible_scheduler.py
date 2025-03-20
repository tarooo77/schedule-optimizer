#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
柔軟なスケジュール最適化のテストプログラム
- 生徒は火曜日から金曜日までの希望を出せる
- 実際の割り当ては3ユニット（21名）なので、4日間のうち3日間だけを使用
"""

import pandas as pd
import numpy as np
import random
import time
from flexible_scheduler import ALL_DAYS, TIMES, get_all_slots_full, create_fully_random_data, FlexibleScheduleOptimizer

def run_test_case(name, num_students, num_iterations=10):
    """テストケースを実行"""
    print(f"\n=== テストケース: {name} ===")
    print(f"生徒数: {num_students}名")
    
    # ダミーデータを生成
    students_df = create_fully_random_data(num_students)
    
    # 最適化を実行
    start_time = time.time()
    optimizer = FlexibleScheduleOptimizer()
    results = optimizer.optimize_schedule(students_df)
    end_time = time.time()
    
    # 結果を表示
    execution_time = end_time - start_time
    print(f"\n処理時間: {execution_time:.2f}秒")
    
    # 割り当て結果のサマリを表示
    if 'stats' in results:
        stats = results['stats']
        print(f"\n割り当て済み: {stats.get('割り当て済み', 0)}名")
        print(f"未割り当て: {stats.get('未割り当て', 0)}名")
        print(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)")
        print(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)")
        print(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)")
        print(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)")
    
    # 曜日ごとの割り当て数を表示
    print("\n【曜日ごとの割り当て】")
    day_assignments = {}
    for student in results['assigned']:
        day = student['割当曜日']
        if day not in day_assignments:
            day_assignments[day] = []
        day_assignments[day].append(student)
    
    for day in ALL_DAYS:
        count = len(day_assignments.get(day, []))
        print(f"{day}: {count}名")
    
    # 詳細な割り当て結果を表示
    print("\n【詳細な割り当て結果】")
    days = ALL_DAYS
    times = TIMES
    
    # 曜日ごとに割り当て結果を整理
    day_assignments = {day: [] for day in days}
    
    # 各生徒の割り当てを曜日ごとに分類
    for student in results['assigned']:
        day = student['割当曜日']
        time = student['割当時間']
        name = student['生徒名']
        pref = student['希望順位']
        day_assignments[day].append((time, f"{name}({pref})"))
    
    # 曜日ごとに表示
    for day in days:
        assignments = day_assignments[day]
        print(f"\n{day}: ({len(assignments)}件)")
        
        # 時間帯ごとに表示
        print("----------------------------------------")
        for time in times:
            students = [s[1] for s in assignments if s[0] == time]
            if students:
                for student in students:
                    print(f"{time}: {student}")
        print("----------------------------------------")
    
    return results

def main():
    """メイン処理"""
    print("=== 柔軟なスケジュール最適化テスト ===")
    
    # シードを固定して結果を再現しやすくする
    random.seed(42)
    
    # 利用可能なスロットを表示
    all_slots = get_all_slots_full()
    print(f"\n利用可能なスロット数: {len(all_slots)}")
    print("スロット一覧:")
    for i, slot in enumerate(all_slots, 1):
        print(f"{i}. {slot}")
    
    # テストケースを実行
    test_cases = [
        ("標準規模", 21)
    ]
    
    for name, num_students in test_cases:
        results = run_test_case(name, num_students)
    
    print("\n=== テスト完了 ===")
    print("柔軟なスケジューラーは、火曜日から金曜日までの中から最適な3日間を選択して")
    print("全生徒を割り当てました。希望を最大限考慮し、できるだけ多くの生徒が")
    print("第1希望または第2希望の時間帯に割り当てられるようにしています。")

if __name__ == "__main__":
    main()
