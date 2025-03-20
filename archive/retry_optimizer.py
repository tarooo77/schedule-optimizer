#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
同じデータセットで試行回数を増やしたスケジュール最適化
"""

import pandas as pd
import numpy as np
import random
import time
import os
from flexible_scheduler import ALL_DAYS, TIMES, get_all_slots_full, create_fully_random_data, FlexibleScheduleOptimizer

def run_optimization_with_more_attempts(num_students, max_attempts=50):
    """試行回数を増やして最適化を実行"""
    print(f"\n=== 試行回数を増やした最適化 (試行回数: {max_attempts}) ===")
    print(f"生徒数: {num_students}名")
    
    # シードを固定して同じデータを使用
    random.seed(42)
    
    # ダミーデータを生成
    students_df = create_fully_random_data(num_students)
    
    # 最適化を実行
    start_time = time.time()
    
    # 試行回数を増やした最適化器を作成
    optimizer = FlexibleScheduleOptimizer()
    optimizer.MAX_ATTEMPTS = max_attempts  # 試行回数を増やす
    
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
    
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, f"retry_optimization_results_{max_attempts}.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write(f"試行回数を増やした最適化の結果 (試行回数: {max_attempts})\n")
        f.write("=================================================\n\n")
        
        # 1. 最適化設定
        f.write("1. 最適化設定\n")
        f.write("-------------------------------------------------\n")
        f.write(f"生徒数: {num_students}名\n")
        f.write(f"試行回数: {max_attempts}回\n\n")
        
        # 2. 最適化結果のサマリ
        f.write("2. 最適化結果のサマリ\n")
        f.write("-------------------------------------------------\n")
        
        if 'stats' in results:
            stats = results['stats']
            f.write(f"割り当て済み: {stats.get('割り当て済み', 0)}名\n")
            f.write(f"未割り当て: {stats.get('未割り当て', 0)}名\n")
            f.write(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)\n")
            f.write(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)\n")
            f.write(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)\n")
            f.write(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)\n\n")
        
        # 3. 曜日ごとの割り当て結果
        f.write("3. 曜日ごとの割り当て結果\n")
        f.write("-------------------------------------------------\n")
        
        days = ALL_DAYS
        times = TIMES
        
        day_counts = {day: 0 for day in days}
        
        if results and 'assigned' in results:
            for student in results['assigned']:
                day = student['割当曜日']
                if day in day_counts:
                    day_counts[day] += 1
        
        for day in days:
            f.write(f"{day}: {day_counts[day]}名\n")
        f.write("\n")
        
        # 4. 詳細な割り当て結果
        f.write("4. 詳細な割り当て結果\n")
        f.write("-------------------------------------------------\n")
        
        f.write(f"割り当て済み件数: {len(results['assigned'])}\n\n")
        
        # 曜日ごとに割り当て結果を整理
        day_assignments = {day: [] for day in days}
        
        # 各生徒の割り当てを曜日ごとに分類
        for student in results['assigned']:
            day = student['割当曜日']
            time = student['割当時間']
            name = student['生徒名']
            pref = student['希望順位']
            day_assignments[day].append((time, name, pref))
        
        # 曜日ごとに書き込む
        for day in days:
            assignments = day_assignments[day]
            f.write(f"{day}: ({len(assignments)}件)\n")
            
            # 時間帯ごとに書き込む
            f.write("----------------------------------------\n")
            for time in times:
                students = [(s[1], s[2]) for s in assignments if s[0] == time]
                if students:
                    for student, pref in students:
                        f.write(f"{time}: {student}({pref})\n")
            f.write("----------------------------------------\n\n")
        
        # 5. まとめ
        f.write("5. まとめ\n")
        f.write("-------------------------------------------------\n")
        
        f.write(f"試行回数を{max_attempts}回に増やした結果、")
        if stats.get('希望外', 0) == 0:
            f.write("全ての生徒を希望通りに割り当てることができました。\n")
        else:
            f.write(f"希望外の割り当ては{stats.get('希望外', 0)}名({stats.get('希望外率', 0):.1f}%)でした。\n")
        
        f.write(f"処理時間は{execution_time:.2f}秒でした。\n")
    
    print(f"\n試行回数を増やした最適化の詳細結果を {results_file} に保存しました。")
    
    return results

def main():
    """メイン処理"""
    print("=== 試行回数を増やした最適化テスト ===")
    
    # 標準の試行回数（10回）での結果を表示
    print("\n【標準の試行回数（10回）での結果】")
    print("これは既に実行済みの結果です。希望外: 4名 (19.0%)")
    
    # 試行回数を増やした最適化を実行
    attempts_list = [50, 100]
    
    for attempts in attempts_list:
        results = run_optimization_with_more_attempts(21, attempts)

if __name__ == "__main__":
    main()
