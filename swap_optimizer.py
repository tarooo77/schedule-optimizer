#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
希望外の割り当てを減らすための交換最適化モジュール v1.0

このモジュールは、希望外の割り当てがある場合に、他の生徒との交換を試みることで
希望外の割り当てを減らすことを目的としています。
"""

import pandas as pd
import numpy as np
import time
import random
from collections import defaultdict

class SwapOptimizer:
    """
    希望外の割り当てを減らすための交換最適化クラス
    """
    
    def __init__(self):
        """初期化"""
        self.MAX_SWAP_ATTEMPTS = 1000
        
    def optimize_by_swapping(self, assignments, students_df):
        """
        割り当て結果を交換によって最適化する
        
        Args:
            assignments: 割り当て結果のリスト
            students_df: 生徒の希望データを含むDataFrame
            
        Returns:
            improved_assignments: 改善された割り当て結果のリスト
            swap_count: 実行された交換の回数
        """
        print("\n=== 交換による希望外最適化 ===")
        print(f"希望外の割り当てを減らすために交換を試みます...")
        
        start_time = time.time()
        
        # 割り当て結果をコピー
        improved_assignments = assignments.copy()
        
        # 希望外の割り当てを持つ生徒を特定
        unwanted_assignments = [a for a in improved_assignments if a['希望順位'] == '希望外']
        print(f"希望外の割り当てがある生徒数: {len(unwanted_assignments)}名")
        
        if not unwanted_assignments:
            print("希望外の割り当てはありません。交換最適化は不要です。")
            return improved_assignments, 0
        
        # 生徒の希望をディクショナリに変換
        student_preferences = {}
        for _, student in students_df.iterrows():
            student_name = student['生徒名']
            prefs = []
            for i in range(1, 4):
                pref_key = f'第{i}希望'
                if pref_key in student and student[pref_key]:
                    prefs.append((student[pref_key], f'第{i}希望'))
            student_preferences[student_name] = prefs
        
        # 現在の割り当てをディクショナリに変換
        current_assignments_dict = {}
        for a in improved_assignments:
            student_name = a['生徒名']
            slot = f"{a['割当曜日']}{a['割当時間']}"
            current_assignments_dict[student_name] = {
                'slot': slot,
                'pref': a['希望順位']
            }
        
        # スロットに割り当てられている生徒を追跡
        slot_to_student = {}
        for a in improved_assignments:
            slot = f"{a['割当曜日']}{a['割当時間']}"
            slot_to_student[slot] = a['生徒名']
        
        # 交換回数をカウント
        swap_count = 0
        
        # 各希望外の割り当てに対して交換を試みる
        for unwanted_assignment in unwanted_assignments:
            unwanted_student = unwanted_assignment['生徒名']
            unwanted_slot = f"{unwanted_assignment['割当曜日']}{unwanted_assignment['割当時間']}"
            
            # この生徒の希望スロット
            preferred_slots = [pref[0] for pref in student_preferences.get(unwanted_student, [])]
            
            # 交換候補を見つける
            found_swap = False
            
            # ランダムな順序で試行
            attempts = 0
            while not found_swap and attempts < self.MAX_SWAP_ATTEMPTS:
                attempts += 1
                
                # ランダムに他の生徒を選択
                other_student = random.choice([s for s in current_assignments_dict.keys() if s != unwanted_student])
                other_slot = current_assignments_dict[other_student]['slot']
                
                # 交換が有効かチェック
                if self._is_valid_swap(unwanted_student, other_student, unwanted_slot, other_slot, 
                                     student_preferences, current_assignments_dict):
                    # 交換を実行
                    self._perform_swap(unwanted_student, other_student, unwanted_slot, other_slot, 
                                     improved_assignments, current_assignments_dict, slot_to_student)
                    swap_count += 1
                    found_swap = True
                    print(f"交換成功: {unwanted_student} と {other_student} のスロットを交換しました")
            
            if not found_swap:
                print(f"交換失敗: {unwanted_student} の希望外割り当てを改善できませんでした")
        
        # 交換後の希望外の割り当て数を確認
        post_unwanted = len([a for a in improved_assignments if a['希望順位'] == '希望外'])
        
        elapsed_time = time.time() - start_time
        print(f"交換最適化が完了しました。処理時間: {elapsed_time:.2f}秒")
        print(f"交換回数: {swap_count}回")
        print(f"希望外の割り当て: {len(unwanted_assignments)}名 → {post_unwanted}名")
        
        return improved_assignments, swap_count
    
    def _is_valid_swap(self, student1, student2, slot1, slot2, student_preferences, current_assignments):
        """
        交換が有効かどうかをチェック
        
        交換が有効な条件:
        1. student1がslot2を希望している
        2. student2がslot1を希望していないか、現在の希望よりも低い希望である
        """
        # student1の希望をチェック
        student1_prefs = student_preferences.get(student1, [])
        student1_wants_slot2 = any(pref[0] == slot2 for pref in student1_prefs)
        
        if not student1_wants_slot2:
            return False
        
        # student2の現在の希望レベル
        student2_current_pref = current_assignments[student2]['pref']
        
        # student2の希望をチェック
        student2_prefs = student_preferences.get(student2, [])
        student2_slot1_pref = None
        for pref in student2_prefs:
            if pref[0] == slot1:
                student2_slot1_pref = pref[1]
                break
        
        # student2がslot1を希望していない場合、交換は無効
        if student2_slot1_pref is None:
            return False
        
        # 希望の優先度を数値に変換
        pref_rank = {
            '第1希望': 1,
            '第2希望': 2,
            '第3希望': 3,
            '希望外': 4
        }
        
        # student2の現在の希望と交換後の希望を比較
        if pref_rank.get(student2_slot1_pref, 4) <= pref_rank.get(student2_current_pref, 4):
            # 交換後の希望が現在の希望と同等以上なら交換可能
            return True
        
        return False
    
    def _perform_swap(self, student1, student2, slot1, slot2, assignments, assignments_dict, slot_to_student):
        """
        二人の生徒間でスロットを交換する
        """
        # 割り当て辞書を更新
        assignments_dict[student1]['slot'] = slot2
        assignments_dict[student2]['slot'] = slot1
        
        # student1の希望順位を更新
        student1_prefs = []
        for a in assignments:
            if a['生徒名'] == student1:
                # スロットを分解
                day2 = slot2[:3]
                time2 = slot2[3:]
                
                # 希望順位を特定
                for i in range(1, 4):
                    pref_key = f'第{i}希望'
                    if a.get(pref_key) == slot2:
                        a['希望順位'] = pref_key
                        break
                else:
                    a['希望順位'] = '希望外'
                
                # 割当情報を更新
                a['割当曜日'] = day2
                a['割当時間'] = time2
        
        # student2の希望順位を更新
        for a in assignments:
            if a['生徒名'] == student2:
                # スロットを分解
                day1 = slot1[:3]
                time1 = slot1[3:]
                
                # 希望順位を特定
                for i in range(1, 4):
                    pref_key = f'第{i}希望'
                    if a.get(pref_key) == slot1:
                        a['希望順位'] = pref_key
                        break
                else:
                    a['希望順位'] = '希望外'
                
                # 割当情報を更新
                a['割当曜日'] = day1
                a['割当時間'] = time1
        
        # スロットと生徒のマッピングを更新
        slot_to_student[slot1] = student2
        slot_to_student[slot2] = student1


def apply_swap_optimization(assignments, students_df):
    """
    交換最適化を適用する関数
    
    Args:
        assignments: 割り当て結果のリスト
        students_df: 生徒の希望データを含むDataFrame
        
    Returns:
        improved_assignments: 改善された割り当て結果のリスト
        swap_count: 実行された交換の回数
    """
    optimizer = SwapOptimizer()
    return optimizer.optimize_by_swapping(assignments, students_df)


if __name__ == "__main__":
    print("このモジュールは直接実行せず、equal_preference_optimizer.pyから呼び出してください。")
