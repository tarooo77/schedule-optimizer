#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
すべての最適化手法を順番に実行するスクリプト

各最適化手法を順番に実行し、最も良い結果を選択します。
"""

import os
import time
import pandas as pd
import argparse
from typing import Dict, List, Tuple

# 各最適化モジュールをインポート
from post_assignment_optimizer import PostAssignmentOptimizer
from block_swap_optimizer import optimize_block_swap
from targeted_optimizer import optimize_targeted
from tabu_search_optimizer import optimize_tabu_search
from genetic_optimizer import optimize_genetic
from multi_optimizer import multi_optimize, calculate_stats, is_better_assignment


def run_all_optimizers(
    input_file: str,
    preferences_file: str,
    output_dir: str = 'results',
    iterations: int = 3
):
    """
    すべての最適化手法を順番に実行
    
    Args:
        input_file: 入力ファイル名
        preferences_file: 希望データファイル名
        output_dir: 出力ディレクトリ
        iterations: 各最適化手法の実行回数
    """
    start_time = time.time()
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 現在の日時を取得してタイムスタンプを作成
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    # 結果保存用のディレクトリを作成
    result_dir = os.path.join(output_dir, f'optimization_run_{timestamp}')
    os.makedirs(result_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"🚀 すべての最適化手法を実行します")
    print(f"   入力ファイル: {input_file}")
    print(f"   希望データ: {preferences_file}")
    print(f"   結果ディレクトリ: {result_dir}")
    print(f"{'='*60}")
    
    # データの読み込み
    assignments = pd.read_csv(input_file)
    preferences = pd.read_csv(preferences_file)
    
    # 初期状態の統計情報
    initial_stats = calculate_stats(assignments, preferences)
    print("\n📊 初期状態:")
    print(f"   第1希望: {initial_stats['第1希望']}名, 第2希望: {initial_stats['第2希望']}名")
    print(f"   第3希望: {initial_stats['第3希望']}名, 希望外: {initial_stats['希望外']}名")
    print(f"   加重スコア: {initial_stats['加重スコア']}点")
    
    # 初期状態を保存
    initial_file = os.path.join(result_dir, '00_initial.csv')
    assignments.to_csv(initial_file, index=False)
    
    # 最適化手法のリスト
    optimization_methods = [
        {
            "name": "連鎖交換最適化",
            "function": lambda df: PostAssignmentOptimizer().optimize(
                df, 
                preferences, 
                max_iterations=iterations*5
            ),
            "output_file": os.path.join(result_dir, '01_chain_exchange.csv')
        },
        {
            "name": "ブロックスワップ最適化(2人)",
            "function": lambda df: optimize_block_swap(df, preferences, block_size=2, max_attempts=iterations*3),
            "output_file": os.path.join(result_dir, '02_block_swap_2.csv')
        },
        {
            "name": "ブロックスワップ最適化(3人)",
            "function": lambda df: optimize_block_swap(df, preferences, block_size=3, max_attempts=iterations*3),
            "output_file": os.path.join(result_dir, '03_block_swap_3.csv')
        },
        {
            "name": "ブロックスワップ最適化(4人)",
            "function": lambda df: optimize_block_swap(df, preferences, block_size=4, max_attempts=iterations*3),
            "output_file": os.path.join(result_dir, '04_block_swap_4.csv')
        },
        {
            "name": "ターゲット最適化",
            "function": lambda df: optimize_targeted(df, preferences, max_attempts=iterations*5),
            "output_file": os.path.join(result_dir, '05_targeted.csv')
        },
        {
            "name": "タブーサーチ最適化",
            "function": lambda df: optimize_tabu_search(
                df, 
                preferences, 
                max_iterations=iterations*10,
                tabu_tenure=iterations*2,
                diversification_threshold=iterations*3
            ),
            "output_file": os.path.join(result_dir, '06_tabu_search.csv')
        },
        {
            "name": "遺伝的アルゴリズム最適化",
            "function": lambda df: optimize_genetic(
                df, 
                preferences, 
                population_size=max(10, iterations*5),
                generations=iterations*10,
                crossover_rate=0.8,
                mutation_rate=0.2
            ),
            "output_file": os.path.join(result_dir, '07_genetic.csv')
        },
        {
            "name": "複合最適化",
            "function": lambda df: multi_optimize(
                input_file=initial_file,
                preferences_file=preferences_file,
                output_file=os.path.join(result_dir, '08_multi.csv'),
                iterations=iterations,
                save_intermediate=True
            ),
            "output_file": os.path.join(result_dir, '08_multi.csv')
        }
    ]
    
    # 各最適化手法を実行
    best_assignments = assignments.copy()
    best_stats = initial_stats.copy()
    best_method = "初期状態"
    
    for i, method in enumerate(optimization_methods):
        print(f"\n\n{'='*60}")
        print(f"🔄 最適化手法 {i+1}/{len(optimization_methods)}: {method['name']}")
        print(f"{'='*60}")
        
        # 最適化を実行
        method_start_time = time.time()
        
        try:
            if method["name"] == "複合最適化":
                # 複合最適化は特別な処理が必要
                temp_result = method["function"](best_assignments)
            else:
                temp_result = method["function"](best_assignments)
            
            # 結果を保存
            temp_result.to_csv(method["output_file"], index=False)
            
            # 結果を評価
            temp_stats = calculate_stats(temp_result, preferences)
            
            print(f"\n⏱️ {method['name']}の実行時間: {time.time() - method_start_time:.1f}秒")
            print(f"   第1希望: {temp_stats['第1希望']}名, 第2希望: {temp_stats['第2希望']}名")
            print(f"   第3希望: {temp_stats['第3希望']}名, 希望外: {temp_stats['希望外']}名")
            print(f"   加重スコア: {temp_stats['加重スコア']}点")
            
            if is_better_assignment(temp_stats, best_stats):
                best_assignments = temp_result.copy()
                best_stats = temp_stats.copy()
                best_method = method["name"]
                
                print(f"\n💫 新たな最良解が見つかりました！（{method['name']}）")
        except Exception as e:
            print(f"\n❌ {method['name']}の実行中にエラーが発生しました: {str(e)}")
    
    # 最終結果の保存
    final_file = os.path.join(result_dir, 'final_best_result.csv')
    best_assignments.to_csv(final_file, index=False)
    
    # 最終結果の表示
    print(f"\n\n{'='*60}")
    print(f"🏁 すべての最適化が完了しました（所要時間: {time.time() - start_time:.1f}秒）")
    print(f"{'='*60}")
    
    print("\n📊 初期状態:")
    print(f"   第1希望: {initial_stats['第1希望']}名, 第2希望: {initial_stats['第2希望']}名")
    print(f"   第3希望: {initial_stats['第3希望']}名, 希望外: {initial_stats['希望外']}名")
    print(f"   加重スコア: {initial_stats['加重スコア']}点")
    
    print(f"\n📈 最終結果 (最良手法: {best_method}):")
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
    
    print(f"\n💾 最終結果を {final_file} に保存しました")
    print(f"   すべての中間結果は {result_dir} ディレクトリに保存されています")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='すべての最適化手法を順番に実行するスクリプト')
    parser.add_argument('--input', '-i', required=True, help='入力ファイル名')
    parser.add_argument('--preferences', '-p', required=True, help='希望データファイル名')
    parser.add_argument('--output-dir', '-o', default='results', help='出力ディレクトリ')
    parser.add_argument('--iterations', '-n', type=int, default=3, help='各最適化手法の実行回数の基準値')
    
    args = parser.parse_args()
    
    run_all_optimizers(
        input_file=args.input,
        preferences_file=args.preferences,
        output_dir=args.output_dir,
        iterations=args.iterations
    )
