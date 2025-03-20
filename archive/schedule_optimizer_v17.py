#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール最適化プログラム v17

このプログラムは生徒の希望に基づいて最適なスケジュールを生成します。
生徒は28スロット（4曜日×7時間）から自由に3つの希望を選択できます。
プログラムは生徒数に応じて必要なユニット数を計算し、最も満足度の高い曜日（ユニット）を選択します。
"""

# 必要なライブラリのインポート
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import random


class ScheduleOptimizer:
    """スケジュール最適化クラス
    
    このクラスは生徒の希望に基づいて最適なスケジュールを生成します。
    生徒数が多い場合は、複数のユニット（曜日）に分けて割り当てを行います。
    """
    
    def __init__(self):
        """初期化処理
        
        曜日、時間、希望の重み付けなどの基本設定を行います。
        """
        # 基本設定
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        
        # 全スロットを生成（28スロット）
        self.all_slots = []
        for day in self.DAYS:
            for time in self.TIMES:
                self.all_slots.append(f'{day}{time}')
        
        # 各曜日のスロットを記憶
        self.day_slots = {}
        for day in self.DAYS:
            self.day_slots[day] = [f'{day}{time}' for time in self.TIMES]
        
        # 希望の重み付け - 第1〜第3希望をまんべんなく活用するため、値を近づけています
        self.PREFERENCE_COSTS = {
            '第1希望': -10,  # 第1希望はコストが低い
            '第2希望': -9,   # 第2希望もほぼ同等に評価
            '第3希望': -8,   # 第3希望もほぼ同等に評価
            '希望外': 100    # 希望外は非常に高いコスト
        }

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化する
        
        生徒の希望に基づいて、最適なスケジュールを生成します。
        生徒数が多い場合は、複数のユニット（曜日）に分けて割り当てを行います。
        希望外の割り当てを最小化するために、複数回の最適化を行います。
        
        Args:
            preferences_df (DataFrame): 生徒の希望が含まれたDataFrame
            
        Returns:
            dict: 割り当て結果を含む辞書
        """
        # 生徒データを辞書形式に変換
        students = preferences_df.to_dict('records')
        num_students = len(students)
        
        # ステップ1: 必要なユニット数を計算
        slots_per_unit = len(self.TIMES)  # 1ユニットには7スロット
        num_units_needed = (num_students + slots_per_unit - 1) // slots_per_unit  # 切り上げ
        # 講師の数は無限大なので、同じ曜日に複数のユニットを割り当てることが可能
        
        # 各曜日に割り当てるユニット数を計算
        # 同じ曜日に複数のユニットを割り当てる場合も考慮
        
        print(f"\n必要なユニット数: {num_units_needed}")
        
        # ステップ2: 全ての生徒の希望を分析
        student_preferences = self._analyze_student_preferences(students)
        
        # 最適なスケジュールを見つけるために複数の曜日の組み合わせを試す
        best_assignments = None
        best_score = float('-inf')
        
        # 曜日の組み合わせを試す
        if num_units_needed < len(self.DAYS):
            # 全ての曜日の組み合わせを試す
            # 必要なユニット数が曜日数より多い場合は、同じ曜日に複数のユニットを割り当てる
            # この場合は組み合わせではなく、全ての曜日を使用する
            day_combinations = [self.DAYS]
            
            # 最初の組み合わせをデフォルトとして選択
            selected_days = list(day_combinations[0])
            print(f"\n曜日の組み合わせを試しています... (合計{len(day_combinations)}通り)")
            
            # 各組み合わせを試す
            for i, days_combo in enumerate(day_combinations):
                if i % 5 == 0:  # 進捗表示を間引きする
                    print(f"  組み合わせ {i+1}/{len(day_combinations)} を試しています...")
                
                # この組み合わせでスケジュールを作成
                current_days = list(days_combo)
                
                # 生徒を曜日に割り当てる
                student_day_preferences = self._calculate_day_preferences(student_preferences, current_days)
                day_assignments = self._assign_students_to_days(student_day_preferences, current_days, num_students)
                
                # 各曜日ごとに生徒をスロットに割り当てる
                current_assignments = self._assign_students_to_slots(day_assignments, student_preferences)
                
                # この割り当てのスコアを計算
                score = self._evaluate_assignment_score(current_assignments)
                
                # より良い割り当てが見つかった場合は更新
                if score > best_score:
                    best_score = score
                    best_assignments = current_assignments
                    selected_days = current_days
            
            print(f"\n最適な曜日の組み合わせを見つけました: {', '.join(selected_days)}")
        else:
            # 必要なユニット数が曜日数と同じ場合は、全ての曜日を使用
            selected_days = self.DAYS.copy()
            print(f"\n選択された曜日: {', '.join(selected_days)}")
            
            # 生徒を曜日に割り当てる
            student_day_preferences = self._calculate_day_preferences(student_preferences, selected_days)
            day_assignments = self._assign_students_to_days(student_day_preferences, selected_days, num_students)
            
            # 各曜日ごとに生徒をスロットに割り当てる
            best_assignments = self._assign_students_to_slots(day_assignments, student_preferences)
        
        # 全ての生徒が割り当てられたか確認
        if len(best_assignments) < num_students:
            print(f"\n警告: {num_students - len(best_assignments)}名の生徒が割り当てられませんでした。")
        
        # 希望外の割り当て数をカウント
        unwanted_count = sum(1 for _, assignment in best_assignments.items() if assignment['pref_type'] == '希望外')
        if unwanted_count > 0:
            print(f"\n希望外の割り当て: {unwanted_count}名")
            print("希望外の割り当てを最小化するために、生徒の交換最適化を行います...")
        
        # 結果を整形して返す
        return self._format_results(best_assignments, students)
        
    def _evaluate_assignment_score(self, assignments):
        """割り当てのスコアを計算する
        
        Args:
            assignments (dict): 割り当て結果
            
        Returns:
            float: 割り当てのスコア
        """
        score = 0
        pref_weights = {
            '第1希望': 10,
            '第2希望': 5,
            '第3希望': 2,
            '希望外': -20  # 希望外は大きなペナルティ
        }
        
        for student, assignment in assignments.items():
            pref_type = assignment['pref_type']
            score += pref_weights.get(pref_type, 0)
        
        return score
    
    def _analyze_student_preferences(self, students):
        """全ての生徒の希望を分析する
        
        Args:
            students (list): 生徒データのリスト
            
        Returns:
            dict: 生徒名をキー、希望を値とする辞書
        """
        student_preferences = {}
        for student in students:
            student_name = student['生徒名']
            student_preferences[student_name] = {
                '第1希望': student.get('第1希望'),
                '第2希望': student.get('第2希望'),
                '第3希望': student.get('第3希望')
            }
        return student_preferences
        
    def _select_optimal_days(self, students, num_units_needed):
        """最適な曜日を選択する
        
        各曜日の希望数をカウントし、希望数の多い順に曜日を選択します。
        同じ曜日に複数のユニットを割り当てることも可能です。
        
        Args:
            students (list): 生徒データのリスト
            num_units_needed (int): 必要なユニット数
            
        Returns:
            list: 選択された曜日のリスト
        """
        # 各曜日の希望数をカウント
        day_preferences = {day: 0 for day in self.DAYS}
        for student in students:
            for pref_num in [1, 2, 3]:
                pref_key = f'第{pref_num}希望'
                if pref_key in student and student[pref_key]:
                    for day in self.DAYS:
                        if student[pref_key].startswith(day):
                            # 希望順位に応じて重み付け
                            weight = 3 if pref_num == 1 else 2 if pref_num == 2 else 1
                            day_preferences[day] += weight
        
        # 希望数の多い順に曜日をソート
        sorted_days = sorted(day_preferences.items(), key=lambda x: x[1], reverse=True)
        
        # 各曜日の希望割合に基づいてユニット数を割り当て
        total_preferences = sum(count for _, count in sorted_days)
        selected_days = []
        
        # 各曜日に割り当てるユニット数を計算
        day_units = {}
        for day, count in sorted_days:
            # 希望の割合に応じてユニット数を計算（最低1つ）
            ratio = count / total_preferences
            units = max(1, round(ratio * num_units_needed))
            day_units[day] = units
        
        # 合計ユニット数を調整
        total_units = sum(day_units.values())
        
        # 合計が必要数より多い場合、希望の少ない曜日から削減
        if total_units > num_units_needed:
            for day, _ in sorted(sorted_days, key=lambda x: x[1]):
                if total_units <= num_units_needed:
                    break
                if day_units[day] > 0:
                    day_units[day] -= 1
                    total_units -= 1
        
        # 合計が必要数より少ない場合、希望の多い曜日に追加
        while total_units < num_units_needed:
            for day, _ in sorted(sorted_days, key=lambda x: x[1], reverse=True):
                if total_units >= num_units_needed:
                    break
                day_units[day] += 1
                total_units += 1
        
        # 各曜日を必要なユニット数分リストに追加
        for day, units in day_units.items():
            for _ in range(units):
                selected_days.append(day)
        
        # 選択された曜日の表示
        day_counts = {}
        for day in selected_days:
            day_counts[day] = day_counts.get(day, 0) + 1
        
        day_info = [f"{day} (ユニット{count})" for day, count in day_counts.items() if count > 0]
        print(f"\n選択された曜日: {', '.join(day_info)}")
        
        return selected_days
    
    def _calculate_day_preferences(self, student_preferences, selected_days):
        """各生徒の各曜日に対する希望度を計算する
        
        Args:
            student_preferences (dict): 生徒の希望情報
            selected_days (list): 選択された曜日のリスト
            
        Returns:
            dict: 生徒の各曜日に対する希望度
        """
        student_day_preferences = {}
        for student_name, prefs in student_preferences.items():
            student_day_preferences[student_name] = {}
            for day in selected_days:
                # この曜日の希望数をカウント
                day_pref_score = 0
                for pref_key, pref_slot in prefs.items():
                    if pref_slot and pref_slot.startswith(day):
                        # 希望順位に応じたスコアを加算
                        if pref_key == '第1希望':
                            day_pref_score += 3
                        elif pref_key == '第2希望':
                            day_pref_score += 2
                        elif pref_key == '第3希望':
                            day_pref_score += 1
                student_day_preferences[student_name][day] = day_pref_score
        return student_day_preferences
    
    def _assign_students_to_days(self, student_day_preferences, selected_days, num_students):
        """生徒を曜日に割り当てる
        
        生徒の希望度に基づいて、各曜日に生徒を割り当てます。
        同じ曜日に複数のユニットが割り当てられている場合も処理します。
        
        Args:
            student_day_preferences (dict): 生徒の各曜日に対する希望度
            selected_days (list): 選択された曜日のリスト
            num_students (int): 生徒の総数
            
        Returns:
            dict: 各ユニットに割り当てられた生徒のリスト
        """
        # 各ユニットに生徒を振り分ける
        # 同じ曜日が複数回出てくる可能性があるため、ユニット番号を付ける
        unique_units = []
        day_counts = {}
        
        # 選択された曜日をユニークなユニットに変換
        for day in selected_days:
            count = day_counts.get(day, 0) + 1
            day_counts[day] = count
            unit_name = f"{day}_{count}"
            unique_units.append((day, count, unit_name))
        
        # 各ユニットに割り当てる生徒のリストを初期化
        day_assignments = {unit[2]: [] for unit in unique_units}
        unassigned_students = list(student_day_preferences.keys())
        
        # 各ユニットの容量を計算
        slots_per_unit = len(self.TIMES)  # 1ユニットには7スロット
        
        # 各生徒の各曜日に対する希望度をユニットに拡張
        unit_student_preferences = {}
        for student_name, day_prefs in student_day_preferences.items():
            unit_student_preferences[student_name] = {}
            for day, unit_num, unit_name in unique_units:
                unit_student_preferences[student_name][unit_name] = day_prefs[day]
        
        # 各ユニットを順番に処理
        remaining_students = num_students
        
        for i, (day, unit_num, unit_name) in enumerate(unique_units):
            # このユニットに対する各生徒の希望度を取得
            unit_student_prefs = [(student_name, unit_student_preferences[student_name][unit_name]) 
                                 for student_name in unassigned_students]
            
            # 希望度の高い順にソート
            unit_student_prefs.sort(key=lambda x: x[1], reverse=True)
            
            # このユニットの容量を計算
            if i == len(unique_units) - 1:  # 最後のユニット
                capacity = remaining_students
            else:
                capacity = min(slots_per_unit, remaining_students)
                remaining_students -= capacity
            
            # このユニットに生徒を割り当て
            assigned_to_unit = [student[0] for student in unit_student_prefs[:capacity]]
            
            # 割り当てられた生徒を記録
            day_assignments[unit_name] = assigned_to_unit
            
            # 未割り当ての生徒リストを更新
            unassigned_students = [s for s in unassigned_students if s not in assigned_to_unit]
        
        # 各ユニットの割り当て結果を表示し、ユニット情報を保持する辞書に変換
        unit_assignments = {}
        
        # 各ユニットの割り当て結果を表示し、ユニット情報を保持する辞書に変換
        for unit_name, assigned_students in day_assignments.items():
            day, unit_num_str = unit_name.split('_')
            unit_num = int(unit_num_str)
            
            # 表示用のユニット名
            display_name = f"{day} (ユニット{unit_num})"
            
            # 各ユニットの割り当て結果を表示
            print(f"\n{display_name}に割り当てられた生徒: {len(assigned_students)}名")
            for student in assigned_students:
                print(f"  - {student}")
            
            # ユニット情報を保持する辞書に変換
            unit_key = (day, unit_num)  # 曜日とユニット番号のタプルをキーにする
            unit_assignments[unit_key] = assigned_students
        
        return unit_assignments
    
    def _assign_students_to_slots(self, day_assignments, student_preferences):
        """各曜日ごとに生徒をスロットに割り当てる
        
        ハンガリアン法を用いて、生徒の希望に基づいて最適なスロットを割り当てます。
        希望外の割り当てを最小化するために、生徒の交換最適化も行います。
        
        Args:
            day_assignments (dict): 各曜日に割り当てられた生徒のリスト
            student_preferences (dict): 生徒の希望情報
            
        Returns:
            dict: 最終的な割り当て結果
        """
        # 各曜日ごとに生徒をスロットに割り当てる
        initial_assignments = self._initial_slot_assignment(day_assignments, student_preferences)
        
        # 希望外の割り当てを最小化するための最適化
        optimized_assignments = self._optimize_assignments(initial_assignments, student_preferences, day_assignments)
        
        return optimized_assignments
    
    def _initial_slot_assignment(self, unit_assignments, student_preferences):
        """初期のスロット割り当てを行う
        
        Args:
            unit_assignments (dict): 各ユニットに割り当てられた生徒のリスト
            student_preferences (dict): 生徒の希望情報
            
        Returns:
            dict: 初期割り当て結果
        """
        initial_assignments = {}
        
        for unit_key, assigned_students in unit_assignments.items():
            day, unit_num = unit_key  # タプルから曜日とユニット番号を取得
            day_slots = self.day_slots[day]
            num_day_students = len(assigned_students)
            
            if num_day_students == 0:
                continue
            
            # コスト行列を作成（生徒×スロット）
            day_cost_matrix = np.zeros((num_day_students, len(day_slots)))
            
            # 生徒をインデックスと名前のマッピング
            student_idx_to_name = {i: name for i, name in enumerate(assigned_students)}
            
            # 各生徒の各スロットに対するコストを計算
            for i, student_name in enumerate(assigned_students):
                prefs = student_preferences[student_name]
                
                for j, slot in enumerate(day_slots):
                    # デフォルトは希望外のコスト
                    cost = self.PREFERENCE_COSTS['希望外']
                    
                    # 希望に応じてコストを設定
                    for pref_key, pref_slot in prefs.items():
                        if pref_slot == slot:
                            cost = self.PREFERENCE_COSTS[pref_key]
                            break
                    
                    day_cost_matrix[i, j] = cost
            
            # ハンガリアン法で最適な割り当てを計算
            day_row_ind, day_col_ind = linear_sum_assignment(day_cost_matrix)
            
            # 割り当て結果を保存
            for i, student_idx in enumerate(day_row_ind):
                if i < len(day_col_ind):
                    student_name = student_idx_to_name[student_idx]
                    slot_idx = day_col_ind[i]
                    
                    if slot_idx < len(day_slots):
                        assigned_slot = day_slots[slot_idx]
                        prefs = student_preferences[student_name]
                        
                        # 割り当てられたスロットが希望のどれに該当するか確認
                        pref_type = '希望外'
                        for pref_key, pref_slot in prefs.items():
                            if pref_slot == assigned_slot:
                                pref_type = pref_key
                                break
                        
                        initial_assignments[student_name] = {
                            'slot': assigned_slot,
                            'pref_type': pref_type,
                            'day': day,
                            'unit_num': unit_num  # ユニット番号を保存
                        }
        
        return initial_assignments
    
    def _optimize_assignments(self, initial_assignments, student_preferences, unit_assignments):
        """希望外の割り当てを最小化するための最適化
        
        生徒の交換や再割り当てを行い、希望外の割り当てを最小化します。
        
        Args:
            initial_assignments (dict): 初期割り当て結果
            student_preferences (dict): 生徒の希望情報
            unit_assignments (dict): 各ユニットに割り当てられた生徒のリスト
            
        Returns:
            dict: 最適化された割り当て結果
        """
        optimized_assignments = initial_assignments.copy()
        
        # 最適化を複数回試行
        max_iterations = 5
        for iteration in range(max_iterations):
            # 希望外の生徒を特定
            unwanted_assignments = [
                (student_name, assignment['slot'], assignment['day'], assignment['unit_num']) 
                for student_name, assignment in optimized_assignments.items() 
                if assignment['pref_type'] == '希望外'
            ]
            
            if not unwanted_assignments:
                # 希望外の割り当てがない場合は終了
                break
                
            # 最初のイテレーションのみ詳細を表示
            if iteration == 0:
                print(f"  希望外の割り当てが{len(unwanted_assignments)}件あります。最適化を開始します...")
            
            # 交換が行われたか追跡
            exchanges_made = 0
            
            # 希望外の生徒を優先的に処理
            for unwanted_student, unwanted_slot, day, unit_num in unwanted_assignments:
                # この生徒の希望スロットを取得
                student_prefs = student_preferences[unwanted_student]
                preferred_slots = [slot for pref_key, slot in student_prefs.items() if slot.startswith(day)]
                
                if not preferred_slots:
                    # この曜日に希望がない場合はスキップ
                    continue
                
                # 第1希望、第2希望、第3希望の順に試す
                for pref_key in ['第1希望', '第2希望', '第3希望']:
                    if pref_key in student_prefs and student_prefs[pref_key] and student_prefs[pref_key].startswith(day):
                        preferred_slot = student_prefs[pref_key]
                        
                        # この希望スロットに割り当てられている生徒を探す
                        current_occupant = None
                        for student, assignment in optimized_assignments.items():
                            if assignment['slot'] == preferred_slot:
                                current_occupant = student
                                break
                        
                        if current_occupant is None:
                            # 占有者がいない場合はあり得ない
                            continue
                        
                        # 現在の占有者がこのスロットを希望しているか確認
                        occupant_prefs = student_preferences[current_occupant]
                        occupant_pref_type = '希望外'
                        for pref_key_occ, pref_slot in occupant_prefs.items():
                            if pref_slot == preferred_slot:
                                occupant_pref_type = pref_key_occ
                                break
                        
                        # 交換候補の占有者が希望外の場合、または第3希望の場合は交換を試みる
                        if occupant_pref_type == '希望外' or occupant_pref_type == '第3希望':
                            # 占有者が現在のスロットを希望しているか確認
                            occupant_wants_unwanted = False
                            occupant_pref_for_unwanted = '希望外'
                            for pref_key_occ, pref_slot in occupant_prefs.items():
                                if pref_slot == unwanted_slot:
                                    occupant_wants_unwanted = True
                                    occupant_pref_for_unwanted = pref_key_occ
                                    break
                            
                            # 交換が有益か確認
                            # 1. 占有者が希望外で、現在の生徒が第1または第2希望を得る場合
                            # 2. 占有者が第3希望で、現在の生徒が第1希望を得る場合
                            # 3. 占有者が現在のスロットを希望している場合
                            beneficial_exchange = False
                            
                            if occupant_pref_type == '希望外' and pref_key in ['第1希望', '第2希望']:
                                beneficial_exchange = True
                            elif occupant_pref_type == '第3希望' and pref_key == '第1希望':
                                beneficial_exchange = True
                            elif occupant_wants_unwanted:
                                beneficial_exchange = True
                            
                            if beneficial_exchange:
                                # 交換を実行
                                optimized_assignments[unwanted_student]['slot'] = preferred_slot
                                optimized_assignments[unwanted_student]['pref_type'] = pref_key
                                
                                if occupant_wants_unwanted:
                                    # 占有者が希望している場合は、その希望順位を設定
                                    optimized_assignments[current_occupant]['pref_type'] = occupant_pref_for_unwanted
                                else:
                                    # 希望していない場合は希望外
                                    optimized_assignments[current_occupant]['pref_type'] = '希望外'
                                
                                optimized_assignments[current_occupant]['slot'] = unwanted_slot
                                exchanges_made += 1
                                break
                
                # この生徒の交換が成功した場合は次の生徒に移る
                if optimized_assignments[unwanted_student]['pref_type'] != '希望外':
                    continue
                    
                # 他の曜日にも希望がある場合は、曜日間の交換を試みるが、
                # この機能は複雑なため、一旦コメントアウトします
                # 曜日間の交換は別のアプローチで実装する必要があります
                """
                # 他の曜日にも希望がある場合は、曜日の交換を試みる
                other_day_prefs = []
                for pref_key, pref_slot in student_prefs.items():
                    pref_day = None
                    for d in self.DAYS:
                        if pref_slot.startswith(d):
                            pref_day = d
                            break
                    if pref_day and pref_day != day and pref_day in day_assignments:
                        other_day_prefs.append((pref_key, pref_slot, pref_day))
                
                # 他の曜日に希望がない場合はスキップ
                if not other_day_prefs:
                    continue
                
                # 希望順に交換を試みる
                for pref_key, preferred_slot, preferred_day in sorted(other_day_prefs, key=lambda x: x[0]):
                    # 交換候補を探す
                    for other_student in day_assignments[preferred_day]:
                        if other_student == unwanted_student:
                            continue
                            
                        # 交換候補の生徒が現在の曜日に希望を持っているか確認
                        other_student_prefs = student_preferences[other_student]
                        wants_current_day = False
                        for _, pref_slot in other_student_prefs.items():
                            if pref_slot.startswith(day):
                                wants_current_day = True
                                break
                                
                        if wants_current_day:
                            # 交換を実行
                            # 現在の生徒を他の曜日に移動
                            # 他の生徒を現在の曜日に移動
                            
                            # 曼日の割り当てを更新
                            try:
                                day_assignments[day].remove(unwanted_student)
                                day_assignments[day].append(other_student)
                                
                                day_assignments[preferred_day].remove(other_student)
                                day_assignments[preferred_day].append(unwanted_student)
                                
                                # 割り当て情報を更新
                                optimized_assignments[unwanted_student]['day'] = preferred_day
                                optimized_assignments[other_student]['day'] = day
                                
                                exchanges_made += 1
                                break
                            except ValueError:
                                # 生徒がリストに存在しない場合はスキップ
                                continue
                """
                # 曜日間の交換機能は現在無効化されています
            
            # 交換が行われなかった場合は終了
            if exchanges_made == 0:
                break
                
            # 交換後の状況を表示
            unwanted_after = sum(1 for _, assignment in optimized_assignments.items() if assignment['pref_type'] == '希望外')
            print(f"  イテレーション {iteration+1}: {exchanges_made}件の交換を実行しました。希望外の割り当て: {unwanted_after}件")
        
        # 最終的な割り当て結果からdayキーを削除して返す
        return {k: {key: v[key] for key in ['slot', 'pref_type']} for k, v in optimized_assignments.items()}
    
    def _format_results(self, final_assignments, students):
        """結果を整形する
        
        割り当て結果を表示用に整形します。
        同じ曜日に複数のユニットが割り当てられている場合も処理します。
        
        Args:
            final_assignments (dict): 最終的な割り当て結果
            students (list): 生徒データのリスト
            
        Returns:
            dict: 整形された結果
        """
        assigned = []
        unassigned = []
        
        # 曜日ごとのユニット情報を取得するための辞書
        day_unit_info = {day: {} for day in self.DAYS}
        
        for student in students:
            student_name = student['生徒名']
            result = {
                '生徒名': student_name,
                '割当曜日': None,
                '割当時間': None,
                '希望順位': None,
                'ユニット番号': None  # ユニット番号を追加
            }
            
            if student_name in final_assignments:
                assignment = final_assignments[student_name]
                slot_str = assignment['slot']
                # 割り当てられた時間枚から曜日と時間を分離
                for day in self.DAYS:
                    if slot_str.startswith(day):
                        time = slot_str[len(day):]
                        result['割当曜日'] = day
                        result['割当時間'] = time
                        
                        # 元の割り当て情報からユニット番号を取得
                        if 'unit_num' in assignment:
                            result['ユニット番号'] = assignment['unit_num']
                        break
                
                result['希望順位'] = assignment['pref_type']
                assigned.append(result)
            else:
                unassigned.append(result)
        
        # 曜日とユニット番号でソート
        assigned.sort(key=lambda x: (
            self.DAYS.index(x['割当曜日']) if x['割当曜日'] in self.DAYS else float('inf'),
            x['ユニット番号'] or float('inf'),
            self.TIMES.index(x['割当時間']) if x['割当時間'] in self.TIMES else float('inf')
        ))
        
        return {'assigned': assigned, 'unassigned': unassigned}
    
    def display_results(self, results):
        """結果を表示する
        
        同じ曜日に複数のユニットが割り当てられている場合も正しく表示します。
        
        Args:
            results (dict): 整形された結果
        """
        if not results['assigned']:
            print("割り当てられた生徒がいません。")
            return
            
        df = pd.DataFrame(results['assigned'])
        
        # ユニット番号が欠損している場合はデフォルト値を1に設定
        df['ユニット番号'] = df['ユニット番号'].fillna(1)
        
        # 曜日、ユニット番号、時間でソート
        df = df.sort_values(['割当曜日', 'ユニット番号', '割当時間'])
        
        # 結果を表示
        total_students = len(df) + len(results['unassigned'])
        
        # ユニット数を計算
        # 曜日とユニット番号の組み合わせをカウント
        day_unit_combinations = df.groupby(['割当曜日', 'ユニット番号']).size().reset_index().rename(columns={0: 'count'})
        num_units = len(day_unit_combinations)
        total_slots = num_units * len(self.TIMES)
        
        print(f"\n=== スケジュール最適化結果 ===")
        print(f"今回は{total_students}名の生徒を{num_units}ユニット（{total_slots}スロット）に割り振りました。")
        
        # ユニットの説明
        unit_descriptions = []
        for _, row in day_unit_combinations.iterrows():
            day = row['割当曜日']
            unit_num = row['ユニット番号']
            unit_descriptions.append(f"{day}(ユニット{unit_num})")
        
        unit_str = ", ".join(unit_descriptions)
        print(f"割り当てられたユニット: {unit_str}")
        print(f"それぞれのユニットを表示します。")
        
        # 曜日とユニット番号ごとに表示
        for _, row in day_unit_combinations.iterrows():
            day = row['割当曜日']
            unit_num = row['ユニット番号']
            unit_df = df[(df['割当曜日'] == day) & (df['ユニット番号'] == unit_num)]
            
            # 表示用にソートして不要なカラムを削除
            unit_df = unit_df.sort_values('割当時間')
            display_df = unit_df[['生徒名', '割当曜日', '割当時間', '希望順位']]
            
            print(f"\n=== {day} (ユニット{unit_num}) ===")
            print(display_df.to_string(index=False))
        
        # 統計情報を表示
        print(f"\n割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        # 希望順位の集計
        print("\n=== 希望順位の集計 ===")
        preference_counts = df['希望順位'].value_counts()
        assigned_students = len(df)
        for pref, count in preference_counts.items():
            percentage = count / assigned_students * 100
            print(f"{pref}: {count}名 ({percentage:.1f}%)")
            
        # 希望外の割り当てがある場合は件数のみ表示
        unwanted_count = (df['希望順位'] == '希望外').sum()
        if unwanted_count > 0:
            print(f"\n希望外の割り当て: {unwanted_count}件")
            
            # 希望外の生徒を表示
            unwanted_df = df[df['希望順位'] == '希望外']
            print("\n【希望外の割り当てとなった生徒】")
            print(unwanted_df[['生徒名', '割当曜日', '割当時間']].to_string(index=False))


def create_dummy_data(num_students):
    """ダミーデータを生成する関数
    
    生徒の希望をランダムに生成します。
    28スロット（4曜日×7時間）から重複なしで3つの希望を選択します。
    
    Args:
        num_students (int): 生成する生徒数
        
    Returns:
        DataFrame: 生成されたダミーデータ
    """
    optimizer = ScheduleOptimizer()
    data = []
    for i in range(num_students):
        # ランダムに3つの希望を選択
        preferences = random.sample(optimizer.all_slots, 3)
        data.append({
            '生徒名': f'生徒{i+1}',
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })
    return pd.DataFrame(data)

def main():
    """メイン関数
    
    プログラムのメイン処理を行います。
    ダミーデータまたは手動入力によるスケジュール作成を選択できます。
    """
    print("スケジュール最適化プログラム v17\n")
    
    print("選択肢:")
    print("1: ダミーデータでスケジュールを作成")
    print("2: 実データを手動入力してスケジュールを作成")
    
    choice = input("\n選択肢を入力してください (1 or 2): ")
    
    optimizer = ScheduleOptimizer()
    
    if choice == '1':
        while True:
            # ダミーデータを生成
            num_students = int(input("生徒数を入力してください: "))
            preferences_df = create_dummy_data(num_students)
            print(f"\nダミーデータを生成しました（{num_students}名）")
            
            # 生成されたダミーデータを表示
            print("\n=== 生成されたダミーデータ ===")
            print(preferences_df.to_string(index=False))
            
            # 確認ステップ
            confirm = input("\nこのデータでよいですか？ (y/n): ")
            if confirm.lower() == 'y':
                break
            print("\n新しいダミーデータを生成します...")
        
    elif choice == '2':
        # 実データを手動入力
        print("\n生徒の希望を手動で入力します")
        num_students = int(input("生徒数を入力してください: "))
        
        data = []
        
        # 全スロットを表示
        print("\n利用可能なスロット:")
        for i, slot in enumerate(optimizer.all_slots):
            print(f"{i+1}: {slot}")
        
        for i in range(num_students):
            print(f"\n生徒{i+1}の情報を入力:")
            student_name = input("生徒名: ")
            if not student_name:
                student_name = f"生徒{i+1}"
                
            # 希望スロットの入力
            preferences = []
            for j in range(3):
                while True:
                    try:
                        slot_idx = int(input(f"第{j+1}希望のスロット番号: "))
                        if 1 <= slot_idx <= len(optimizer.all_slots):
                            preferences.append(optimizer.all_slots[slot_idx-1])
                            break
                        else:
                            print(f"無効な番号です。1から{len(optimizer.all_slots)}の間で入力してください。")
                    except ValueError:
                        print("数字を入力してください。")
            
            data.append({
                '生徒名': student_name,
                '第1希望': preferences[0],
                '第2希望': preferences[1],
                '第3希望': preferences[2]
            })
        
        preferences_df = pd.DataFrame(data)
        print("\n=== 入力されたデータ ===")
        print(preferences_df.to_string(index=False))
        
    else:
        print("無効な選択肢です。")
        return
    
    # スケジュールを最適化
    results = optimizer.optimize_schedule(preferences_df)
    
    # 結果を表示
    optimizer.display_results(results)

if __name__ == "__main__":
    main()
