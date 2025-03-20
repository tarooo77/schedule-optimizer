#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
柔軟なスケジュール最適化プログラム
- 生徒は火曜日から金曜日までの希望を出せる
- 実際の割り当ては3ユニット（21名）なので、4日間のうち3日間だけを使用
- 最適な3日間を選択して全員を希望内に割り当てる
"""

import pandas as pd
import numpy as np
import random
import os
import time as time_module
from schedule_optimizer_compact import ScheduleOptimizer
from utils import TIMES, DEFAULT_PREFERENCE_COSTS

# 全ての曜日
ALL_DAYS = ["火曜日", "水曜日", "木曜日", "金曜日"]

def get_all_slots_full():
    """
    全ての曜日と時間帯のスロットを生成
    """
    days = ALL_DAYS
    times = TIMES
    
    all_slots = []
    for day in days:
        for time in times:
            all_slots.append(f"{day}{time}")
    
    return all_slots

def create_fully_random_data(num_students):
    """
    完全にランダムなダミーデータを生成する関数
    全ての曜日（火曜から金曜）を含む
    """
    # 全ての曜日のスロットを取得
    all_slots = get_all_slots_full()
    
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

def validate_preferences_full(preferences_df):
    """生徒の希望データをバリデーション（全曜日対応）"""
    # 全ての生徒が3つの希望を持っているか確認
    required_columns = ['生徒名', '第1希望', '第2希望', '第3希望']
    for col in required_columns:
        if col not in preferences_df.columns:
            raise ValueError(f"データフレームに必要なカラム '{col}' がありません")
    
    # 希望が有効なスロットか確認
    valid_slots = get_all_slots_full()
    
    for pref in ['第1希望', '第2希望', '第3希望']:
        invalid_slots = set(preferences_df[pref]) - set(valid_slots)
        if invalid_slots:
            raise ValueError(f"{pref}に無効なスロットが含まれています: {invalid_slots}")
    
    return True

class FlexibleScheduleOptimizer:
    """
    柔軟なスケジュール最適化クラス
    - 4日間のうち最適な3日間を選択
    """
    
    def __init__(self, preference_costs=None):
        """初期化処理"""
        # 基本設定
        self.TIMES = TIMES
        self.all_slots = None
        
        # 希望の重み付け
        self.PREFERENCE_COSTS = preference_costs or DEFAULT_PREFERENCE_COSTS.copy()
        
        # 最大試行回数
        self.MAX_ATTEMPTS = 10
        self.MAX_LOCAL_ATTEMPTS = 50
    
    def _get_slot_preferences(self, student):
        """生徒の希望時間枠を取得"""
        preferences = []
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key in student and student[pref_key]:
                preferences.append((student[pref_key], pref_key))
        return preferences
    
    def _get_students_by_slot(self, students, slot):
        """特定の時間枠を希望している生徒を取得"""
        interested_students = []
        for student in students:
            for pref, pref_type in self._get_slot_preferences(student):
                if pref == slot:
                    interested_students.append((student, pref_type))
                    break
        return interested_students
    
    def _try_local_reassignment(self, assignments, students, problem_slots):
        """局所的な再割り当てを試行"""
        improved = False
        iteration = 0
        
        # 各問題スロットに対して再割り当てを試みる
        while iteration < self.MAX_LOCAL_ATTEMPTS and not improved:
            for slot in problem_slots:
                interested_students = self._get_students_by_slot(students, slot)
                if not interested_students:
                    continue
                
                # 現在の割り当てを持つ生徒を優先度順にソート
                interested_students.sort(key=lambda x: {
                    '第1希望': 3,
                    '第2希望': 2,
                    '第3希望': 1,
                    '希望外': 0
                }[x[1]])
                
                # 各生徒について、現在の割り当てを変更できるか試みる
                for student, pref_type in interested_students:
                    # 生徒の現在の割り当てを検索
                    current_assignment = None
                    for i, assignment in enumerate(assignments):
                        if assignment['生徒名'] == student['生徒名']:
                            current_assignment = assignment
                            assignment_index = i
                            break
                    
                    if current_assignment:
                        # 現在の割り当てスロットを解放
                        current_slot = f"{current_assignment['割当曜日']}{current_assignment['割当時間']}"
                        
                        # 新しい割り当てを試みる
                        day, time = slot.split('日', 1)
                        day = f"{day}日"
                        
                        # 割り当てを更新
                        assignments[assignment_index] = {
                            '生徒名': student['生徒名'],
                            '割当曜日': day,
                            '割当時間': time,
                            '希望順位': pref_type
                        }
                        
                        improved = True
                        break
                
                if improved:
                    break
            
            iteration += 1
        
        return improved
    
    def optimize_schedule_for_days(self, preferences_df, days_to_use):
        """指定された曜日のみを使用してスケジュールを最適化"""
        # 入力データの検証
        validate_preferences_full(preferences_df)
        
        students = preferences_df.to_dict('records')
        num_students = len(students)
        
        # 指定された曜日のスロットのみを使用
        self.all_slots = []
        for day in days_to_use:
            for time in self.TIMES:
                self.all_slots.append(f'{day}{time}')
        
        num_slots = len(self.all_slots)
        
        # 理論的なパターン数を計算
        import math
        student_preferences = 3 ** num_students  # 各生徒が3つの希望から選ぶパターン
        slot_permutations = math.factorial(num_slots)  # スロットの割り当て順列
        theoretical_patterns = min(student_preferences, slot_permutations)
        print(f"理論的なパターン数:")
        print(f"  - 生徒の希望パターン: {student_preferences:,}通り (3^{num_students})")
        print(f"  - スロットの割り当て順列: {slot_permutations:,}通り ({num_slots}!)")
        print(f"  - 実現可能な組み合わせの上限: {theoretical_patterns:,}通り")
        
        # 最適化アルゴリズムの実行
        best_assignments = None
        best_cost = float('inf')
        best_stats = None
        
        # 複数回試行して最良の結果を探す
        for attempt in range(self.MAX_ATTEMPTS):
            # ランダムな順序で生徒を処理
            random.shuffle(students)
            
            # 各スロットに割り当てられた生徒を記録
            slot_assignments = {slot: None for slot in self.all_slots}
            
            # 各生徒の割り当て結果を記録
            student_assignments = []
            unassigned_students = []
            
            # 希望の種類ごとのカウント
            preference_counts = {'第1希望': 0, '第2希望': 0, '第3希望': 0, '希望外': 0}
            
            # 各生徒を処理
            for student in students:
                # 生徒の希望時間枠を取得
                preferences = self._get_slot_preferences(student)
                
                # 希望時間枠を優先度順にチェック
                assigned = False
                for slot, pref_type in preferences:
                    # 指定された曜日のスロットのみを使用
                    day = slot.split('日', 1)[0] + '日'
                    if day in days_to_use:
                        if slot in slot_assignments and slot_assignments[slot] is None:
                            # スロットが空いていれば割り当て
                            time = slot.split('日', 1)[1]
                            
                            slot_assignments[slot] = student['生徒名']
                            student_assignments.append({
                                '生徒名': student['生徒名'],
                                '割当曜日': day,
                                '割当時間': time,
                                '希望順位': pref_type
                            })
                            preference_counts[pref_type] += 1
                            assigned = True
                            break
                
                if not assigned:
                    # 全ての希望時間枠が埋まっていた場合、希望外の時間枠を探す
                    for slot in self.all_slots:
                        if slot_assignments[slot] is None:
                            day, time = slot.split('日', 1)
                            day = f"{day}日"
                            
                            slot_assignments[slot] = student['生徒名']
                            student_assignments.append({
                                '生徒名': student['生徒名'],
                                '割当曜日': day,
                                '割当時間': time,
                                '希望順位': '希望外'
                            })
                            preference_counts['希望外'] += 1
                            assigned = True
                            break
                
                if not assigned:
                    # それでも割り当てられなかった場合
                    unassigned_students.append(student['生徒名'])
            
            # 割り当て結果の評価
            total_cost = (
                self.PREFERENCE_COSTS['第1希望'] * preference_counts['第1希望'] +
                self.PREFERENCE_COSTS['第2希望'] * preference_counts['第2希望'] +
                self.PREFERENCE_COSTS['第3希望'] * preference_counts['第3希望'] +
                self.PREFERENCE_COSTS['希望外'] * preference_counts['希望外']
            )
            
            # 問題のあるスロットを特定
            problem_slots = []
            for slot, student_name in slot_assignments.items():
                if student_name is None:
                    # 未割り当てのスロット
                    problem_slots.append(slot)
            
            # 局所的な再割り当てを試行
            if problem_slots and unassigned_students:
                improved = self._try_local_reassignment(
                    student_assignments, students, problem_slots
                )
                if improved:
                    # 再割り当て後の統計を更新
                    preference_counts = {'第1希望': 0, '第2希望': 0, '第3希望': 0, '希望外': 0}
                    for assignment in student_assignments:
                        preference_counts[assignment['希望順位']] += 1
                    
                    # コストを再計算
                    total_cost = (
                        self.PREFERENCE_COSTS['第1希望'] * preference_counts['第1希望'] +
                        self.PREFERENCE_COSTS['第2希望'] * preference_counts['第2希望'] +
                        self.PREFERENCE_COSTS['第3希望'] * preference_counts['第3希望'] +
                        self.PREFERENCE_COSTS['希望外'] * preference_counts['希望外']
                    )
            
            # 現在の結果が最良かどうか確認
            if total_cost < best_cost:
                best_cost = total_cost
                best_assignments = {
                    'assigned': student_assignments,
                    'unassigned': unassigned_students
                }
                
                # 統計情報を計算
                total_assigned = len(student_assignments)
                if total_assigned > 0:
                    best_stats = {
                        '割り当て済み': total_assigned,
                        '未割り当て': len(unassigned_students),
                        '第1希望': preference_counts['第1希望'],
                        '第2希望': preference_counts['第2希望'],
                        '第3希望': preference_counts['第3希望'],
                        '希望外': preference_counts['希望外'],
                        '第1希望率': preference_counts['第1希望'] / total_assigned * 100,
                        '第2希望率': preference_counts['第2希望'] / total_assigned * 100,
                        '第3希望率': preference_counts['第3希望'] / total_assigned * 100,
                        '希望外率': preference_counts['希望外'] / total_assigned * 100
                    }
                
                # 希望外の生徒がいない場合は早期終了
                if preference_counts['希望外'] == 0:
                    print(f"完全に希望通りの解が見つかりました！")
                    break
                else:
                    print(f"改善された解が見つかりました（希望外: {preference_counts['希望外']}名）")
            
            # 進捗表示
            progress = (attempt + 1) / self.MAX_ATTEMPTS * 100
            if (attempt + 1) % (self.MAX_ATTEMPTS // 2) == 0:
                print(f"進捗: {progress:.1f}% ({attempt + 1}パターン試行済み)")
                print(f"試行{attempt // (self.MAX_ATTEMPTS // 2) + 1}: 希望外{best_stats['希望外']}名の解が最良でした。")
        
        # 最終結果
        if best_stats:
            best_assignments['stats'] = best_stats
            print(f"理論上限{theoretical_patterns:,}パターン中{self.MAX_ATTEMPTS}パターンを試行し、希望外{best_stats['希望外']}名の解が最良でした。")
        
        return best_assignments, best_cost
    
    def optimize_schedule(self, preferences_df):
        """
        最適な3日間を選択してスケジュールを最適化
        """
        # 全ての曜日の組み合わせを試す
        import itertools
        days = ALL_DAYS
        day_combinations = list(itertools.combinations(days, 3))
        
        best_result = None
        best_cost = float('inf')
        best_days = None
        
        print(f"全ての3日間の組み合わせを試行中...")
        
        for i, days_to_use in enumerate(day_combinations, 1):
            print(f"\n組み合わせ {i}/{len(day_combinations)}: {', '.join(days_to_use)}")
            result, cost = self.optimize_schedule_for_days(preferences_df, days_to_use)
            
            if cost < best_cost:
                best_cost = cost
                best_result = result
                best_days = days_to_use
                print(f"新しい最良の組み合わせが見つかりました: {', '.join(best_days)}")
        
        print(f"\n最適な3日間: {', '.join(best_days)}")
        return best_result

def main():
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, "flexible_schedule_results.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write("柔軟なスケジュール最適化の詳細プロセスと結果\n")
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
        optimizer = FlexibleScheduleOptimizer()
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
        
        # 7. まとめ
        f.write("7. まとめ\n")
        f.write("-------------------------------------------------\n")
        
        f.write("このスケジュール最適化では、21名の生徒を火曜日から金曜日の中から最適な3日間に\n")
        f.write("割り当てました。各生徒の希望を最大限考慮し、できるだけ多くの生徒が\n")
        f.write("第1希望または第2希望の時間帯に割り当てられるようにしました。\n\n")
        
        if 'stats' in results:
            stats = results['stats']
            f.write(f"第1希望達成率: {stats.get('第1希望率', 0):.1f}%\n")
            f.write(f"第2希望達成率: {stats.get('第2希望率', 0):.1f}%\n")
            f.write(f"第3希望達成率: {stats.get('第3希望率', 0):.1f}%\n")
            f.write(f"希望外割合: {stats.get('希望外率', 0):.1f}%\n\n")
        
        f.write("以上が最適化の詳細プロセスと結果です。\n")
        
        # 8. 改善点
        f.write("8. 改善点\n")
        f.write("-------------------------------------------------\n")
        
        f.write("今回の実装では、以下の改善を行いました：\n")
        f.write("1. 生徒は火曜日から金曜日までの希望を出せる\n")
        f.write("2. 実際の割り当ては3ユニット（21名）なので、4日間のうち最適な3日間だけを使用\n")
        f.write("3. 全ての曜日の組み合わせを試して、最も希望を満たせる3日間を選択\n\n")
        
        f.write("これにより、より柔軟なスケジュール最適化が可能になりました。\n")
    
    print(f"\n柔軟なスケジュール最適化の詳細結果を {results_file} に保存しました。")
    print("以下のコマンドで結果を確認できます:")
    print(f"less {results_file}")

if __name__ == "__main__":
    main()
