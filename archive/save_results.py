#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
スケジュール最適化の結果をファイルに保存するスクリプト
"""

import pandas as pd
import numpy as np
import random
from schedule_optimizer_compact import ScheduleOptimizer
from data_generator import create_dummy_data
from utils import get_all_slots
import os

def main():
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, "schedule_results.txt")
    
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
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        # 結果のサマリを書き込む
        if 'stats' in results:
            stats = results['stats']
            f.write(f"\n=== 結果サマリー ===\n")
            f.write(f"割り当て済み: {stats.get('割り当て済み', 0)}名\n")
            f.write(f"未割り当て: {stats.get('未割り当て', 0)}名\n")
            f.write(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)\n")
            f.write(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)\n")
            f.write(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)\n")
            f.write(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)\n")
        
        # 曜日ごとの割り当て結果を書き込む
        days = ["火曜日", "水曜日", "木曜日", "金曜日"]
        times = ["10時", "11時", "12時", "14時", "15時", "16時", "17時"]
        
        f.write("\n=== 曜日ごとの割り当て ===\n")
        day_counts = {day: 0 for day in days}
        
        if results and 'assigned' in results:
            for student in results['assigned']:
                day = student['割当曜日']
                if day in day_counts:
                    day_counts[day] += 1
        
        for day in days:
            f.write(f"{day}: {day_counts[day]}名\n")
        
        # 詳細な割り当て結果を書き込む
        f.write("\n=== 割り当て結果 ===\n")
        f.write(f"\n割り当て済み件数: {len(results['assigned'])}\n")
        
        # 曜日ごとに割り当て結果を整理
        day_assignments = {day: [] for day in days}
        
        # 各生徒の割り当てを曜日ごとに分類
        for student in results['assigned']:
            day = student['割当曜日']
            time = student['割当時間']
            name = student['生徒名']
            pref = student['希望順位']
            day_assignments[day].append((time, f"{name}({pref})"))
        
        # 曜日ごとに書き込む
        for day in days:
            assignments = day_assignments[day]
            f.write(f"\n{day}: ({len(assignments)}件)\n")
            
            # 時間帯ごとに書き込む
            f.write("----------------------------------------\n")
            for time in times:
                students = [s[1] for s in assignments if s[0] == time]
                if students:
                    for student in students:
                        f.write(f"{time}: {student}\n")
            f.write("----------------------------------------\n")
    
    print(f"\n結果を {results_file} に保存しました。")
    print("以下のコマンドで結果を確認できます:")
    print(f"cat {results_file}")

if __name__ == "__main__":
    main()
