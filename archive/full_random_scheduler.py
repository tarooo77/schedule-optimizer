#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
完全ランダムなスケジュール最適化（全曜日対応版）
"""

import pandas as pd
import numpy as np
import random
import os
import time as time_module
from schedule_optimizer_compact import ScheduleOptimizer
from utils_enhanced import TIMES, DAYS, get_all_slots_full, validate_preferences

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

class EnhancedScheduleOptimizer(ScheduleOptimizer):
    """
    スケジュール最適化クラス（拡張版）
    全ての曜日（火曜から金曜）を使用
    """
    
    def optimize_schedule(self, preferences_df):
        """スケジュールの最適化を実行（拡張版）"""
        # 入力データの検証
        validate_preferences(preferences_df)
        
        students = preferences_df.to_dict('records')
        num_students = len(students)
        
        # 生徒数に関わらず全てのスロットを使用
        self.all_slots = get_all_slots_full()
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
        
        # 最適化アルゴリズムの実行（親クラスの実装を継続）
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
                    if slot_assignments[slot] is None:
                        # スロットが空いていれば割り当て
                        day, time = slot.split('日', 1)
                        day = f"{day}日"
                        
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
                    if assigned:
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
        
        return best_assignments

def main():
    # 結果を保存するディレクトリを作成
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 結果ファイルのパス
    results_file = os.path.join(results_dir, "full_random_schedule_results.txt")
    
    # 結果をファイルに書き込む
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("=================================================\n")
        f.write("完全ランダムなスケジュール最適化の詳細プロセスと結果（全曜日対応版）\n")
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
        optimizer = EnhancedScheduleOptimizer()
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
        
        days = DAYS
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
        
        # 9. 改善点
        f.write("9. 改善点\n")
        f.write("-------------------------------------------------\n")
        
        f.write("今回の実装では、以下の改善を行いました：\n")
        f.write("1. 生徒数に関わらず全ての曜日（火曜日から金曜日）を使用\n")
        f.write("2. 各曜日のスロット数を柔軟に設定可能\n")
        f.write("3. 全てのスロットを使用可能\n\n")
        
        f.write("これにより、より柔軟なスケジュール最適化が可能になりました。\n")
    
    print(f"\n完全ランダムな詳細結果（全曜日対応版）を {results_file} に保存しました。")
    print("以下のコマンドで結果を確認できます:")
    print(f"less {results_file}")

if __name__ == "__main__":
    main()
