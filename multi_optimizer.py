#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
複合最適化スクリプト

複数の最適化手法を組み合わせて実行するスクリプトです。
"""

import pandas as pd
import random
import time
import os
from typing import Dict, List, Tuple

# 各最適化モジュールをインポート
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from post_assignment_optimizer import PostAssignmentOptimizer
from block_swap_optimizer import optimize_block_swap
from targeted_optimizer import optimize_targeted
from tabu_search_optimizer import optimize_tabu_search
from genetic_optimizer import optimize_genetic


def multi_optimize(
    input_file: str,
    preferences_file: str,
    output_file: str = None,
    iterations: int = 5,
    save_intermediate: bool = True
) -> pd.DataFrame:
    """
    複数の最適化手法を組み合わせて実行
    
    Args:
        input_file: 入力ファイル名
        preferences_file: 希望データファイル名
        output_file: 出力ファイル名
        iterations: 各最適化手法の実行回数
        save_intermediate: 中間結果を保存するかどうか
        
    Returns:
        最適化後の割り当て
    """
    start_time = time.time()
    
    # データの読み込み
    assignments = pd.read_csv(input_file)
    preferences = pd.read_csv(preferences_file)
    
    # 初期状態の統計情報
    initial_stats = calculate_stats(assignments, preferences)
    print("\n📊 初期状態:")
    print(f"   第1希望: {initial_stats['第1希望']}名, 第2希望: {initial_stats['第2希望']}名")
    print(f"   第3希望: {initial_stats['第3希望']}名, 希望外: {initial_stats['希望外']}名")
    print(f"   加重スコア: {initial_stats['加重スコア']}点")
    
    # 最適化の実行
    current = assignments.copy()
    best_assignments = current.copy()
    best_stats = initial_stats.copy()
    
    # 最適化手法のリスト
    optimization_methods = [
        {"name": "連鎖交換最適化", "function": lambda df: PostAssignmentOptimizer().optimize(
            df, 
            preferences, 
            max_iterations=iterations
        )},
        {"name": "ブロックスワップ最適化", "function": lambda df: optimize_block_swap(df, preferences, max_attempts=iterations)},
        {"name": "ターゲット最適化", "function": lambda df: optimize_targeted(df, preferences, max_attempts=iterations*2)},
        {"name": "タブーサーチ最適化", "function": lambda df: optimize_tabu_search(
            df, 
            preferences, 
            max_iterations=iterations*5,
            tabu_tenure=iterations,
            diversification_threshold=iterations*2
        )},
        {"name": "遺伝的アルゴリズム最適化", "function": lambda df: optimize_genetic(
            df, 
            preferences, 
            population_size=max(10, iterations*3),
            generations=iterations*5,
            crossover_rate=0.8,
            mutation_rate=0.2
        )},
    ]
    
    # 各最適化手法を実行
    for i, method in enumerate(optimization_methods):
        print(f"\n\n{'='*50}")
        print(f"🚀 最適化手法 {i+1}/{len(optimization_methods)}: {method['name']}")
        print(f"{'='*50}")
        
        # 最適化を実行
        temp_result = method["function"](current)
        
        # 結果を評価
        temp_stats = calculate_stats(temp_result, preferences)
        
        if is_better_assignment(temp_stats, best_stats):
            best_assignments = temp_result.copy()
            best_stats = temp_stats.copy()
            current = temp_result.copy()
            
            print(f"\n💫 {method['name']}で改善されました！")
            print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
            print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
            print(f"   加重スコア: {best_stats['加重スコア']}点")
            
            # 中間結果を保存
            if save_intermediate:
                intermediate_file = f"results/intermediate_{i+1}_{method['name'].replace(' ', '_')}.csv"
                best_assignments.to_csv(intermediate_file, index=False)
                print(f"   中間結果を {intermediate_file} に保存しました")
        else:
            print(f"\n❌ {method['name']}では改善されませんでした")
    
    # 最終結果の表示
    print(f"\n\n{'='*50}")
    print(f"🏁 最適化完了（所要時間: {time.time() - start_time:.1f}秒）")
    print(f"{'='*50}")
    
    print("\n📊 初期状態:")
    print(f"   第1希望: {initial_stats['第1希望']}名, 第2希望: {initial_stats['第2希望']}名")
    print(f"   第3希望: {initial_stats['第3希望']}名, 希望外: {initial_stats['希望外']}名")
    print(f"   加重スコア: {initial_stats['加重スコア']}点")
    
    print("\n📈 最終結果:")
    print(f"   第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
    print(f"   第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
    print(f"   加重スコア: {best_stats['加重スコア']}点")
    
    # 改善率の計算
    improvement = {
        '第1希望': best_stats['第1希望'] - initial_stats['第1希望'],
        '第2希望': best_stats['第2希望'] - initial_stats['第2希望'],
        '第3希望': best_stats['第3希望'] - initial_stats['第3希望'],
        '希望外': best_stats['希望外'] - initial_stats['希望外'],
        '加重スコア': best_stats['加重スコア'] - initial_stats['加重スコア']
    }
    
    print("\n📊 改善状況:")
    print(f"   第1希望: {improvement['第1希望']:+d}名")
    print(f"   第2希望: {improvement['第2希望']:+d}名")
    print(f"   第3希望: {improvement['第3希望']:+d}名")
    print(f"   希望外: {improvement['希望外']:+d}名")
    print(f"   加重スコア: {improvement['加重スコア']:+d}点")
    
    # 結果を保存
    if output_file:
        best_assignments.to_csv(output_file, index=False)
        print(f"\n💾 最適化結果を {output_file} に保存しました")
    
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
    
    # 希望外が同じ場合は加重スコアで判断
    if new_stats['希望外'] == current_stats['希望外']:
        if new_stats['加重スコア'] > current_stats['加重スコア']:
            return True
    
    return False


if __name__ == "__main__":
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='複数の最適化手法を組み合わせて実行するスクリプト')
    parser.add_argument('--input', '-i', required=True, help='入力ファイル名')
    parser.add_argument('--preferences', '-p', required=True, help='希望データファイル名')
    parser.add_argument('--output', '-o', help='出力ファイル名')
    parser.add_argument('--iterations', '-n', type=int, default=5, help='各最適化手法の実行回数')
    parser.add_argument('--no-save-intermediate', action='store_false', dest='save_intermediate',
                        help='中間結果を保存しない')
    
    args = parser.parse_args()
    
    # 出力ファイル名が指定されていない場合はデフォルト値を設定
    if not args.output:
        args.output = 'results/multi_optimized_results.csv'
    
    # 結果ディレクトリが存在しない場合は作成
    os.makedirs('results', exist_ok=True)
    
    # 最適化を実行
    multi_optimize(
        input_file=args.input,
        preferences_file=args.preferences,
        output_file=args.output,
        iterations=args.iterations,
        save_intermediate=args.save_intermediate
    )
