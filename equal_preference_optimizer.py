#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全ての希望（第1～第3）を平等に扱い、希望外をゼロにする最適化 v2.5

更新履歴：
- v2.5 (2025-03-18): ランダム性を向上させ、毎回異なるデータセットと最適化結果が得られるように改善。
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
from swap_optimizer import apply_swap_optimization
from flexible_scheduler import ALL_DAYS, TIMES, get_all_slots_full, create_fully_random_data
from typing import Dict, List, Tuple

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
            # 各試行ごとに異なるランダムシードを設定
            random.seed(time_module.time() + attempt)
            
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
            
            # 全ての生徒を割り当てる必要がある
            # 空きスロットが足りない場合はこの解を使わない
            if len(empty_slots) < len(unassigned_students):
                # 割り当てられない生徒がいる場合はこの解をスキップ
                continue
                
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
        
        # best_unwantedがinfinityの場合は特別な表示にする
        if best_unwanted == float('inf'):
            print(f"試行{trial_num}: 有効な解が見つかりませんでした。")
            print(f"理論上限{3**num_students:,}パターン中{attempt+1}パターンを試行しましたが、有効な解は見つかりませんでした。")
        else:
            print(f"試行{trial_num}: 希望外{best_unwanted}名の解が最良でした。")
            print(f"理論上限{3**num_students:,}パターン中{attempt+1}パターンを試行し、希望外{best_unwanted}名の解が最良でした。")
        
        return {
            'assigned': best_assignments,
            'stats': best_stats
        }, best_unwanted
    
    def optimize_schedule_for_days(self, students_df, days_to_use):
        """指定された曜日の組み合わせに対して最適化を実行"""
        try:
            result = self.optimize_schedule(students_df, days_to_use)
            # 結果が有効か確認
            if result and isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                # 有効な結果が得られなかった場合は空の結果を返す
                return {'assigned': [], 'stats': {'\u5e0c\u671b\u5916': float('inf')}}, float('inf')
        except Exception as e:
            print(f"最適化中にエラーが発生しました: {e}")
            # エラーが発生した場合は空の結果を返す
            return {'assigned': [], 'stats': {'\u5e0c\u671b\u5916': float('inf')}}, float('inf')
    
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
        
        # 割り当てられた生徒を追跡
        assigned_students = set()
        
        # 各割り当てを集計
        for assignment in assignments:
            student_name = assignment['生徒名']
            assigned_students.add(student_name)
            
            pref = assignment['希望順位']
            day = assignment['割当曜日']
            
            if pref in pref_counts:
                pref_counts[pref] += 1
            
            if day in day_counts:
                day_counts[day] += 1
                
        # 実際に割り当てられた生徒数
        actually_assigned = len(assigned_students)
        
        # 統計情報を計算
        stats = {
            '割り当て済み': actually_assigned,
            '未割り当て': num_students - actually_assigned,
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

def save_assignments_to_csv(assignments, csv_file):
    """割り当て結果をCSVファイルに保存する"""
    # CSVファイル用のデータフレームを作成
    data = []
    for assignment in assignments:
        if isinstance(assignment, dict):
            student = assignment.get('生徒名')
            day = assignment.get('割当曜日')
            time = assignment.get('割当時間')
            pref = assignment.get('希望順位')
            if student and day and time:
                slot = f"{day}{time}"
                row = {
                    '生徒名': student,
                    '割り当て時間': slot,
                    '希望順位': pref,
                    '火曜日': slot if day == '火曜日' else None,
                    '水曜日': slot if day == '水曜日' else None,
                    '木曜日': slot if day == '木曜日' else None,
                    '金曜日': slot if day == '金曜日' else None
                }
                data.append(row)
    
    # データフレームを作成してCSVに保存
    if data:
        df = pd.DataFrame(data)
        # 列の順序を整理
        columns = ['生徒名', '割り当て時間', '希望順位', '火曜日', '水曜日', '木曜日', '金曜日']
        df = df[columns]
        # CSVに保存
        df.to_csv(csv_file, index=False, encoding='utf-8')
        return True
    return False

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
    
    # 生徒数から必要なユニット数を計算
    import itertools
    import math
    days = ALL_DAYS
    # 生徒数を7で割って切り上げ、必要なユニット数を求める
    units_needed = math.ceil(num_students / 7)
    print(f"生徒数 {num_students} 名に対して必要なユニット数: {units_needed} ユニット")
    
    # 必要なユニット数に基づいて曜日の組み合わせを取得
    if units_needed <= 3:
        # 3ユニット以下の場合は、4日間から必要な日数を選ぶ
        day_combinations = list(itertools.combinations(days, units_needed))
        print(f"3ユニット以下: {len(day_combinations)}通りの組み合わせを試します")
    elif units_needed == 4:
        # 4ユニットの場合は、全ての曜日を使用
        day_combinations = [tuple(days)]
        print(f"4ユニット: 全ての曜日を使用します")
    else:
        # 5ユニット以上の場合
        # まず基本の4日間（火・水・木・金）を使用
        # 残りのユニットは「火(2)・水(2)・木(2)・金(2)」から必要な日数を選ぶ
        
        # 残りのユニット数を計算
        remaining_units = units_needed - 4  # 基本の4日間を使用した後の残り
        print(f"5ユニット以上: 基本の4日間 + 残り{remaining_units}ユニットを考慮します")
        
        # 第2序列の曜日リストを作成 (各曜日の2回目)
        second_days = [f"{day}(2)" for day in days]
        
        # 残りのユニット数に基づいて、第2序列の曜日から必要な日数を選ぶ
        second_combinations = list(itertools.combinations(second_days, remaining_units))
        print(f"第2序列の曜日から{remaining_units}日を選ぶ組み合わせ: {len(second_combinations)}通り")
        
        # 基本の4日間と第2序列の組み合わせを結合
        day_combinations = []
        base_days = list(days)  # 基本の4日間
        
        for second_combo in second_combinations:
            # 第2序列の曜日から元の曜日名を取得
            additional_days = [day.split('(')[0] for day in second_combo]
            # 基本の4日間と結合
            combined_days = base_days + additional_days
            day_combinations.append(tuple(combined_days))
        
        # 最初の組み合わせを表示
        if day_combinations:
            first_combination = day_combinations[0]
            day_counts = {day: first_combination.count(day) for day in days}
            print(f"例: {first_combination} (曜日ごとの使用回数: {day_counts})")
    
    best_result = None
    best_cost = float('inf')
    best_days = None
    best_stats = None
    
    print(f"希望外がゼロになるまで最適化を実行します...")
    print(f"各曜日の組み合わせに対して最大{max_attempts}回の試行を行います")
    print(f"全ての希望（第1～第3）を平等に扱います")
    
    # 進捗表示用のカウンター
    total_attempts = 0  # 総試行回数の初期化
    found_zero_unwanted = False
    
    # 希望外ゼロの解のリスト
    zero_unwanted_solutions = []
    
    for i, days_to_use in enumerate(day_combinations, 1):
        print(f"\n組み合わせ {i}/{len(day_combinations)}: {', '.join(days_to_use)}")
        
        # 最適化を実行
        result, cost = optimizer.optimize_schedule_for_days(students_df, days_to_use)
        
        # 結果を評価
        try:
            if result and isinstance(result, dict) and 'stats' in result and result['stats']:
                stats = result['stats']
                unwanted = stats.get('希望外', float('inf'))
                
                # float('inf')の場合は特別な表示
                if unwanted == float('inf'):
                    print(f"組み合わせ {', '.join(days_to_use)} では有効な解が得られませんでした")
                else:
                    print(f"組み合わせ {', '.join(days_to_use)} の最良結果: 希望外 {unwanted}名 ({stats.get('希望外率', 0):.1f}%)")
                    
                    # 有効な結果が得られた場合のみ評価
                    if unwanted < best_cost:
                        best_cost = unwanted
                        best_result = result
                        best_days = days_to_use
                        best_stats = stats
                        print(f"新しい最良の組み合わせが見つかりました: {', '.join(best_days)} (希望外: {unwanted}名)")
                        
                        # 希望外がゼロならリストに追加し、探索を続ける
                        if unwanted == 0:
                            print(f"希望外ゼロの解が見つかりました！おめでとうございます！")
                            found_zero_unwanted = True
                            # 希望外ゼロの解をリストに追加
                            zero_unwanted_solutions.append({
                                'days': days_to_use.copy(),
                                'result': result.copy(),
                                'stats': stats.copy()
                            })
                            # 探索を続けるのでbreakしない
            else:
                print(f"組み合わせ {', '.join(days_to_use)} では有効な結果が得られませんでした")
                continue
        except Exception as e:
            print(f"結果の評価中にエラーが発生しました: {e}")
            print(f"組み合わせ {', '.join(days_to_use)} をスキップします")
            continue
        
        # 実際に行われた試行回数を加算
        if result and isinstance(result, dict) and 'stats' in result and result['stats']:
            # 有効な結果が得られた場合、max_attemptsを加算
            total_attempts += max_attempts
        else:
            # 有効な結果が得られなかった場合も、max_attemptsを加算
            total_attempts += max_attempts
        print(f"現在までの総試行回数: {total_attempts}回")
        
        # 希望外が発生している場合のメッセージ
        if best_cost > 0:
            print(f"希望外が発生しています。時間をかけてもっともっとやり直しています...")
            print(f"がんばって希望外をゼロにしています...")
            sys.stdout.flush()  # 即座に出力
    
    # 希望外がゼロでない場合、1回だけ追加試行
    if not found_zero_unwanted and best_days and best_cost > 0:
        print(f"\n最良の組み合わせ {', '.join(best_days)} で最後の追加試行を行います...")
        
        # 追加の試行回数
        additional_attempts = max_attempts * 2
        print(f"追加で{additional_attempts}回の試行を行います...")
        
        optimizer.MAX_ATTEMPTS = additional_attempts
        result, cost = optimizer.optimize_schedule_for_days(students_df, best_days)
        
        if result and isinstance(result, dict) and 'stats' in result:
            stats = result['stats']
            unwanted = stats.get('希望外', float('inf'))
            
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
        
        # 追加試行の試行回数を加算
        total_attempts += additional_attempts
    
    end_time = time_module.time()
    execution_time = end_time - start_time
    
    # 希望外の割り当てがある場合のメッセージ
    if best_stats and best_stats.get('希望外', 0) > 0 and 'assigned' in best_result:
        print(f"\n希望外の割り当てが {best_stats.get('希望外', 0)}名 います。")
        print("ポスト最適化でさらに改善を試みます。")
    
    # 最終結果
    print(f"\n=== 最終結果 ===")
    print(f"総試行回数: {total_attempts}回")
    print(f"総処理時間: {execution_time:.2f}秒")
    if best_days and isinstance(best_days, (list, tuple)):
        print(f"最適な曜日の組み合わせ: {', '.join(best_days)}")
    else:
        print("最適な曜日の組み合わせ: 見つかりませんでした")
    
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
    
    # ポスト最適化を実行するかどうか確認
    print("\nポスト最適化を実行しますか？")
    print("1: すべての最適化手法を実行する")
    print("2: 特定の最適化手法を選択する")
    print("3: ポスト最適化を行わない")
    
    post_opt_choice = input("選択してください (1/2/3): ")
    
    if post_opt_choice == "1":
        # 全ての最適化手法を実行
        print("\nすべての最適化手法を実行します...")
        # 結果をCSVに保存
        csv_file = os.path.join(results_dir, "equal_preference_results.csv")
        save_assignments_to_csv(best_result['assigned'], csv_file)
        print(f"最適化結果をCSVファイルとして保存しました: {csv_file}")
        
        # run_all_optimizers.pyを実行
        cmd = f"python run_all_optimizers.py --input {csv_file} --preferences data/student_preferences.csv --iterations 3"
        print(f"実行コマンド: {cmd}")
        os.system(cmd)
        
        # 完了後の選択肢を表示
        print("\n最適化が完了しました。")
        print("1: 同じデータでもう一度最適化を実行する")
        print("2: 最終割り当てデータをダブルチェックする")
        print("3: 終了する")
        
        final_choice = input("選択してください (1-3): ")
        
        if final_choice == "1":
            # 同じデータで再度最適化を実行
            print("\n同じデータで再度最適化を実行します...")
            return run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
        elif final_choice == "2":
            # 最終割り当てデータをダブルチェックする
            from validation_menu import show_validation_menu
            if show_validation_menu():
                # メインメニューに戻る場合は再度最適化を実行
                return run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
        elif final_choice == "3":
            print("\nプログラムを終了します。")
            sys.exit(0)
        
    elif post_opt_choice == "2":
        # 特定の最適化手法を選択
        print("\n実行する最適化手法を選択してください:")
        print("1: 連鎖交換最適化")
        print("2: ブロックスワップ最適化")
        print("3: ターゲット最適化")
        print("4: タブーサーチ最適化")
        print("5: 遺伝的アルゴリズム最適化")
        print("6: 複合最適化")
        
        method_choice = input("選択してください (1-6): ")
        
        # 結果をCSVに保存
        csv_file = os.path.join(results_dir, "equal_preference_results.csv")
        save_assignments_to_csv(best_result['assigned'], csv_file)
        print(f"最適化結果をCSVファイルとして保存しました: {csv_file}")
        
        # 選択された最適化手法を実行
        if method_choice == "1":
            from post_assignment_optimizer import PostAssignmentOptimizer
            print("\n連鎖交換最適化を実行します...")
            optimizer = PostAssignmentOptimizer()
            assignments = pd.read_csv(csv_file)
            preferences = pd.read_csv("data/student_preferences.csv")
            result = optimizer.optimize(assignments, preferences, max_iterations=50)
            
            # 完了後の選択肢を表示
            print("\n最適化が完了しました。")
            print("1: 同じデータでもう一度最適化を実行する")
            print("2: 終了する")
            
            final_choice = input("選択してください (1/2): ")
            
            if final_choice == "1":
                # 同じデータで再度最適化を実行
                print("\n同じデータで再度最適化を実行します...")
                return run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
            elif final_choice == "2":
                print("\nプログラムを終了します。")
                sys.exit(0)
            result.to_csv(os.path.join(results_dir, "chain_exchange_results.csv"), index=False)
        elif method_choice == "2":
            from block_swap_optimizer import optimize_block_swap
            print("\nブロックスワップ最適化を実行します...")
            assignments = pd.read_csv(csv_file)
            preferences = pd.read_csv("data/student_preferences.csv")
            result = optimize_block_swap(assignments, preferences, max_attempts=10)
            result.to_csv(os.path.join(results_dir, "block_swap_results.csv"), index=False)
        elif method_choice == "3":
            from targeted_optimizer import optimize_targeted
            print("\nターゲット最適化を実行します...")
            assignments = pd.read_csv(csv_file)
            preferences = pd.read_csv("data/student_preferences.csv")
            result = optimize_targeted(assignments, preferences, max_attempts=10)
            result.to_csv(os.path.join(results_dir, "targeted_results.csv"), index=False)
        elif method_choice == "4":
            from tabu_search_optimizer import optimize_tabu_search
            print("\nタブーサーチ最適化を実行します...")
            assignments = pd.read_csv(csv_file)
            preferences = pd.read_csv("data/student_preferences.csv")
            result = optimize_tabu_search(assignments, preferences, max_iterations=50)
            result.to_csv(os.path.join(results_dir, "tabu_search_results.csv"), index=False)
        elif method_choice == "5":
            from genetic_optimizer import optimize_genetic
            print("\n遺伝的アルゴリズム最適化を実行します...")
            assignments = pd.read_csv(csv_file)
            preferences = pd.read_csv("data/student_preferences.csv")
            result = optimize_genetic(assignments, preferences, population_size=20, generations=30)
            result.to_csv(os.path.join(results_dir, "genetic_results.csv"), index=False)
        elif method_choice == "6":
            from multi_optimizer import multi_optimize
            print("\n複合最適化を実行します...")
            multi_optimize(csv_file, "data/student_preferences.csv", os.path.join(results_dir, "multi_results.csv"), iterations=3)
        else:
            print("無効な選択です。ポスト最適化をスキップします。")
    else:
        print("ポスト最適化をスキップします。")
        # 結果をCSVに保存
        csv_file = os.path.join(results_dir, "equal_preference_results.csv")
        save_assignments_to_csv(best_result['assigned'], csv_file)
        print(f"最適化結果をCSVファイルとして保存しました: {csv_file}")
        
        # 完了後の選択肢を表示
        print("\n最適化が完了しました。")
        print("1: 同じデータでもう一度最適化を実行する")
        print("2: 最終割り当てデータをダブルチェックする")
        print("3: 終了する")
        
        final_choice = input("選択してください (1-3): ")
        
        if final_choice == "1":
            # 同じデータで再度最適化を実行
            print("\n同じデータで再度最適化を実行します...")
            return run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
        elif final_choice == "2":
            # 最終割り当てデータをダブルチェックする
            from validation_menu import show_validation_menu
            if show_validation_menu():
                # メインメニューに戻る場合は再度最適化を実行
                return run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
        elif final_choice == "3":
            print("\nプログラムを終了します。")
            sys.exit(0)
    
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
    
    # 結果をCSVファイルとしても保存
    csv_result_file = os.path.join('results', 'equal_preference_results.csv')
    # save_assignments_to_csv関数を使用してCSVファイルを保存
    if best_result and isinstance(best_result, dict) and 'assigned' in best_result:
        save_assignments_to_csv(best_result['assigned'], csv_result_file)
        print(f"\n最適化結果をCSVファイルとしても保存しました: {csv_result_file}")
    else:
        print("\n警告: 有効な割り当て結果がありません。CSVファイルは作成されませんでした。")
    
    return best_result

def main():
    """メイン処理"""
    while True:
        print("\n=== 全希望平等・希望外ゼロを目指した最適化 v2.5 ===")
        print("\nこのプログラムは生徒の希望を平等に扱い、希望外の割り当てをゼロにすることを目指します。")
        
        # データタイプの選択
        print("\n使用するデータタイプを選択してください:")
        print("1. ダミーデータを使用する")
        print("2. リアルデータを入力する (現在未実装)")
        print("3. プログラムを終了する")
        
        data_choice = input("\n選択肢の番号を入力してください (1-3): ").strip()
        
        if data_choice == "3":
            print("\nプログラムを終了します。")
            break
        
        elif data_choice == "2":
            print("\nリアルデータの入力機能は現在開発中です。")
            input("Enterキーを押してメインメニューに戻ります...")
            continue
        
        elif data_choice == "1":
            # ダミーデータを使用する処理
            os.makedirs('data', exist_ok=True)
            data_file = 'data/student_preferences.csv'
            
            while True:
                print("\nダミーデータのオプション:")
                print("1. 新しいダミーデータを生成する")
                
                # 既存のデータがあれば表示
                if os.path.exists(data_file):
                    try:
                        students_df = pd.read_csv(data_file)
                        print(f"2. 既存のダミーデータを使用する ({len(students_df)}名の生徒)")
                    except Exception as e:
                        print(f"2. 既存のデータは破損しています: {e}")
                else:
                    print("2. 既存のダミーデータはありません")
                
                print("3. メインメニューに戻る")
                
                dummy_choice = input("\n選択肢の番号を入力してください (1-3): ").strip()
                
                if dummy_choice == "3":
                    # メインメニューに戻る
                    break
                
                elif dummy_choice == "1":
                    # 新しいダミーデータを生成
                    while True:
                        try:
                            num_students_input = input("\nダミーデータの生徒数を入力してください (7～100): ")
                            num_students = int(num_students_input)
                            if 7 <= num_students <= 100:
                                break
                            else:
                                print("7～100の間の数値を入力してください。")
                        except ValueError:
                            print("数値を入力してください。")
                    
                    # 新しいダミーデータを生成
                    print(f"\n{num_students}名の生徒のダミーデータを生成します...")
                    # 毎回異なるデータを生成するためにシードを設定しない
                    students_df = create_fully_random_data(num_students)
                    students_df.to_csv(data_file, index=False)
                    print(f"生成したダミーデータを保存しました: {data_file}")
                    print("\nダミーデータの全内容:")
                    pd.set_option('display.max_rows', None)
                    print(students_df)
                    pd.reset_option('display.max_rows')
                    
                    # 生成したデータで割り当てを行うか確認
                    proceed_options = [
                        "1. このデータで割り当てを行う",
                        "2. 別のデータを選択する",
                        "3. メインメニューに戻る"
                    ]
                    
                    print("\n次のオプションから選択してください:")
                    for option in proceed_options:
                        print(option)
                    
                    proceed_choice = input("\n選択肢の番号を入力してください (1-3): ").strip()
                    
                    if proceed_choice == "1":
                        # 割り当てを実行
                        print("\n割り当てを開始します...")
                        results = run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
                        
                        # 結果表示後にメインメニューに戻るか確認
                        input("\nEnterキーを押してメインメニューに戻ります...")
                        break
                    elif proceed_choice == "2":
                        # 別のデータを選択するためにループ継続
                        continue
                    else:  # proceed_choice == "3" またはその他
                        # メインメニューに戻る
                        break
                
                elif dummy_choice == "2" and os.path.exists(data_file):
                    # 既存のダミーデータを使用
                    try:
                        students_df = pd.read_csv(data_file)
                        num_students = len(students_df)
                        print("\n既存のダミーデータ:")
                        pd.set_option('display.max_rows', None)
                        print(students_df)
                        pd.reset_option('display.max_rows')
                        
                        # 既存データで割り当てを行うか確認
                        proceed_options = [
                            "1. このデータで割り当てを行う",
                            "2. 別のデータを選択する",
                            "3. メインメニューに戻る"
                        ]
                        
                        print("\n次のオプションから選択してください:")
                        for option in proceed_options:
                            print(option)
                        
                        proceed_choice = input("\n選択肢の番号を入力してください (1-3): ").strip()
                        
                        if proceed_choice == "1":
                            # 割り当てを実行
                            print("\n割り当てを開始します...")
                            results = run_equal_preference_optimization(num_students, max_attempts=10000, regenerate_data=False)
                            
                            # 結果表示後にメインメニューに戻るか確認
                            input("\nEnterキーを押してメインメニューに戻ります...")
                            break
                        elif proceed_choice == "2":
                            # 別のデータを選択するためにループ継続
                            continue
                        else:  # proceed_choice == "3" またはその他
                            # メインメニューに戻る
                            break
                    
                    except Exception as e:
                        print(f"\n既存のデータの読み込みに失敗しました: {e}")
                        input("Enterキーを押して続行します...")
                        continue
                
                else:
                    print("\n無効な選択です。再度お試しください。")
        
        else:
            print("\n無効な選択です。再度お試しください。")

if __name__ == "__main__":
    main()
