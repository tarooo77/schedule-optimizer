#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ブロックスワップ最適化モジュール

複数の生徒をブロックとして扱い、ブロック間でスロットを交換する最適化手法を提供します。
"""

import pandas as pd
import random
from typing import Dict, List, Tuple, Set


def optimize_block_swap(
    assignments: pd.DataFrame,
    preferences_df: pd.DataFrame,
    block_size: int = 3,
    max_attempts: int = 10
) -> pd.DataFrame:
    """
    ブロック単位でのスワップ最適化を実行
    
    Args:
        assignments: 現在の割り当て
        preferences_df: 生徒の希望データ
        block_size: ブロックサイズ（デフォルト: 3人）
        max_attempts: 最大試行回数
        
    Returns:
        最適化後の割り当て
    """
    current = assignments.copy()
    best_assignments = current.copy()
    best_stats = calculate_stats(best_assignments, preferences_df)
    
    print(f"\n🔄 ブロックスワップ最適化を開始（ブロックサイズ: {block_size}人）")
    
    for attempt in range(max_attempts):
        # 全生徒をリスト化
        all_students = current['生徒名'].tolist()
        
        # 十分な生徒数があるか確認
        if len(all_students) < block_size * 2:
            print(f"⚠️ ブロックスワップに必要な生徒数が足りません（必要: {block_size*2}人, 現在: {len(all_students)}人）")
            return best_assignments
        
        # ブロック1の生徒を選択
        block1_students = random.sample(all_students, block_size)
        
        # ブロック2の生徒を選択 (ブロック1と重複しないように)
        remaining_students = [s for s in all_students if s not in block1_students]
        block2_students = random.sample(remaining_students, block_size)
        
        # ブロック間でスロットを交換
        block1_slots = {}
        block2_slots = {}
        
        # 各ブロックのスロット情報を取得
        for student in block1_students:
            for col in current.columns:
                if '曜日' in col and pd.notna(current.loc[current['生徒名'] == student, col].values[0]):
                    slot_col = col
                    slot_val = current.loc[current['生徒名'] == student, col].values[0]
                    block1_slots[student] = (slot_col, slot_val)
                    break
        
        for student in block2_students:
            for col in current.columns:
                if '曜日' in col and pd.notna(current.loc[current['生徒名'] == student, col].values[0]):
                    slot_col = col
                    slot_val = current.loc[current['生徒名'] == student, col].values[0]
                    block2_slots[student] = (slot_col, slot_val)
                    break
        
        # ブロック間でスロットを交換
        temp_result = current.copy()
        
        # ブロック1の生徒にブロック2のスロットを割り当て
        for i, student1 in enumerate(block1_students):
            student2 = block2_students[i]
            
            # スロット情報を取得
            col1, val1 = block1_slots[student1]
            col2, val2 = block2_slots[student2]
            
            # 交換を適用
            idx1 = temp_result[temp_result['生徒名'] == student1].index[0]
            idx2 = temp_result[temp_result['生徒名'] == student2].index[0]
            
            temp_result.at[idx1, col1] = val2
            temp_result.at[idx2, col2] = val1
        
        # 交換後の評価
        temp_stats = calculate_stats(temp_result, preferences_df)
        
        if is_better_assignment(temp_stats, best_stats):
            best_assignments = temp_result.copy()
            best_stats = temp_stats
            print(f"✅ 試行 {attempt+1}/{max_attempts}: 改善されました！")
            print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
            print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
        else:
            print(f"❌ 試行 {attempt+1}/{max_attempts}: 改善されませんでした")
    
    return best_assignments


def calculate_stats(assignments: pd.DataFrame, preferences_df: pd.DataFrame) -> Dict:
    """割り当ての統計情報を計算"""
    stats = {
        '第1希望': 0,
        '第2希望': 0,
        '第3希望': 0,
        '希望外': 0,
        '加重スコア': 0  # 加重スコアを追加
    }
    
    for _, row in assignments.iterrows():
        student = row['生徒名']
        assigned_slot = None
        for col in assignments.columns:
            if '曜日' in col and pd.notna(row[col]):
                assigned_slot = row[col]
                break
        
        if assigned_slot is None:
            stats['希望外'] += 1
            continue
            
        prefs = preferences_df[preferences_df['生徒名'] == student].iloc[0]
        if assigned_slot == prefs['第1希望']:
            stats['第1希望'] += 1
            stats['加重スコア'] += 3  # 第1希望は3点
        elif assigned_slot == prefs['第2希望']:
            stats['第2希望'] += 1
            stats['加重スコア'] += 2  # 第2希望は2点
        elif assigned_slot == prefs['第3希望']:
            stats['第3希望'] += 1
            stats['加重スコア'] += 1  # 第3希望は1点
        else:
            stats['希望外'] += 1
            stats['加重スコア'] += 0  # 希望外は0点
    
    # 統計情報をコピーして割合を追加
    result_stats = stats.copy()
    total = len(assignments)  # 全生徒数を使用
    
    # 割合を計算して追加
    for key, value in stats.items():
        if key != '加重スコア':
            result_stats[f'{key}率'] = value / total * 100
        
    return result_stats


def is_better_assignment(new_stats: Dict, current_stats: Dict) -> bool:
    """新しい割り当てが現在の割り当てより良いかどうかを判定"""
    # 希望外の数が少ない方が良い
    if new_stats['希望外'] < current_stats['希望外']:
        return True
    
    # 希望外が同じ場合は第1希望の数で判断
    if new_stats['希望外'] == current_stats['希望外']:
        if new_stats['第1希望'] > current_stats['第1希望']:
            return True
        
        # 第1希望も同じ場合は第2希望の数で判断
        if new_stats['第1希望'] == current_stats['第1希望']:
            if new_stats['第2希望'] > current_stats['第2希望']:
                return True
    
    return False


if __name__ == "__main__":
    # 単体テスト用コード
    import pandas as pd
    
    # データの読み込み
    assignments = pd.read_csv('results/equal_preference_results.csv')
    preferences = pd.read_csv('data/student_preferences.csv')
    
    # ブロックスワップ最適化を実行
    optimized = optimize_block_swap(assignments, preferences, block_size=3, max_attempts=10)
    
    # 結果を保存
    optimized.to_csv('results/block_swap_results.csv', index=False)
    print("\n最適化結果を results/block_swap_results.csv に保存しました")
