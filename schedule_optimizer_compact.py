#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール最適化プログラム (Compact Version)

最適化アルゴリズムのコアロジックに特化したバージョン。
データ生成やユーティリティ関数は別ファイルに分離。
"""

import pandas as pd
import numpy as np
import random
from scipy.optimize import linear_sum_assignment
from utils import DEFAULT_PREFERENCE_COSTS, TIMES, get_all_slots, validate_preferences


class ScheduleOptimizer:
    """スケジュール最適化クラス"""
    
    def __init__(self, preference_costs=None):
        """初期化処理"""
        # 基本設定
        self.TIMES = TIMES
        self.all_slots = None  # optimize_scheduleで生徒数に基づいて設定
        
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
                
                # 上位5件のみを処理
                for student, pref_type in interested_students[:5]:
                    if student['生徒名'] not in assignments:
                        # 他の生徒との交換を試みる
                        for assigned_student, assignment in assignments.items():
                            if assignment['slot'] == slot:
                                # 交換可能な生徒を見つけた場合
                                other_preferences = self._get_slot_preferences(student)
                                for other_slot, _ in other_preferences:
                                    if not any(a['slot'] == other_slot for a in assignments.values()):
                                        # 交換を実行
                                        assignments[assigned_student] = {
                                            'slot': other_slot,
                                            'pref_type': pref_type
                                        }
                                        assignments[student['生徒名']] = {
                                            'slot': slot,
                                            'pref_type': '第1希望'
                                        }
                                        improved = True
                                        break
                            if improved:
                                break
                    if improved:
                        break
            iteration += 1
        
        return improved
    
    def optimize_schedule(self, preferences_df):
        """スケジュールの最適化を実行"""
        # 入力データの検証
        validate_preferences(preferences_df)
        
        students = preferences_df.to_dict('records')
        num_students = len(students)
        
        # 生徒数に基づいてスロットを生成
        self.all_slots = get_all_slots(num_students)
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
        
        # 最大2回まで全体の最適化を試行
        max_attempts = 2
        for retry in range(max_attempts):
            best_assignments = None
            min_unwanted = float('inf')
            original_penalty = self.PREFERENCE_COSTS['希望外']
            
            # 各試行での最適化
            attempt = 0
            while attempt < self.MAX_ATTEMPTS:
                # コスト行列を作成（生徒×スロット）
                cost_matrix = np.full((num_students, num_slots), 1000.0)  # 初期値を希望外コストに設定
                
                # 各生徒の各スロットに対するコストを計算
                for i, student in enumerate(students):
                    # 各生徒の希望スロットのみコストを設定
                    for pref_num in [1, 2, 3]:
                        pref_key = f'第{pref_num}希望'
                        if pref_key in student:
                            slot = student[pref_key]
                            j = self.all_slots.index(slot)
                            cost_matrix[i, j] = self.PREFERENCE_COSTS[pref_key] + random.random() * 0.01
                
                row_ind, col_ind = linear_sum_assignment(cost_matrix)
                
                # 割り当て結果を保存
                assignments = {}
                unwanted_count = 0
                slot_assignments = {slot: [] for slot in self.all_slots}
                
                # スロットごとの割り当て数をカウント
                slot_counts = {slot: 0 for slot in self.all_slots}
                
                for i, student in enumerate(students):
                    student_name = student['生徒名']
                    # 割り当てられたスロットを取得
                    assigned_slot = self.all_slots[col_ind[i]]
                    
                    # スロットの重複チェック
                    if slot_counts[assigned_slot] >= 1:
                        # スロットの重複がある場合は、この解をスキップ
                        unwanted_count = float('inf')  # 最悪のコストを設定
                        break
                    
                    slot_counts[assigned_slot] += 1
                    slot_assignments[assigned_slot].append(student_name)  # スロットに生徒を割り当て
                    
                    # 割り当てられたスロットが希望のどれに該当するか確認
                    pref_type = '希望外'
                    for pref_num in [1, 2, 3]:
                        pref_key = f'第{pref_num}希望'
                        if pref_key in student and student[pref_key] == assigned_slot:
                            pref_type = pref_key
                            break
                    
                    if pref_type == '希望外':
                        unwanted_count += 1
                    
                    assignments[student_name] = {
                        'slot': assigned_slot,
                        'pref_type': pref_type
                    }
                
                # 未使用スロットのチェック
                unused_slots = [slot for slot, count in slot_counts.items() if count == 0]
                if unused_slots:
                    print(f"エラー: 未使用のスロットがあります: {unused_slots}")
                    continue
                
                # より良い解が見つかった場合は更新
                if unwanted_count < min_unwanted:
                    min_unwanted = unwanted_count
                    best_assignments = assignments.copy()
                    
                    if unwanted_count == 0:
                        print(f"最適な解が見つかりました！（試行回数: {attempt + 1}回）")
                        break
                    else:
                        print(f"改善された解が見つかりました（希望外: {unwanted_count}名）")
                
                # コストを動的に調整し、ランダム性を加える
                if unwanted_count > 0:
                    self.PREFERENCE_COSTS['希望外'] *= (1.1 + random.random() * 0.1)  # 1.1〜1.2倍
                    # 各希望のコストにも少しのランダム性を加える
                    for pref in ['第1希望', '第2希望', '第3希望']:
                        self.PREFERENCE_COSTS[pref] *= (0.95 + random.random() * 0.1)  # 0.95〜1.05倍
                
                attempt += 1
                if attempt % 10 == 0:  # 10回ごとに進捗を表示
                    progress = (retry * self.MAX_ATTEMPTS + attempt) / (max_attempts * self.MAX_ATTEMPTS) * 100
                    print(f"進捗: {progress:.1f}% ({retry * self.MAX_ATTEMPTS + attempt:,}パターン試行済み)")
        
            if attempt >= self.MAX_ATTEMPTS:
                if best_assignments is None:
                    print(f"試行{retry + 1}: 有効な解が見つかりませんでした。")
                    break
                else:
                    print(f"試行{retry + 1}: 希望外{min_unwanted}名の解が最良でした。")
            
            # 希望外の生徒がいない場合は終了
            if min_unwanted == 0:
                print(f"試行{retry + 1}で希望外0名の解が見つかりました！")
                break
            
            # ペナルティを元に戻す
            self.PREFERENCE_COSTS['希望外'] = original_penalty
        
        # 全試行が終了した場合、最良の結果を使用
        if min_unwanted > 0:
            total_attempts = max_attempts * self.MAX_ATTEMPTS
            print(f"理論上限{theoretical_patterns:,}パターン中{total_attempts:,}パターンを試行し、希望外{min_unwanted}名の解が最良でした。")
        
        # 結果を整形
        assigned = []
        unassigned = []
        
        for student in students:
            result = {
                '生徒名': student['生徒名'],
                '割当曜日': None,
                '割当時間': None,
                '希望順位': None
            }
            
            assignment = best_assignments.get(student['生徒名'])
            if assignment:
                slot_str = assignment['slot']
                # 割り当てられた時間枠から曜日と時間を分離
                for time in self.TIMES:
                    if slot_str.endswith(time):
                        day = slot_str[:-len(time)]
                        result['割当曜日'] = day
                        result['割当時間'] = time
                        break
                
                result['希望順位'] = assignment['pref_type']
                assigned.append(result)
            else:
                unassigned.append(result)
        
        return {'assigned': assigned, 'unassigned': unassigned}
