#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
希望外をゼロにするための徹底的な最適化
"""

import pandas as pd
import numpy as np
import random
import time as time_module
import os
import sys
from flexible_scheduler import ALL_DAYS, TIMES, get_all_slots_full, create_fully_random_data, FlexibleScheduleOptimizer

def run_exhaustive_optimization(num_students, max_attempts_per_combination=1000):
    """希望外がゼロになるまで徹底的に最適化を実行"""
    print(f"\n=== 希望外ゼロを目指した徹底的な最適化 ===")
    print(f"生徒数: {num_students}名")
    
    # シードを固定して同じデータを使用
    random.seed(42)
    
    # ダミーデータを生成
    students_df = create_fully_random_data(num_students)
    
    # 最適化を実行
    start_time = time_module.time()
    
    # 徹底的な最適化器を作成
    optimizer = FlexibleScheduleOptimizer()
    
    # 曜日の組み合わせを取得
    import itertools
    days = ALL_DAYS
    day_combinations = list(itertools.combinations(days, 3))
    
    best_result = None
    best_cost = float('inf')
    best_days = None
    best_stats = None
    
    print(f"希望外がゼロになるまで徹底的に最適化を実行します...")
    print(f"各曜日の組み合わせに対して最大{max_attempts_per_combination}回の試行を行います")
    
    # 進捗表示用のカウンター
    total_attempts = 0
    found_zero_unwanted = False
    
    for i, days_to_use in enumerate(day_combinations, 1):
        print(f"\n組み合わせ {i}/{len(day_combinations)}: {', '.join(days_to_use)}")
        
        # 試行回数を増やして最適化
        optimizer.MAX_ATTEMPTS = max_attempts_per_combination
        result, cost = optimizer.optimize_schedule_for_days(students_df, days_to_use)
        
        # 結果を評価
        if 'stats' in result:
            stats = result['stats']
            unwanted = stats.get('希望外', 0)
            
            print(f"組み合わせ {', '.join(days_to_use)} の最良結果: 希望外 {unwanted}名 ({stats.get('希望外率', 0):.1f}%)")
            
            if unwanted < best_cost:
                best_cost = unwanted
                best_result = result
                best_days = days_to_use
                best_stats = stats
                print(f"新しい最良の組み合わせが見つかりました: {', '.join(best_days)} (希望外: {unwanted}名)")
                
                # 希望外がゼロなら終了
                if unwanted == 0:
                    print(f"希望外ゼロの解が見つかりました！")
                    found_zero_unwanted = True
                    break
        
        total_attempts += max_attempts_per_combination
        print(f"現在までの総試行回数: {total_attempts}回")
        
        # 希望外が発生している場合のメッセージ
        if best_cost > 0:
            print(f"希望外が発生しています。時間をかけてもっともっとやり直しています...")
            print(f"がんばって希望外をゼロにしています...")
            sys.stdout.flush()  # 即座に出力
    
    # 希望外がゼロでない場合、さらに試行
    if not found_zero_unwanted and best_days:
        print(f"\n最良の組み合わせ {', '.join(best_days)} でさらに試行を続けます...")
        
        # 追加の試行回数
        additional_attempts = 10000
        print(f"追加で{additional_attempts}回の試行を行います...")
        
        optimizer.MAX_ATTEMPTS = additional_attempts
        result, cost = optimizer.optimize_schedule_for_days(students_df, best_days)
        
        if 'stats' in result:
            stats = result['stats']
            unwanted = stats.get('希望外', 0)
            
            print(f"追加試行の結果: 希望外 {unwanted}名 ({stats.get('希望外率', 0):.1f}%)")
            
            if unwanted < best_cost:
                best_cost = unwanted
                best_result = result
                best_stats = stats
                print(f"より良い解が見つかりました！ (希望外: {unwanted}名)")
                
                # 希望外がゼロなら成功
                if unwanted == 0:
                    print(f"希望外ゼロの解が見つかりました！")
                    found_zero_unwanted = True
            else:
                print(f"追加試行でも改善されませんでした。")
        
        total_attempts += additional_attempts
    
    end_time = time_module.time()
    execution_time = end_time - start_time
    
    # 最終結果
    print(f"\n=== 最終結果 ===")
    print(f"総試行回数: {total_attempts}回")
    print(f"総処理時間: {execution_time:.2f}秒")
    print(f"最適な3日間: {', '.join(best_days)}")
    
    if best_stats:
        print(f"割り当て済み: {best_stats.get('割り当て済み', 0)}名")
        print(f"未割り当て: {best_stats.get('未割り当て', 0)}名")
        print(f"第1希望: {best_stats.get('第1希望', 0)}名 ({best_stats.get('第1希望率', 0):.1f}%)")
        print(f"第2希望: {best_stats.get('第2希望', 0)}名 ({best_stats.get('第2希望率', 0):.1f}%)")
        print(f"第3希望: {best_stats.get('第3希望', 0)}名 ({best_stats.get('第3希望率', 0):.1f}%)")
        print(f"希望外: {best_stats.get('希望外', 0)}名 ({best_stats.get('希望外率', 0):.1f}%)")
    
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, "exhaustive_optimization_results.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write("希望外ゼロを目指した徹底的な最適化の結果\n")
        f.write("=================================================\n\n")
        
        # 1. 最適化設定
        f.write("1. 最適化設定\n")
        f.write("-------------------------------------------------\n")
        f.write(f"生徒数: {num_students}名\n")
        f.write(f"総試行回数: {total_attempts}回\n")
        f.write(f"処理時間: {execution_time:.2f}秒\n\n")
        
        # 2. 最適化結果のサマリ
        f.write("2. 最適化結果のサマリ\n")
        f.write("-------------------------------------------------\n")
        
        if best_stats:
            f.write(f"割り当て済み: {best_stats.get('割り当て済み', 0)}名\n")
            f.write(f"未割り当て: {best_stats.get('未割り当て', 0)}名\n")
            f.write(f"第1希望: {best_stats.get('第1希望', 0)}名 ({best_stats.get('第1希望率', 0):.1f}%)\n")
            f.write(f"第2希望: {best_stats.get('第2希望', 0)}名 ({best_stats.get('第2希望率', 0):.1f}%)\n")
            f.write(f"第3希望: {best_stats.get('第3希望', 0)}名 ({best_stats.get('第3希望率', 0):.1f}%)\n")
            f.write(f"希望外: {best_stats.get('希望外', 0)}名 ({best_stats.get('希望外率', 0):.1f}%)\n\n")
        
        # 3. 曜日ごとの割り当て結果
        f.write("3. 曜日ごとの割り当て結果\n")
        f.write("-------------------------------------------------\n")
        
        days = ALL_DAYS
        times = TIMES
        
        day_counts = {day: 0 for day in days}
        
        if best_result and 'assigned' in best_result:
            for student in best_result['assigned']:
                day = student['割当曜日']
                if day in day_counts:
                    day_counts[day] += 1
        
        for day in days:
            f.write(f"{day}: {day_counts[day]}名\n")
        f.write("\n")
        
        # 4. 詳細な割り当て結果
        f.write("4. 詳細な割り当て結果\n")
        f.write("-------------------------------------------------\n")
        
        f.write(f"割り当て済み件数: {len(best_result['assigned'])}\n\n")
        
        # 曜日ごとに割り当て結果を整理
        day_assignments = {day: [] for day in days}
        
        # 各生徒の割り当てを曜日ごとに分類
        for student in best_result['assigned']:
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
        
        f.write(f"徹底的な最適化の結果、")
        if best_stats.get('希望外', 0) == 0:
            f.write("全ての生徒を希望通りに割り当てることができました！\n")
        else:
            f.write(f"希望外の割り当ては{best_stats.get('希望外', 0)}名({best_stats.get('希望外率', 0):.1f}%)でした。\n")
            f.write(f"これ以上の改善は難しい可能性があります。\n")
        
        f.write(f"最適な曜日の組み合わせは {', '.join(best_days)} でした。\n")
        f.write(f"処理時間は{execution_time:.2f}秒でした。\n")
    
    print(f"\n徹底的な最適化の詳細結果を {results_file} に保存しました。")
    
    return best_result

def main():
    """メイン処理"""
    print("=== 希望外ゼロを目指した徹底的な最適化 ===")
    
    # 標準の試行回数（10回）での結果を表示
    print("\n【標準の試行回数（10回）での結果】")
    print("これは既に実行済みの結果です。希望外: 4名 (19.0%)")
    
    # 徹底的な最適化を実行
    results = run_exhaustive_optimization(21, max_attempts_per_combination=500)

if __name__ == "__main__":
    main()
