#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
タブーサーチ最適化モジュール

一度試した交換パターンを記録し、同じパターンの再試行を避けることで、
局所解から抜け出す最適化手法を提供します。
"""

import pandas as pd
import random
import time
from typing import Dict, List, Tuple, Set


def optimize_tabu_search(
    assignments: pd.DataFrame,
    preferences_df: pd.DataFrame,
    max_iterations: int = 50,
    tabu_tenure: int = 10,
    diversification_threshold: int = 15
) -> pd.DataFrame:
    """
    タブーサーチによる最適化を実行
    
    Args:
        assignments: 現在の割り当て
        preferences_df: 生徒の希望データ
        max_iterations: 最大反復回数
        tabu_tenure: タブーリストの保持期間
        diversification_threshold: 多様化戦略を発動する閾値
        
    Returns:
        最適化後の割り当て
    """
    start_time = time.time()
    
    # 初期解と最良解
    current = assignments.copy()
    best_assignments = current.copy()
    best_stats = calculate_stats(current, preferences_df)
    
    # タブーリスト（交換のペアをキーとして、そのタブー期限をバリューとする辞書）
    tabu_list = {}
    
    # 改善なしの連続回数をカウント
    no_improvement_count = 0
    
    print(f"\n🔍 タブーサーチ最適化を開始（最大{max_iterations}回）")
    print(f"   タブー期間: {tabu_tenure}回, 多様化閾値: {diversification_threshold}回")
    
    for iteration in range(max_iterations):
        # 近傍解の生成（すべての可能な交換ペアを列挙）
        neighbors = []
        
        # 交換候補の生成
        students = current['生徒名'].tolist()
        
        # 多様化戦略：改善がない場合はランダムな交換を試みる
        if no_improvement_count >= diversification_threshold:
            print(f"\n🔄 多様化戦略を発動（{no_improvement_count}回改善なし）")
            # ランダムに生徒を選び、ランダムに交換する
            for _ in range(10):  # 10個のランダムな交換を生成
                student1 = random.choice(students)
                student2 = random.choice([s for s in students if s != student1])
                
                # 現在のスロットを取得
                slot1_col, slot1_val = get_student_slot(current, student1)
                slot2_col, slot2_val = get_student_slot(current, student2)
                
                if slot1_col and slot2_col:
                    # 交換ペアをタプルで表現
                    exchange_pair = ((student1, student2), (slot1_col, slot1_val, slot2_col, slot2_val))
                    
                    # タブーリストにない場合のみ追加
                    if (student1, student2) not in tabu_list or iteration > tabu_list[(student1, student2)]:
                        neighbors.append(exchange_pair)
            
            # 多様化カウンターをリセット
            no_improvement_count = 0
        else:
            # 通常の近傍生成：希望度の低い生徒を優先的に選択
            unmatched_students = find_unmatched_students(current, preferences_df)
            low_preference_students = unmatched_students + find_low_preference_students(current, preferences_df)
            
            # 希望度の低い生徒がいない場合は全生徒から選択
            if not low_preference_students:
                low_preference_students = students
            
            # 各希望度の低い生徒について、交換候補を生成
            for student1 in low_preference_students:
                # 現在のスロットを取得
                slot1_col, slot1_val = get_student_slot(current, student1)
                
                if not slot1_col:
                    continue
                
                # 他の生徒との交換を試みる
                for student2 in students:
                    if student2 == student1:
                        continue
                    
                    # 現在のスロットを取得
                    slot2_col, slot2_val = get_student_slot(current, student2)
                    
                    if not slot2_col:
                        continue
                    
                    # 交換ペアをタプルで表現
                    exchange_pair = ((student1, student2), (slot1_col, slot1_val, slot2_col, slot2_val))
                    
                    # タブーリストにない場合のみ追加
                    if (student1, student2) not in tabu_list or iteration > tabu_list[(student1, student2)]:
                        neighbors.append(exchange_pair)
        
        # 近傍解がない場合は終了
        if not neighbors:
            print(f"\n⚠️ 交換候補がありません。最適化を終了します。")
            break
        
        # 各近傍解を評価し、最良の近傍解を選択
        best_neighbor = None
        best_neighbor_stats = None
        
        for neighbor in neighbors:
            # 交換を適用
            (student1, student2), (slot1_col, slot1_val, slot2_col, slot2_val) = neighbor
            
            temp_result = current.copy()
            idx1 = temp_result[temp_result['生徒名'] == student1].index[0]
            idx2 = temp_result[temp_result['生徒名'] == student2].index[0]
            
            temp_result.at[idx1, slot1_col] = slot2_val
            temp_result.at[idx2, slot2_col] = slot1_val
            
            # 評価
            temp_stats = calculate_stats(temp_result, preferences_df)
            
            # 最良の近傍解を更新
            if not best_neighbor_stats or is_better_assignment(temp_stats, best_neighbor_stats):
                best_neighbor = neighbor
                best_neighbor_stats = temp_stats
        
        # 最良の近傍解を現在の解に適用
        if best_neighbor:
            (student1, student2), (slot1_col, slot1_val, slot2_col, slot2_val) = best_neighbor
            
            # 交換を適用
            idx1 = current[current['生徒名'] == student1].index[0]
            idx2 = current[current['生徒名'] == student2].index[0]
            
            current.at[idx1, slot1_col] = slot2_val
            current.at[idx2, slot2_col] = slot1_val
            
            # タブーリストに追加
            tabu_list[(student1, student2)] = iteration + tabu_tenure
            tabu_list[(student2, student1)] = iteration + tabu_tenure
            
            # 最良解の更新
            if is_better_assignment(best_neighbor_stats, best_stats):
                best_assignments = current.copy()
                best_stats = best_neighbor_stats.copy()
                
                print(f"\n✅ 試行 {iteration+1}/{max_iterations}: 改善されました！")
                print(f"   {student1} と {student2} を交換")
                print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
                print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
                print(f"   加重スコア: {best_stats['加重スコア']}点")
                
                # 改善カウンターをリセット
                no_improvement_count = 0
            else:
                no_improvement_count += 1
                print(f"試行 {iteration+1}/{max_iterations}: 改善なし（{no_improvement_count}回連続）")
        
        # タブーリストの期限切れエントリを削除
        tabu_list = {k: v for k, v in tabu_list.items() if v > iteration}
        
        # 進捗表示
        if (iteration + 1) % 10 == 0:
            elapsed_time = time.time() - start_time
            print(f"\n⏱️ 経過時間: {elapsed_time:.1f}秒, タブーリストサイズ: {len(tabu_list)}")
    
    print(f"\n🏁 タブーサーチ最適化が完了しました（所要時間: {time.time() - start_time:.1f}秒）")
    print(f"   最終結果: 第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
    print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
    print(f"   加重スコア: {best_stats['加重スコア']}点")
    
    return best_assignments


def get_student_slot(assignments: pd.DataFrame, student: str) -> Tuple[str, str]:
    """生徒の現在のスロットを取得"""
    student_row = assignments[assignments['生徒名'] == student]
    if len(student_row) == 0:
        return None, None
    
    for col in assignments.columns:
        if '曜日' in col and pd.notna(student_row[col].values[0]):
            return col, student_row[col].values[0]
    
    return None, None


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


def find_low_preference_students(assignments: pd.DataFrame, preferences_df: pd.DataFrame) -> List[str]:
    """第2希望、第3希望の生徒を特定"""
    low_preference_students = []
    for _, row in assignments.iterrows():
        student = row['生徒名']
        assigned_slot = None
        for col in assignments.columns:
            if '曜日' in col and pd.notna(row[col]):
                assigned_slot = row[col]
                break
        
        if assigned_slot is not None:
            prefs = preferences_df[preferences_df['生徒名'] == student].iloc[0]
            if assigned_slot == prefs['第2希望'] or assigned_slot == prefs['第3希望']:
                low_preference_students.append(student)
    
    return low_preference_students


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
    
    # 希望外が同じ場合は加重スコアで判断
    if new_stats['希望外'] == current_stats['希望外']:
        if new_stats['加重スコア'] > current_stats['加重スコア']:
            return True
    
    return False


if __name__ == "__main__":
    # 単体テスト用コード
    import pandas as pd
    
    # データの読み込み
    assignments = pd.read_csv('results/equal_preference_results.csv')
    preferences = pd.read_csv('data/student_preferences.csv')
    
    # タブーサーチ最適化を実行
    optimized = optimize_tabu_search(
        assignments, 
        preferences, 
        max_iterations=50,
        tabu_tenure=10,
        diversification_threshold=15
    )
    
    # 結果を保存
    optimized.to_csv('results/tabu_search_results.csv', index=False)
    print("\n最適化結果を results/tabu_search_results.csv に保存しました")
