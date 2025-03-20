#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール最適化のテストプログラム (Compact Version)
"""

import pandas as pd
from time import perf_counter
from schedule_optimizer_compact import ScheduleOptimizer
from data_generator import create_dummy_data
from utils import TIMES, format_results
import time
from result_formatter import (
    format_assignment_results, 
    format_single_result_summary,
    get_assignments_list, 
    format_results_summary, 
    find_best_result, 
    format_best_result
)


def run_test_case(name, num_students, num_iterations=10):
    """テストケースを実行"""
    print(f"\n==================================================")
    print(f"テストケース: {name}")
    print(f"==================================================\n")
    
    results_data = []
    
    for i in range(num_iterations):
        print(f"イテレーション {i+1}/{num_iterations}\n")
        print(f"=== {name} ===")
        
        # ダミーデータを生成
        print("ダミーデータを生成しています...")
        preferences_df = create_dummy_data(num_students)
        print(f"合計生徒数: {len(preferences_df)}名")
        print(f"森ビル: {len(preferences_df)}名 ({(len(preferences_df) + 6) // 7}ユニット)")
        
        # スケジュールを最適化
        optimizer = ScheduleOptimizer()
        start_time = perf_counter()
        results = optimizer.optimize_schedule(preferences_df)
        end_time = perf_counter()
        
        # 処理時間を計算
        processing_time = end_time - start_time
        
        # 結果を集計
        assigned_count = len(results['assigned'])
        unassigned_count = len(results['unassigned'])
        
        preference_counts = {'第1希望': 0, '第2希望': 0, '第3希望': 0, '希望外': 0}
        for student in results['assigned']:
            pref = student['希望順位']
            preference_counts[pref] += 1
        
        # 処理時間を表示
        print(f"\n処理時間: {processing_time:.2f}秒")
        
        # 結果のサマリーを表示（result_formatter.pyを使用）
        summary = format_single_result_summary(results)
        print(summary)
        
        # 割り当て結果の詳細を表示（result_formatter.pyを使用）
        formatted_results = format_assignment_results(results)
        print(formatted_results)
        
        # 結果を保存
        assignments = []
        for student in results['assigned']:
            name = student['生徒名']
            day = student['割当曜日']
            time = student['割当時間']
            pref = student['希望順位']
            assignments.append(f"{name}: {day}{time} ({pref})")

        # 結果をデータフレーム用に保存
        result_row = {
            'テストケース': name,
            'イテレーション': i + 1,
            '生徒数': num_students,
            '処理時間': processing_time,
            '未割り当て': unassigned_count,
            '第1希望': preference_counts['第1希望'],
            '第2希望': preference_counts['第2希望'],
            '第3希望': preference_counts['第3希望'],
            '希望外': preference_counts['希望外'],
            '割り当て結果': sorted(assignments)
        }
        results_data.append(result_row)
        
        print()  # 空行を追加
    
    return results_data


def main():
    """メイン処理"""
    # テストケースを定義
    test_cases = [
        ("3ユニット（21名）", 21)
    ]
    
    # 全テストケースの結果を保存
    all_results = []
    
    # 各テストケースを実行
    for name, num_students in test_cases:
        results = run_test_case(name, num_students)
        all_results.extend(results)
    
    # 最適な結果を見つける（result_formatter.pyを使用）
    best_result = find_best_result(all_results)
    
    # 結果のサマリを表示（result_formatter.pyを使用）
    summary = format_results_summary(all_results)
    print(summary)

    # 最適な結果の例を表示（result_formatter.pyを使用）
    best_result_formatted = format_best_result(best_result)
    print(best_result_formatted)
    
    # 最適な割り当て結果の詳細スケジュールを表示
    if best_result and 'result' in best_result:
        print("\n=== 最適な割り当て結果の詳細スケジュール ===\n")
        print("以下はシミュレーションによる割り当て例です。実際の割り当ては生徒の希望により異なります。")
        
        # 各曜日と時間帯の割り当てを表示
        days = ["火曜日", "水曜日", "木曜日", "金曜日"]
        times = ["10時", "11時", "12時", "14時", "15時", "16時", "17時"]
        
        # 直接実行して結果を取得
        from schedule_optimizer_compact import ScheduleOptimizer
        from data_generator import create_dummy_data
        import pandas as pd
        import random
        
        # 最適な結果のテストケースを取得
        test_case = best_result['case_name']
        num_students = best_result['num_students']
        
        # ダミーデータを生成
        print(f"\n最適化アルゴリズムを実行中...")
        # シードを固定して結果を再現しやすくする
        random.seed(42)
        students_df = create_dummy_data(num_students)
        
        # スロットを取得
        from utils import get_all_slots
        slots = get_all_slots(num_students)
        
        # スケジュール最適化を実行
        optimizer = ScheduleOptimizer()
        results = optimizer.optimize_schedule(students_df)
        
        # 割り当て結果を取得
        best_assignment = results
        
        # 結果のサマリを表示
        total_students = len(students_df)
        if 'stats' in best_assignment:
            stats = best_assignment['stats']
            print(f"\n割り当て結果のサマリ:")
            print(f"  第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)")
            print(f"  第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)")
            print(f"  第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)")
            print(f"  希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)")
        
        if best_assignment and 'assigned' in best_assignment:
            # 曜日ごとに割り当て結果を整理
            day_assignments = {day: [] for day in days}
            
            # 各生徒の割り当てを曜日ごとに分類
            for student in best_assignment['assigned']:
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
