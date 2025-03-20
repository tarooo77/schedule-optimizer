#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
連鎖交換による希望外最適化モジュール v1.1

このモジュールは、希望外の割り当てがある場合に、連鎖的な交換を試みることで
希望外の割り当てを減らすことを目的としています。

更新履歴：
- v1.1 (2025-03-18): リアルタイム進捗表示機能を実装し、連鎖交換の探索状況を詳細に表示するように改善。
- v1.0 (2025-03-18): 初期バージョン。連鎖交換による希望外最適化アルゴリズムを実装。
"""

import pandas as pd
import numpy as np
import time
import random
from collections import defaultdict, deque

class ChainSwapOptimizer:
    """
    連鎖交換による希望外最適化クラス
    """
    
    def __init__(self):
        """初期化"""
        self.MAX_CHAIN_LENGTH = 5  # 最大連鎖長
        self.MAX_ATTEMPTS = 1000   # 最大試行回数
        
    def optimize_by_chain_swapping(self, assignments, students_df):
        """
        連鎖交換による最適化を実行する
        
        Args:
            assignments: 割り当て結果のリスト
            students_df: 生徒の希望データを含むDataFrame
            
        Returns:
            improved_assignments: 改善された割り当て結果のリスト
            swap_count: 実行された交換の回数
        """
        print("\n=== 連鎖交換による希望外最適化 ===")
        print(f"希望外の割り当てを減らすために連鎖交換を試みます...")
        
        start_time = time.time()
        
        # 割り当て結果をコピー
        improved_assignments = assignments.copy()
        
        # 希望外の割り当てを持つ生徒を特定
        unwanted_assignments = [a for a in improved_assignments if a['希望順位'] == '希望外']
        print(f"希望外の割り当てがある生徒数: {len(unwanted_assignments)}名")
        
        if not unwanted_assignments:
            print("希望外の割り当てはありません。連鎖交換最適化は不要です。")
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
                'pref': a['希望順位'],
                'assignment': a
            }
        
        # スロットに割り当てられている生徒を追跡
        slot_to_student = {}
        for a in improved_assignments:
            slot = f"{a['割当曜日']}{a['割当時間']}"
            slot_to_student[slot] = a['生徒名']
        
        # 交換回数をカウント
        swap_count = 0
        
        # 各希望外の割り当てに対して連鎖交換を試みる
        for unwanted_assignment in unwanted_assignments:
            unwanted_student = unwanted_assignment['生徒名']
            unwanted_slot = f"{unwanted_assignment['割当曜日']}{unwanted_assignment['割当時間']}"
            
            print(f"生徒 {unwanted_student} の希望外割り当てを改善するために連鎖交換を試みます...")
            
            # 連鎖交換を試みる
            success, chain = self._find_swap_chain(
                unwanted_student, 
                unwanted_slot, 
                student_preferences, 
                current_assignments_dict,
                slot_to_student
            )
            
            if success:
                # 連鎖交換を実行
                self._perform_chain_swap(chain, improved_assignments, current_assignments_dict, slot_to_student)
                swap_count += 1
                print(f"連鎖交換成功: {len(chain)}人の連鎖で {unwanted_student} の希望外割り当てを改善しました")
                print(f"交換チェーン: {' -> '.join([s for s, _ in chain])}")
            else:
                print(f"連鎖交換失敗: {unwanted_student} の希望外割り当てを改善できませんでした")
        
        # 交換後の希望外の割り当て数を確認
        post_unwanted = len([a for a in improved_assignments if a['希望順位'] == '希望外'])
        
        elapsed_time = time.time() - start_time
        print(f"連鎖交換最適化が完了しました。処理時間: {elapsed_time:.2f}秒")
        print(f"交換回数: {swap_count}回")
        print(f"希望外の割り当て: {len(unwanted_assignments)}名 → {post_unwanted}名")
        
        return improved_assignments, swap_count
    
    def _find_swap_chain(self, start_student, start_slot, student_preferences, current_assignments, slot_to_student):
        """
        連鎖交換のパスを見つける
        
        Args:
            start_student: 開始生徒（希望外の割り当てがある生徒）
            start_slot: 開始生徒の現在のスロット
            student_preferences: 生徒の希望辞書
            current_assignments: 現在の割り当て辞書
            slot_to_student: スロットから生徒へのマッピング
            
        Returns:
            (success, chain): 成功したかどうかと、見つかった交換チェーン
        """
        print(f"連鎖交換を探索中: 生徒 {start_student} の希望外割り当てを改善するための連鎖を探します...")
        
        # 開始生徒の希望スロット
        start_prefs = [pref[0] for pref in student_preferences.get(start_student, [])]
        
        if not start_prefs:
            return False, []
        
        # 各試行で異なる順序で試す
        random.shuffle(start_prefs)
        print(f"  探索開始: {len(start_prefs)}個の希望スロットから連鎖を探索します")
        
        # 各希望スロットから連鎖を探索
        for i, target_slot in enumerate(start_prefs):
            print(f"  希望スロット {i+1}/{len(start_prefs)}: {target_slot} を探索中...")
            # そのスロットに割り当てられている生徒
            if target_slot not in slot_to_student:
                print(f"    スキップ: {target_slot} に割り当てられている生徒がいません")
                continue
                
            next_student = slot_to_student[target_slot]
            print(f"    {target_slot} には生徒 {next_student} が割り当てられています")
            
            # BFSで連鎖を探索
            visited = {start_student}
            queue = deque([(next_student, [(start_student, start_slot), (next_student, target_slot)])])
            
            attempts = 0
            progress_interval = max(1, self.MAX_ATTEMPTS // 10)  # 10%ごとに進捗を表示
            print(f"    BFS探索開始: 最大{self.MAX_ATTEMPTS}回の試行、最大連鎖長{self.MAX_CHAIN_LENGTH}")
            
            while queue and attempts < self.MAX_ATTEMPTS:
                attempts += 1
                
                # 進捗表示（10%ごと）
                if attempts % progress_interval == 0 or attempts == 1:
                    progress = (attempts / self.MAX_ATTEMPTS) * 100
                    print(f"    探索進捗: {progress:.1f}% ({attempts}/{self.MAX_ATTEMPTS}回) - キュー内{len(queue)}件")
                
                current_student, chain = queue.popleft()
                
                # 連鎖が長すぎる場合はスキップ
                if len(chain) > self.MAX_CHAIN_LENGTH:
                    continue
                
                # 現在の生徒の希望を取得
                current_prefs = [pref[0] for pref in student_preferences.get(current_student, [])]
                
                # 連鎖の最初の生徒のスロットが現在の生徒の希望に含まれているか
                if start_slot in current_prefs:
                    # 連鎖が完成
                    print(f"    連鎖発見! {len(chain)}人の連鎖で希望外を解消できます")
                    return True, chain
                
                # 連鎖を続ける
                for next_pref in current_prefs:
                    if next_pref not in slot_to_student:
                        continue
                        
                    next_student = slot_to_student[next_pref]
                    
                    # 既に訪問済みならスキップ
                    if next_student in visited:
                        continue
                    
                    # 訪問済みに追加
                    visited.add(next_student)
                    
                    # 連鎖に追加
                    new_chain = chain + [(next_student, next_pref)]
                    queue.append((next_student, new_chain))
            
            # この希望スロットからは連鎖が見つからなかった
            print(f"    この希望スロットからは連鎖が見つかりませんでした ({attempts}回試行)")
        
        # 全ての希望スロットを探索したが連鎖が見つからなかった
        print(f"  全ての希望スロットを探索しましたが、連鎖が見つかりませんでした")
        return False, []
    
    def _perform_chain_swap(self, chain, assignments, assignments_dict, slot_to_student):
        """
        連鎖交換を実行する
        
        Args:
            chain: 交換チェーン [(生徒名, スロット), ...]
            assignments: 割り当て結果のリスト
            assignments_dict: 割り当て辞書
            slot_to_student: スロットから生徒へのマッピング
        """
        # 連鎖の最後から2番目の生徒が最初の生徒のスロットを取得
        n = len(chain)
        
        # 各生徒の新しいスロットを計算（循環的に交換）
        new_slots = {}
        for i in range(n):
            student, _ = chain[i]
            _, next_slot = chain[(i + 1) % n]
            new_slots[student] = next_slot
        
        # 割り当てを更新
        for student, new_slot in new_slots.items():
            # スロットを分解
            day = new_slot[:3]
            time = new_slot[3:]
            
            # 希望順位を特定
            pref_rank = '希望外'
            for a in assignments:
                if a['生徒名'] == student:
                    # 希望順位を更新
                    for i in range(1, 4):
                        pref_key = f'第{i}希望'
                        if pref_key in a and a[pref_key] == new_slot:
                            pref_rank = pref_key
                            break
                    
                    # 割当情報を更新
                    a['割当曜日'] = day
                    a['割当時間'] = time
                    a['希望順位'] = pref_rank
                    
                    # 辞書も更新
                    assignments_dict[student]['slot'] = new_slot
                    assignments_dict[student]['pref'] = pref_rank
                    break
        
        # スロットと生徒のマッピングを更新
        for student, new_slot in new_slots.items():
            slot_to_student[new_slot] = student


def apply_chain_swap_optimization(assignments, students_df):
    """
    連鎖交換最適化を適用する関数
    
    Args:
        assignments: 割り当て結果のリスト
        students_df: 生徒の希望データを含むDataFrame
        
    Returns:
        improved_assignments: 改善された割り当て結果のリスト
        swap_count: 実行された交換の回数
    """
    optimizer = ChainSwapOptimizer()
    return optimizer.optimize_by_chain_swapping(assignments, students_df)


if __name__ == "__main__":
    print("このモジュールは直接実行せず、必要に応じて他のプログラムから呼び出してください。")
