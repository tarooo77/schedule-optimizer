#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール最適化のテストプログラム (拡張版 - 全曜日対応)
"""

import pandas as pd
import numpy as np
import random
import time
from utils_enhanced import TIMES, DAYS, get_all_slots_full, format_results
from result_formatter import format_assignment_results
from full_random_scheduler import EnhancedScheduleOptimizer, create_fully_random_data

def run_test_case(name, num_students, num_iterations=10):
    """テストケースを実行"""
    print(f"\n=== テストケース: {name} ===")
    print(f"生徒数: {num_students}名")
    
    # ダミーデータを生成
    students_df = create_fully_random_data(num_students)
    
    # 最適化を実行
    start_time = time.time()
    optimizer = EnhancedScheduleOptimizer()
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
    
    for day in DAYS:
        count = len(day_assignments.get(day, []))
        print(f"{day}: {count}名")
    
    # 詳細な割り当て結果を表示
    print("\n【詳細な割り当て結果】")
    formatted_results = format_assignment_results(results)
    print(formatted_results)
    
    return results

def main():
    """メイン処理"""
    print("=== スケジュール最適化テスト (拡張版 - 全曜日対応) ===")
    
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
        ("小規模", 7),
        ("中規模", 14),
        ("大規模", 21),
        ("最大規模", 28)
    ]
    
    results_by_case = {}
    for name, num_students in test_cases:
        results = run_test_case(name, num_students)
        results_by_case[name] = results
    
    # 全テストケースの結果を比較
    print("\n=== テストケース比較 ===")
    print("テストケース別の希望達成率:")
    print("テストケース | 第1希望率 | 第2希望率 | 第3希望率 | 希望外率")
    print("-" * 60)
    
    for name, results in results_by_case.items():
        if 'stats' in results:
            stats = results['stats']
            print(f"{name:10} | {stats.get('第1希望率', 0):8.1f}% | {stats.get('第2希望率', 0):8.1f}% | {stats.get('第3希望率', 0):8.1f}% | {stats.get('希望外率', 0):8.1f}%")
    
    # 最も良い結果を表示
    print("\n=== 最も良い結果 ===")
    best_case = min(results_by_case.items(), key=lambda x: x[1]['stats'].get('希望外率', 100) if 'stats' in x[1] else 100)
    print(f"テストケース: {best_case[0]}")
    
    if 'stats' in best_case[1]:
        stats = best_case[1]['stats']
        print(f"第1希望率: {stats.get('第1希望率', 0):.1f}%")
        print(f"第2希望率: {stats.get('第2希望率', 0):.1f}%")
        print(f"第3希望率: {stats.get('第3希望率', 0):.1f}%")
        print(f"希望外率: {stats.get('希望外率', 0):.1f}%")
    
    # 詳細な割り当て結果を表示
    print("\n=== 最も良い結果の詳細 ===")
    best_results = best_case[1]
    
    if 'assigned' in best_results:
        days = DAYS
        times = TIMES
        
        # 曜日ごとに割り当て結果を整理
        day_assignments = {day: [] for day in days}
        
        # 各生徒の割り当てを曜日ごとに分類
        for student in best_results['assigned']:
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
    else:
        print("\n詳細な割り当て情報が利用できません。")

if __name__ == "__main__":
    main()
