#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
遺伝的アルゴリズム最適化モジュール

複数の解候補を保持し、交叉や突然変異によって新しい解を生成する最適化手法を提供します。
"""

import pandas as pd
import numpy as np
import random
import time
from typing import Dict, List, Tuple, Set


def optimize_genetic(
    assignments: pd.DataFrame,
    preferences_df: pd.DataFrame,
    population_size: int = 20,
    generations: int = 30,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.2
) -> pd.DataFrame:
    """
    遺伝的アルゴリズムによる最適化を実行
    
    Args:
        assignments: 現在の割り当て
        preferences_df: 生徒の希望データ
        population_size: 個体群のサイズ
        generations: 世代数
        crossover_rate: 交叉率
        mutation_rate: 突然変異率
        
    Returns:
        最適化後の割り当て
    """
    start_time = time.time()
    
    print(f"\n🧬 遺伝的アルゴリズム最適化を開始")
    print(f"   個体群サイズ: {population_size}, 世代数: {generations}")
    print(f"   交叉率: {crossover_rate}, 突然変異率: {mutation_rate}")
    
    # 初期個体群の生成
    population = [assignments.copy()]
    
    # 残りの個体をランダムな交換で生成
    for _ in range(population_size - 1):
        new_individual = assignments.copy()
        
        # ランダムな交換を10回適用
        for _ in range(10):
            new_individual = apply_random_swap(new_individual)
        
        population.append(new_individual)
    
    # 最良個体の初期化
    best_individual = assignments.copy()
    best_stats = calculate_stats(best_individual, preferences_df)
    
    # 世代ごとの進化
    for generation in range(generations):
        # 適応度の計算
        fitness_scores = []
        for individual in population:
            stats = calculate_stats(individual, preferences_df)
            # 適応度 = 加重スコア - (希望外 * 10)
            # 希望外の生徒を減らすことを最優先
            fitness = stats['加重スコア'] - (stats['希望外'] * 10)
            fitness_scores.append(fitness)
        
        # 新しい個体群
        new_population = []
        
        # エリート選択（最良個体をそのまま次世代に残す）
        elite_index = fitness_scores.index(max(fitness_scores))
        elite = population[elite_index].copy()
        new_population.append(elite)
        
        # エリート個体の統計情報
        elite_stats = calculate_stats(elite, preferences_df)
        
        # 最良個体の更新
        if is_better_assignment(elite_stats, best_stats):
            best_individual = elite.copy()
            best_stats = elite_stats.copy()
            
            print(f"\n✅ 世代 {generation+1}/{generations}: 改善されました！")
            print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
            print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
            print(f"   加重スコア: {best_stats['加重スコア']}点")
        
        # 残りの個体を生成
        while len(new_population) < population_size:
            # トーナメント選択
            parent1 = tournament_selection(population, fitness_scores, tournament_size=3)
            parent2 = tournament_selection(population, fitness_scores, tournament_size=3)
            
            # 交叉
            if random.random() < crossover_rate:
                child = crossover(parent1, parent2)
            else:
                # 交叉しない場合は親の一方をコピー
                child = parent1.copy() if random.random() < 0.5 else parent2.copy()
            
            # 突然変異
            if random.random() < mutation_rate:
                child = mutate(child)
            
            new_population.append(child)
        
        # 個体群の更新
        population = new_population
        
        # 進捗表示
        if (generation + 1) % 5 == 0:
            elapsed_time = time.time() - start_time
            print(f"\n⏱️ 世代 {generation+1}/{generations}, 経過時間: {elapsed_time:.1f}秒")
            print(f"   最良個体: 第1希望: {best_stats['第1希望']}名, 希望外: {best_stats['希望外']}名")
    
    print(f"\n🏁 遺伝的アルゴリズム最適化が完了しました（所要時間: {time.time() - start_time:.1f}秒）")
    print(f"   最終結果: 第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
    print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
    print(f"   加重スコア: {best_stats['加重スコア']}点")
    
    return best_individual


def apply_random_swap(assignments: pd.DataFrame) -> pd.DataFrame:
    """ランダムな2人の生徒間でスロットを交換"""
    result = assignments.copy()
    students = result['生徒名'].tolist()
    
    if len(students) < 2:
        return result
    
    # ランダムに2人の生徒を選択
    student1, student2 = random.sample(students, 2)
    
    # 現在のスロットを取得
    slot1_col, slot1_val = get_student_slot(result, student1)
    slot2_col, slot2_val = get_student_slot(result, student2)
    
    if slot1_col and slot2_col:
        # 交換を適用
        idx1 = result[result['生徒名'] == student1].index[0]
        idx2 = result[result['生徒名'] == student2].index[0]
        
        result.at[idx1, slot1_col] = slot2_val
        result.at[idx2, slot2_col] = slot1_val
    
    return result


def tournament_selection(population: List[pd.DataFrame], fitness_scores: List[float], tournament_size: int = 3) -> pd.DataFrame:
    """トーナメント選択によって個体を選択"""
    # ランダムにtournament_size個の個体を選択
    tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
    
    # 最も適応度の高い個体を選択
    tournament_fitness = [fitness_scores[i] for i in tournament_indices]
    winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
    
    return population[winner_index].copy()


def crossover(parent1: pd.DataFrame, parent2: pd.DataFrame) -> pd.DataFrame:
    """2つの親から子を生成（一様交叉）"""
    child = parent1.copy()
    students = child['生徒名'].tolist()
    
    # 各生徒について50%の確率で親2のスロットを採用
    for student in students:
        if random.random() < 0.5:
            # 親2のスロットを取得
            slot2_col, slot2_val = get_student_slot(parent2, student)
            
            if slot2_col:
                # 親1のスロットを取得
                slot1_col, _ = get_student_slot(parent1, student)
                
                if slot1_col:
                    # 子に親2のスロットを設定
                    idx = child[child['生徒名'] == student].index[0]
                    child.at[idx, slot1_col] = slot2_val
    
    return child


def mutate(individual: pd.DataFrame) -> pd.DataFrame:
    """突然変異（ランダムな交換）を適用"""
    # ランダムな交換を1〜3回適用
    num_swaps = random.randint(1, 3)
    
    result = individual.copy()
    for _ in range(num_swaps):
        result = apply_random_swap(result)
    
    return result


def get_student_slot(assignments: pd.DataFrame, student: str) -> Tuple[str, str]:
    """生徒の現在のスロットを取得"""
    student_row = assignments[assignments['生徒名'] == student]
    if len(student_row) == 0:
        return None, None
    
    for col in assignments.columns:
        if '曜日' in col and pd.notna(student_row[col].values[0]):
            return col, student_row[col].values[0]
    
    return None, None


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
    
    # 遺伝的アルゴリズム最適化を実行
    optimized = optimize_genetic(
        assignments, 
        preferences, 
        population_size=20,
        generations=30,
        crossover_rate=0.8,
        mutation_rate=0.2
    )
    
    # 結果を保存
    optimized.to_csv('results/genetic_results.csv', index=False)
    print("\n最適化結果を results/genetic_results.csv に保存しました")
