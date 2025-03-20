#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
スケジュール最適化の結果を表示するスクリプト
"""

import pandas as pd
import numpy as np
import random
from schedule_optimizer_compact import ScheduleOptimizer
from data_generator import create_dummy_data
from utils import get_all_slots

def main():
    # シードを固定して結果を再現しやすくする
    random.seed(42)
    
    # ダミーデータを生成
    num_students = 21
    print(f"合計生徒数: {num_students}名")
    print(f"森ビル: {num_students}名 ({num_students // 7}ユニット)")
    
    students_df = create_dummy_data(num_students)
    
    # スロットを取得
    slots = get_all_slots(num_students)
    
    # スケジュール最適化を実行
    optimizer = ScheduleOptimizer()
    results = optimizer.optimize_schedule(students_df)
    
    # 結果のサマリを表示
    if 'stats' in results:
        stats = results['stats']
        print(f"\n=== 結果サマリー ===")
        print(f"割り当て済み: {stats.get('割り当て済み', 0)}名")
        print(f"未割り当て: {stats.get('未割り当て', 0)}名")
        print(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)")
        print(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)")
        print(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)")
        print(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)")
    
    # 曜日ごとの割り当て結果を表示
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    times = ["10時", "11時", "12時", "14時", "15時", "16時", "17時"]
    
    print("\n=== 曜日ごとの割り当て ===")
    day_counts = {day: 0 for day in days}
    
    if results and 'assigned' in results:
        for student in results['assigned']:
            day = student['割当曜日']
            if day in day_counts:
                day_counts[day] += 1
    
    for day in days:
        print(f"{day}: {day_counts[day]}名")
    
    # 詳細な割り当て結果を表示
    print("\n=== 割り当て結果 ===")
    print(f"\n割り当て済み件数: {len(results['assigned'])}")
    
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

if __name__ == "__main__":
    main()
