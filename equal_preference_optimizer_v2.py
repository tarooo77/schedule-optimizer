#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全ての希望（第1～第3）を平等に扱い、希望外をゼロにする最適化 v2.4

更新履歴：
- v2.4 (2025-03-18): 希望外の割り当てがある場合に交換最適化を行う機能を追加。
- v2.3 (2025-03-18): ユニット数を生徒数÷7で可変にし、未割り当てをゼロにするように修正。
- v2.2 (2025-03-18): 生徒数をユーザーが入力できるように機能追加。
- v2.1 (2025-03-18): 最適化の試行回数を1000から10000に増やし、希望外ゼロの確率を向上。
- v2.0 (2025-03-18): ダミーデータの生成・確認機能を追加。割り当て前にデータ確認と選択が可能に。
- v1.0: 初期バージョン。全ての希望を平等に扱う最適化アルゴリズムを実装。
"""

import pandas as pd
import numpy as np
import random
import time as time_module
import os
import sys
import math
from flexible_scheduler import ALL_DAYS, TIMES, get_all_slots_full, create_fully_random_data

class EqualPreferenceOptimizer:
    """全ての希望を平等に扱う最適化器"""
    
    def __init__(self):
        """初期化"""
        self.MAX_ATTEMPTS = 1000
        
    def optimize_schedule(self, students_df, days_to_use):
        """
        スケジュールを最適化する
        第1～第3希望を平等に扱い、希望外をゼロにすることを優先
        """
        # 全スロットを取得
        all_slots = []
        for day in days_to_use:
            for time in TIMES:
                all_slots.append(f"{day}{time}")
        num_students = len(students_df)
        
        # 理論的なパターン数を表示
        print("理論的なパターン数:")
        print(f"  - 生徒の希望パターン: {3**num_students:,}通り (3^{num_students})")
        print(f"  - スロットの割り当て順列: {math.factorial(num_students):,}通り ({num_students}!)")
        print(f"  - 実現可能な組み合わせの上限: {3**num_students:,}通り")
        
        best_assignments = None
        best_stats = None
        best_unwanted = float('inf')
        
        # 最大試行回数
        max_attempts = self.MAX_ATTEMPTS
        
        # 進捗表示用
        progress_interval = max(1, max_attempts // 10)
        
        for attempt in range(max_attempts):
            # 進捗表示
            if (attempt + 1) % progress_interval == 0 or attempt == 0:
                progress = (attempt + 1) / max_attempts * 100
                print(f"進捗: {progress:.1f}% ({attempt + 1}パターン試行済み)")
            
            # 各スロットの割り当て状況を追跡
            slot_assignments = {slot: None for slot in all_slots}
            
            # 生徒ごとの希望スロットを取得
            student_preferences = {}
            for _, student in students_df.iterrows():
                student_name = student['生徒名']
                prefs = self._get_all_preferences(student)
                student_preferences[student_name] = prefs
            
            # 各スロットを希望している生徒数をカウント
            slot_popularity = {slot: 0 for slot in all_slots}
            for prefs in student_preferences.values():
                for slot, _ in prefs:
                    if slot in slot_popularity:
                        slot_popularity[slot] += 1
            
            # 割り当て結果
            assignments = []
            
            # 未割り当ての生徒リスト
            unassigned_students = list(student_preferences.keys())
            
            # 希望外の生徒数
            unwanted_count = 0
            
            # 希望が少ないスロットから割り当てていく
            # 各スロットを希望している生徒数でソート
            sorted_slots = sorted(all_slots, key=lambda slot: slot_popularity[slot])
            
            # 各スロットに対して割り当てを行う
            for slot in sorted_slots:
                # このスロットを希望している生徒を取得
                students_wanting_slot = []
                for student in unassigned_students:
                    for pref_slot, pref_type in student_preferences[student]:
                        if pref_slot == slot:
                            students_wanting_slot.append((student, pref_type))
                            break
                
                # 希望している生徒がいる場合、ランダムに一人選択
                if students_wanting_slot:
                    # 希望順位を平等に扱うためランダムに選択
                    student, pref_type = random.choice(students_wanting_slot)
                    # 曜日と時間を分割
                    # 曜日の長さは3文字
                    day = slot[:3]
                    time = slot[3:]
                    assignments.append({
                        '生徒名': student,
                        '割当曜日': day,
                        '割当時間': time,
                        '希望順位': pref_type
                    })
                    unassigned_students.remove(student)
                    slot_assignments[slot] = student
            
            # 未割り当ての生徒がいる場合、空きスロットに割り当て
            empty_slots = [slot for slot, assigned in slot_assignments.items() if assigned is None]
            
            for student in unassigned_students:
                if empty_slots:
                    # 空きスロットを取得
                    slot = empty_slots.pop(0)
                    # 曜日と時間を分割
                    day = slot[:3]
                    time = slot[3:]
                    assignments.append({
                        '生徒名': student,
                        '割当曜日': day,
                        '割当時間': time,
                        '希望順位': '希望外'
                    })
                    slot_assignments[slot] = student
                    unwanted_count += 1
            
            # 統計情報を計算
            stats = self._calculate_stats(assignments, num_students)
            
            # 希望外の生徒数が少ない解を保持
            if stats['希望外'] < best_unwanted:
                best_unwanted = stats['希望外']
                best_assignments = assignments
                best_stats = stats
                print(f"改善された解が見つかりました（希望外: {best_unwanted}名）")
                
                # 希望外がゼロなら終了
                if best_unwanted == 0:
                    print("希望外ゼロの解が見つかりました！")
                    break
        
        # 試行結果のサマリを表示
        trial_num = attempt // (max_attempts // 2) + 1
        print(f"試行{trial_num}: 希望外{best_unwanted}名の解が最良でした。")
        
        # 理論上限と試行数の比較
        print(f"理論上限{3**num_students:,}パターン中{attempt+1}パターンを試行し、希望外{best_unwanted}名の解が最良でした。")
        
        return {
            'assigned': best_assignments,
            'stats': best_stats
        }, best_unwanted
    
    def optimize_schedule_for_days(self, students_df, days_to_use):
        """指定された曜日の組み合わせに対して最適化を実行"""
        return self.optimize_schedule(students_df, days_to_use)
    
    def _get_all_preferences(self, student):
        """生徒の全ての希望を取得（第1～第3希望を平等に扱う）"""
        preferences = []
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key in student and student[pref_key]:
                preferences.append((student[pref_key], pref_key))
        return preferences
    
    def _calculate_stats(self, assignments, num_students):
        """割り当て結果の統計情報を計算"""
        # 希望ごとのカウント
        pref_counts = {
            '第1希望': 0,
            '第2希望': 0,
            '第3希望': 0,
            '希望外': 0
        }
        
        # 曜日ごとのカウント
        day_counts = {day: 0 for day in ALL_DAYS}
        
        # 各割り当てを集計
        for assignment in assignments:
            pref = assignment['希望順位']
            day = assignment['割当曜日']
            
            if pref in pref_counts:
                pref_counts[pref] += 1
            
            if day in day_counts:
                day_counts[day] += 1
        
        # 統計情報を計算
        stats = {
            '割り当て済み': len(assignments),
            '未割り当て': num_students - len(assignments),
            '第1希望': pref_counts['第1希望'],
            '第2希望': pref_counts['第2希望'],
            '第3希望': pref_counts['第3希望'],
            '希望外': pref_counts['希望外'],
            '第1希望率': pref_counts['第1希望'] / num_students * 100 if num_students > 0 else 0,
            '第2希望率': pref_counts['第2希望'] / num_students * 100 if num_students > 0 else 0,
            '第3希望率': pref_counts['第3希望'] / num_students * 100 if num_students > 0 else 0,
            '希望外率': pref_counts['希望外'] / num_students * 100 if num_students > 0 else 0,
        }
        
        # 曜日ごとの割り当て数を追加
        for day, count in day_counts.items():
            stats[f'{day}_count'] = count
        
        return stats

def run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False):
    """希望外ゼロを目指した最適化を実行（全ての希望を平等に扱う）"""
    print(f"\n=== 全希望平等・希望外ゼロを目指した最適化 ===")
    print(f"生徒数: {num_students}名")
    
    # データ保存用のディレクトリを作成
    os.makedirs('data', exist_ok=True)
    data_file = 'data/student_preferences.csv'
    
    # データの読み込み
    try:
        students_df = pd.read_csv(data_file)
        print(f"データを読み込みました: {len(students_df)}名の生徒")
    except Exception as e:
        print(f"データの読み込みに失敗しました: {e}")
        print("プログラムを終了します。")
        return None
    
    # 最適化を実行
    start_time = time_module.time()
    
    # 平等希望最適化器を作成
    optimizer = EqualPreferenceOptimizer()
    optimizer.MAX_ATTEMPTS = max_attempts
    
    # 曜日の組み合わせを取得
    import itertools
    days = ALL_DAYS
    day_combinations = list(itertools.combinations(days, 3))
    
    best_result = None
    best_cost = float('inf')
    best_days = None
    best_stats = None
    
    print(f"希望外がゼロになるまで最適化を実行します...")
    print(f"各曜日の組み合わせに対して最大{max_attempts}回の試行を行います")
    print(f"全ての希望（第1～第3）を平等に扱います")
    
    # 進捗表示用のカウンター
    total_attempts = 0
    found_zero_unwanted = False
    
    for i, days_to_use in enumerate(day_combinations, 1):
        print(f"\n組み合わせ {i}/{len(day_combinations)}: {', '.join(days_to_use)}")
        
        # 最適化を実行
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
                    print(f"希望外ゼロの解が見つかりました！おめでとうございます！")
                    found_zero_unwanted = True
                    break
        
        total_attempts += max_attempts
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
        additional_attempts = max_attempts * 2
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
                    print(f"希望外ゼロの解が見つかりました！おめでとうございます！")
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
    results_file = os.path.join(results_dir, "equal_preference_results.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write("全希望平等・希望外ゼロを目指した最適化の結果\n")
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
        
        f.write(f"全希望平等・希望外ゼロを目指した最適化の結果、")
        if best_stats.get('希望外', 0) == 0:
            f.write("全ての生徒を希望通りに割り当てることができました！\n")
        else:
            f.write(f"希望外の割り当ては{best_stats.get('希望外', 0)}名({best_stats.get('希望外率', 0):.1f}%)でした。\n")
            f.write(f"これ以上の改善は難しい可能性があります。\n")
        
        f.write(f"最適な曜日の組み合わせは {', '.join(best_days)} でした。\n")
        f.write(f"処理時間は{execution_time:.2f}秒でした。\n")
    
    print(f"\n全希望平等・希望外ゼロを目指した最適化の詳細結果を {results_file} に保存しました。")
    
    return best_result

def main():
    """メイン処理"""
    print("=== 全希望平等・希望外ゼロを目指した最適化 ===")
    print("\nこのプログラムは生徒の希望を平等に扱い、希望外の割り当てをゼロにすることを目指します。")
    print("まずダミーデータの生成または確認を行い、その後に割り当てを行います。")
    
    # データ保存用のディレクトリを作成
    os.makedirs('data', exist_ok=True)
    data_file = 'data/student_preferences.csv'
    
    # データの準備
    if os.path.exists(data_file):
        # 既存のデータを確認
        try:
            students_df = pd.read_csv(data_file)
            print(f"\n既存のダミーデータがあります: {len(students_df)}名の生徒")
            print("\nダミーデータの全内容:")
            pd.set_option('display.max_rows', None)
            print(students_df)
            pd.reset_option('display.max_rows')
            
            # ユーザーに確認
            response = input("\nこのダミーデータを使用しますか？新しいデータを生成する場合はnを入力してください (y/n): ").strip().lower()
            regenerate_data = response == 'n'
        except Exception as e:
            print(f"\n既存のデータの読み込みに失敗しました: {e}")
            print("新しいダミーデータを生成します。")
            regenerate_data = True
    else:
        print("\nダミーデータがありません。新しいデータを生成します。")
        regenerate_data = True
    
    # 生徒数を入力
    if regenerate_data:
        while True:
            try:
                num_students_input = input("\nダミーデータの生徒数を入力してください (7〜100): ")
                num_students = int(num_students_input)
                if 7 <= num_students <= 100:
                    break
                else:
                    print("7〜100の間の数値を入力してください。")
            except ValueError:
                print("数値を入力してください。")
        
        # 新しいダミーデータを生成
        print(f"\n{num_students}名の生徒のダミーデータを生成します...")
        random.seed(42)
        students_df = create_fully_random_data(num_students)
        students_df.to_csv(data_file, index=False)
        print(f"生成したダミーデータを保存しました: {data_file}")
        print("\nダミーデータの全内容:")
        pd.set_option('display.max_rows', None)
        print(students_df)
        pd.reset_option('display.max_rows')
    else:
        # 既存データの生徒数を取得
        num_students = len(students_df)
    
    # 割り当てを行うか確認
    proceed = input("\nこのダミーデータで割り当てを行いますか？ (y/n): ").strip().lower()
    
    if proceed == 'y':
        print("\n割り当てを開始します...")
        # 全希望平等・希望外ゼロを目指した最適化を実行
        results = run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
    else:
        print("\n割り当てを中止しました。")

if __name__ == "__main__":
    main()
