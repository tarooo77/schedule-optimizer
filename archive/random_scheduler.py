#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
完全にランダムなスケジュール最適化のデモスクリプト
"""

import pandas as pd
import numpy as np
import random
import os
import time as time_module
from schedule_optimizer_compact import ScheduleOptimizer
from utils import TIMES

def create_fully_random_data(num_students):
    """
    完全にランダムなダミーデータを生成する関数
    火曜日から金曜日までの全ての曜日と時間帯を使用
    """
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    times = TIMES
    
    # 全てのスロットを生成
    all_slots = []
    for day in days:
        for time in times:
            all_slots.append(f"{day}{time}")
    
    data = []
    for i in range(num_students):
        # ランダムに3つの希望を選択
        preferences = random.sample(all_slots, 3)
        data.append({
            '生徒名': f'生徒{i+1}',
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })
    return pd.DataFrame(data)

def get_all_slots_full():
    """
    全ての曜日と時間帯のスロットを生成
    """
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    times = TIMES
    
    all_slots = []
    for day in days:
        for time in times:
            all_slots.append(f"{day}{time}")
    
    return all_slots

def main():
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, "random_schedule_results.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write("完全ランダムなスケジュール最適化の詳細プロセスと結果\n")
        f.write("=================================================\n\n")
        
        # 1. ダミーデータの作成
        f.write("1. ダミーデータの作成\n")
        f.write("-------------------------------------------------\n")
        
        # シードを固定して結果を再現しやすくする
        random.seed(42)
        
        # ダミーデータを生成
        num_students = 21
        f.write(f"合計生徒数: {num_students}名\n")
        f.write(f"森ビル: {num_students}名 ({num_students // 7}ユニット)\n\n")
        
        students_df = create_fully_random_data(num_students)
        
        # ダミーデータの表示
        f.write("生成されたダミーデータ:\n")
        f.write(students_df.to_string(index=False) + "\n\n")
        
        # 2. スロットの取得
        f.write("2. スロットの取得\n")
        f.write("-------------------------------------------------\n")
        
        slots = get_all_slots_full()
        
        f.write(f"利用可能なスロット数: {len(slots)}\n")
        f.write("スロット一覧:\n")
        for i, slot in enumerate(slots, 1):
            f.write(f"{i}. {slot}\n")
        f.write("\n")
        
        # 3. スケジュール最適化の実行
        f.write("3. スケジュール最適化の実行\n")
        f.write("-------------------------------------------------\n")
        
        start_time = time_module.time()
        optimizer = ScheduleOptimizer()
        results = optimizer.optimize_schedule(students_df)
        end_time = time_module.time()
        
        execution_time = end_time - start_time
        f.write(f"処理時間: {execution_time:.2f}秒\n\n")
        
        # 4. 最適化結果のサマリ
        f.write("4. 最適化結果のサマリ\n")
        f.write("-------------------------------------------------\n")
        
        if 'stats' in results:
            stats = results['stats']
            f.write(f"割り当て済み: {stats.get('割り当て済み', 0)}名\n")
            f.write(f"未割り当て: {stats.get('未割り当て', 0)}名\n")
            f.write(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)\n")
            f.write(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)\n")
            f.write(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)\n")
            f.write(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)\n\n")
        
        # 5. 曜日ごとの割り当て結果
        f.write("5. 曜日ごとの割り当て結果\n")
        f.write("-------------------------------------------------\n")
        
        days = ["火曜日", "水曜日", "木曜日", "金曜日"]
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
        
        # 6. 詳細な割り当て結果
        f.write("6. 詳細な割り当て結果\n")
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
        
        # 7. 生徒ごとの希望と割り当て結果の比較
        f.write("7. 生徒ごとの希望と割り当て結果の比較\n")
        f.write("-------------------------------------------------\n")
        
        # 生徒の希望と割り当て結果を整理
        student_results = []
        for student in results['assigned']:
            name = student['生徒名']
            assigned_day = student['割当曜日']
            assigned_time = student['割当時間']
            pref = student['希望順位']
            
            # 生徒の希望を取得
            student_data = students_df[students_df['生徒名'] == name].iloc[0]
            pref1 = student_data['第1希望']
            pref2 = student_data['第2希望']
            pref3 = student_data['第3希望']
            
            student_results.append({
                '生徒名': name,
                '第1希望': pref1,
                '第2希望': pref2,
                '第3希望': pref3,
                '割当結果': f"{assigned_day} {assigned_time}",
                '希望順位': pref
            })
        
        # 生徒ごとに書き込む
        for i, result in enumerate(sorted(student_results, key=lambda x: x['生徒名']), 1):
            f.write(f"生徒{result['生徒名'].replace('生徒', '')}:\n")
            f.write(f"  第1希望: {result['第1希望']}\n")
            f.write(f"  第2希望: {result['第2希望']}\n")
            f.write(f"  第3希望: {result['第3希望']}\n")
            f.write(f"  割当結果: {result['割当結果']} ({result['希望順位']})\n")
            f.write("\n")
        
        # 8. まとめ
        f.write("8. まとめ\n")
        f.write("-------------------------------------------------\n")
        
        f.write("このスケジュール最適化では、21名の生徒を火曜日から金曜日の時間帯に\n")
        f.write("割り当てました。各生徒の希望を最大限考慮し、できるだけ多くの生徒が\n")
        f.write("第1希望または第2希望の時間帯に割り当てられるようにしました。\n\n")
        
        if 'stats' in results:
            stats = results['stats']
            f.write(f"第1希望達成率: {stats.get('第1希望率', 0):.1f}%\n")
            f.write(f"第2希望達成率: {stats.get('第2希望率', 0):.1f}%\n")
            f.write(f"第3希望達成率: {stats.get('第3希望率', 0):.1f}%\n")
            f.write(f"希望外割合: {stats.get('希望外率', 0):.1f}%\n\n")
        
        f.write("以上が最適化の詳細プロセスと結果です。\n")
    
    print(f"\n完全ランダムな詳細結果を {results_file} に保存しました。")
    print("以下のコマンドで結果を確認できます:")
    print(f"less {results_file}")

if __name__ == "__main__":
    main()
