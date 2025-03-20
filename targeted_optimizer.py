#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ターゲット最適化モジュール

希望外の生徒に焦点を当てた最適化手法を提供します。
"""

import pandas as pd
import random
from typing import Dict, List, Tuple, Set


def optimize_targeted(
    assignments: pd.DataFrame,
    preferences_df: pd.DataFrame,
    max_attempts: int = 20
) -> pd.DataFrame:
    """
    希望外の生徒に焦点を当てた最適化を実行
    
    Args:
        assignments: 現在の割り当て
        preferences_df: 生徒の希望データ
        max_attempts: 最大試行回数
        
    Returns:
        最適化後の割り当て
    """
    current = assignments.copy()
    best_assignments = current.copy()
    best_stats = calculate_stats(best_assignments, preferences_df)
    
    print(f"\n🎯 ターゲット最適化を開始")
    
    # 希望外の生徒を特定
    unmatched_students = find_unmatched_students(current, preferences_df)
    
    if not unmatched_students:
        print("✅ 希望外の生徒がいません。最適化の必要はありません。")
        return best_assignments
    
    print(f"🔍 希望外の生徒数: {len(unmatched_students)}名")
    
    for attempt in range(max_attempts):
        if not unmatched_students:
            print("✅ すべての希望外の生徒が解消されました！")
            break
            
        # ターゲット生徒を選択
        target_student = random.choice(unmatched_students)
        
        # 希望スロットを取得
        prefs = preferences_df[preferences_df['生徒名'] == target_student].iloc[0]
        preferred_slots = [prefs['第1希望'], prefs['第2希望'], prefs['第3希望']]
        
        # 現在のスロットを取得
        target_row = current[current['生徒名'] == target_student].iloc[0]
        current_slot_col = None
        current_slot = None
        for col in current.columns:
            if '曜日' in col and pd.notna(target_row[col]):
                current_slot_col = col
                current_slot = target_row[col]
                break
        
        print(f"\n🔄 試行 {attempt+1}/{max_attempts}: {target_student} の最適化を試みています")
        print(f"   現在のスロット: {current_slot}, 希望スロット: {preferred_slots}")
        
        # 希望スロットを持つ生徒を探す
        found_exchange = False
        for preferred_slot in preferred_slots:
            for _, row in current.iterrows():
                other_student = row['生徒名']
                if other_student == target_student:
                    continue
                
                for col in current.columns:
                    if '曜日' in col and pd.notna(row[col]) and row[col] == preferred_slot:
                        # 交換候補を見つけた
                        other_slot_col = col
                        
                        # 交換が有効か確認
                        other_prefs = preferences_df[preferences_df['生徒名'] == other_student].iloc[0]
                        other_preferred_slots = [other_prefs['第1希望'], other_prefs['第2希望'], other_prefs['第3希望']]
                        
                        # 交換を適用
                        temp_result = current.copy()
                        idx1 = temp_result[temp_result['生徒名'] == target_student].index[0]
                        idx2 = temp_result[temp_result['生徒名'] == other_student].index[0]
                        
                        temp_result.at[idx1, current_slot_col] = preferred_slot
                        temp_result.at[idx2, other_slot_col] = current_slot
                        
                        # 交換後の評価
                        temp_stats = calculate_stats(temp_result, preferences_df)
                        
                        if is_better_assignment(temp_stats, best_stats):
                            current = temp_result.copy()
                            best_assignments = temp_result.copy()
                            best_stats = temp_stats
                            print(f"✅ 改善されました！ {target_student} と {other_student} を交換")
                            print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
                            print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
                            
                            # 希望外の生徒リストを更新
                            unmatched_students = find_unmatched_students(current, preferences_df)
                            found_exchange = True
                            break
                
                if found_exchange:
                    break
            
            if found_exchange:
                break
        
        if not found_exchange:
            print(f"❌ {target_student} の最適化に失敗しました")
    
    print(f"\n🏁 ターゲット最適化が完了しました")
    print(f"   最終結果: 第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
    print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
    
    return best_assignments


def find_unmatched_students(assignments: pd.DataFrame, preferences_df: pd.DataFrame) -> List[str]:
    """希望外の生徒を特定"""
    unmatched_students = []
    for _, row in assignments.iterrows():
        student = row['生徒名']
        assigned_slot = None
        for col in assignments.columns:
            if '曜日' in col and pd.notna(row[col]):
                assigned_slot = row[col]
                break
        
        if assigned_slot is not None:
            prefs = preferences_df[preferences_df['生徒名'] == student].iloc[0]
            if assigned_slot not in [prefs['第1希望'], prefs['第2希望'], prefs['第3希望']]:
                unmatched_students.append(student)
    
    return unmatched_students


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
    
    # ターゲット最適化を実行
    optimized = optimize_targeted(assignments, preferences, max_attempts=20)
    
    # 結果を保存
    optimized.to_csv('results/targeted_results.csv', index=False)
    print("\n最適化結果を results/targeted_results.csv に保存しました")
