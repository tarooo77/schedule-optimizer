#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改良版スケジュール最適化プログラム v1.0

このプログラムは、既存の割り当て結果を改善するための高度な最適化アルゴリズムを実装しています。
主な機能：
- 連鎖交換最適化（Chain Exchange）
- グループ交換最適化（Group Exchange）
- シミュレーテッドアニーリング（Simulated Annealing）
- 進捗の可視化と中間結果の保存
"""

import pandas as pd
import numpy as np
import random
import time
import math
import os
from typing import List, Dict, Tuple, Set, Any, Optional

class ImprovedOptimizer:
    def __init__(self):
        self.current_assignments = None
        self.preferences_df = None
        self.all_slots = []
        self.tabu_list = []
        self.tabu_size = 100
        self.max_chain_length = 5
        self.max_group_size = 4
        
    def load_data(self, assignments_file: str, preferences_file: str):
        """割り当て結果と希望データを読み込む"""
        try:
            # ファイルの存在チェック
            if not os.path.exists(assignments_file):
                raise FileNotFoundError(f"割り当てファイルが見つかりません: {assignments_file}")
            if not os.path.exists(preferences_file):
                raise FileNotFoundError(f"希望ファイルが見つかりません: {preferences_file}")
                
            # データ読み込み
            self.current_assignments = pd.read_csv(assignments_file)
            self.preferences_df = pd.read_csv(preferences_file)
            
            # 必須列の確認
            required_cols_assignments = ['生徒名']
            required_cols_preferences = ['生徒名', '第1希望', '第2希望', '第3希望']
            
            for col in required_cols_assignments:
                if col not in self.current_assignments.columns:
                    raise ValueError(f"割り当てファイルに必要な列がありません: {col}")
            
            for col in required_cols_preferences:
                if col not in self.preferences_df.columns:
                    raise ValueError(f"希望ファイルに必要な列がありません: {col}")
            
            # 生徒名の整合性チェック
            assignment_students = set(self.current_assignments['生徒名'])
            preference_students = set(self.preferences_df['生徒名'])
            
            if assignment_students != preference_students:
                missing_in_assignments = preference_students - assignment_students
                missing_in_preferences = assignment_students - preference_students
                
                if missing_in_assignments:
                    print(f"警告: 割り当てファイルに存在しない生徒: {missing_in_assignments}")
                if missing_in_preferences:
                    print(f"警告: 希望ファイルに存在しない生徒: {missing_in_preferences}")
            
            # 利用可能なスロットを抽出
            self.all_slots = []
            for col in self.current_assignments.columns:
                if '曜日' in col:
                    slots = self.current_assignments[col].dropna().unique()
                    self.all_slots.extend(slots)
            
            self.all_slots = list(set(self.all_slots))
            
            print(f"データの読み込みが完了しました:")
            print(f"- 生徒数: {len(self.current_assignments)}名")
            print(f"- 利用可能なスロット数: {len(self.all_slots)}個")
            
        except Exception as e:
            raise ValueError(f"データの読み込み中にエラーが発生しました: {str(e)}")
    
    def calculate_stats(self, assignments: pd.DataFrame) -> Dict:
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
                
            prefs = self.preferences_df[self.preferences_df['生徒名'] == student].iloc[0]
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
    
    def find_chain_exchanges(self, assignments: pd.DataFrame, max_length: int = 5) -> List[List[Tuple]]:
        """連鎖交換の可能性を探索（改良版）"""
        chains = []
        visited = set()
        
        def get_student_slot(student: str) -> str:
            """生徒の現在の割り当てスロットを取得"""
            student_row = assignments[assignments['生徒名'] == student].iloc[0]
            for col in assignments.columns:
                if '曜日' in col and pd.notna(student_row[col]):
                    return student_row[col]
            return None
        
        def get_preferences(student: str) -> List[str]:
            """生徒の希望スロットリストを取得"""
            prefs = self.preferences_df[self.preferences_df['生徒名'] == student].iloc[0]
            return [prefs['第1希望'], prefs['第2希望'], prefs['第3希望']]
        
        def find_chain(start_student: str, current_chain: List[Tuple], length: int = 0):
            """再帰的に交換連鎖を探索"""
            if length >= max_length:
                return
                
            current_slot = get_student_slot(start_student)
            preferences = get_preferences(start_student)
            
            # 現在のスロットの希望度を計算
            current_pref_rank = 3  # デフォルトは希望外
            if current_slot in preferences:
                current_pref_rank = preferences.index(current_slot)
            
            for pref_idx, pref in enumerate(preferences):
                # 現在の希望度より良くなる場合のみ検討
                if pref_idx >= current_pref_rank or pref == current_slot:
                    continue
                    
                # そのスロットに割り当てられている生徒を探す
                for _, row in assignments.iterrows():
                    next_student = row['生徒名']
                    if next_student == start_student:
                        continue
                        
                    next_slot = get_student_slot(next_student)
                    if next_slot == pref:
                        # 連鎖が完成するかチェック（最初の生徒に戻る）
                        if len(current_chain) > 0 and next_student == current_chain[0][0]:
                            if len(current_chain) >= 2:  # 最低2回の交換が必要
                                # 交換後の状態が改善されるか確認
                                improved = False
                                full_chain = current_chain + [(start_student, next_slot)]
                                
                                for student, new_slot in full_chain:
                                    student_prefs = get_preferences(student)
                                    old_slot = get_student_slot(student)
                                    
                                    old_rank = 3 if old_slot not in student_prefs else student_prefs.index(old_slot)
                                    new_rank = 3 if new_slot not in student_prefs else student_prefs.index(new_slot)
                                    
                                    if new_rank < old_rank:
                                        improved = True
                                        break
                                
                                if improved:
                                    chains.append(full_chain)
                            return
                            
                        # 連鎖をまだ続ける
                        if next_student not in visited:
                            visited.add(next_student)
                            find_chain(next_student, 
                                     current_chain + [(start_student, next_slot)],
                                     length + 1)
                            visited.remove(next_student)
        
        # 希望外の生徒から優先的に探索
        for _, row in assignments.iterrows():
            student = row['生徒名']
            current_slot = get_student_slot(student)
            preferences = get_preferences(student)
            
            if current_slot not in preferences:  # 希望外の生徒
                visited.add(student)
                find_chain(student, [], 0)
                visited.remove(student)
        
        # 希望度の低い生徒も探索
        for _, row in assignments.iterrows():
            student = row['生徒名']
            current_slot = get_student_slot(student)
            preferences = get_preferences(student)
            
            if current_slot in preferences and preferences.index(current_slot) > 0:
                # 第2希望、第3希望の生徒
                if student not in visited:
                    visited.add(student)
                    find_chain(student, [], 0)
                    visited.remove(student)
        
        return chains
    
    def find_group_exchanges(self, assignments: pd.DataFrame, group_size: int) -> List[List[Tuple]]:
        """グループ交換（3人以上の循環的な交換）の可能性を探索"""
        groups = []
        visited = set()
        
        def get_student_slot(student: str) -> str:
            student_row = assignments[assignments['生徒名'] == student].iloc[0]
            for col in assignments.columns:
                if '曜日' in col and pd.notna(student_row[col]):
                    return student_row[col]
            return None
        
        def get_preferences(student: str) -> List[str]:
            prefs = self.preferences_df[self.preferences_df['生徒名'] == student].iloc[0]
            return [prefs['第1希望'], prefs['第2希望'], prefs['第3希望']]
        
        def find_group(start_student: str, current_group: List[Tuple], group_size: int):
            if len(current_group) == group_size:
                # グループが完成したら、それが有効な交換かチェック
                improvements = 0
                for student, new_slot in current_group:
                    prefs = get_preferences(student)
                    current_slot = get_student_slot(student)
                    current_rank = 3 if current_slot not in prefs else prefs.index(current_slot)
                    new_rank = 3 if new_slot not in prefs else prefs.index(new_slot)
                    if new_rank < current_rank:
                        improvements += 1
                if improvements > 0:
                    groups.append(current_group)
                return
            
            current_slot = get_student_slot(start_student)
            preferences = get_preferences(start_student)
            
            for pref in preferences:
                if pref == current_slot:
                    continue
                    
                for _, row in assignments.iterrows():
                    next_student = row['生徒名']
                    if next_student in visited:
                        continue
                        
                    next_slot = get_student_slot(next_student)
                    if next_slot == pref:
                        # 最後の生徒の場合、グループが閉じるかチェック
                        if len(current_group) == group_size - 1:
                            first_student = current_group[0][0]
                            first_slot = get_student_slot(first_student)
                            
                            # 最後の生徒の希望に最初の生徒のスロットがあるかチェック
                            next_prefs = get_preferences(next_student)
                            if first_slot in next_prefs:
                                full_group = current_group + [(start_student, next_slot), (next_student, first_slot)]
                                
                                # 改善されるかチェック
                                improvements = 0
                                for student, new_slot in full_group:
                                    prefs = get_preferences(student)
                                    current_slot = get_student_slot(student)
                                    current_rank = 3 if current_slot not in prefs else prefs.index(current_slot)
                                    new_rank = 3 if new_slot not in prefs else prefs.index(new_slot)
                                    if new_rank < current_rank:
                                        improvements += 1
                                
                                if improvements > 0:
                                    groups.append(full_group)
                        else:
                            # グループをまだ続ける
                            visited.add(next_student)
                            find_group(next_student, current_group + [(start_student, next_slot)], group_size)
                            visited.remove(next_student)
        
        # 希望外の生徒から優先的に探索
        for _, row in assignments.iterrows():
            student = row['生徒名']
            current_slot = get_student_slot(student)
            preferences = get_preferences(student)
            
            if current_slot not in preferences:  # 希望外の生徒
                visited.add(student)
                find_group(student, [], group_size)
                visited.remove(student)
        
        return groups
    
    def apply_exchange(self, assignments: pd.DataFrame, exchange: List[Tuple]) -> pd.DataFrame:
        """交換を適用して新しい割り当てを作成"""
        result = assignments.copy()
        
        # 各生徒の現在のスロットを取得
        student_slots = {}
        for _, row in result.iterrows():
            student = row['生徒名']
            for col in result.columns:
                if '曜日' in col and pd.notna(row[col]):
                    student_slots[student] = (col, row[col])
                    break
        
        # 交換を適用
        for student, new_slot in exchange:
            col, _ = student_slots[student]
            idx = result[result['生徒名'] == student].index[0]
            result.at[idx, col] = new_slot
        
        return result
    
    def simulated_annealing(self, 
                          initial_temp: float = 100.0,
                          cooling_rate: float = 0.95,
                          iterations: int = 100,
                          adaptive_temp: bool = True,
                          reheating: bool = False) -> pd.DataFrame:
        """シミュレーテッドアニーリングによる最適化"""
        current = self.current_assignments.copy()
        best = current.copy()
        
        current_stats = self.calculate_stats(current)
        best_stats = current_stats.copy()
        
        temperature = initial_temp
        min_temp = 0.1
        
        # 適応的温度調整のためのパラメータ
        acceptance_rate = 1.0
        target_rate = 0.5
        temp_adjust_factor = 1.1
        
        # 再加熱のためのパラメータ
        reheat_count = 0
        max_reheats = 3
        reheat_temp = initial_temp * 1.1
        
        # アニーリング処理
        for i in range(iterations):
            # 近傍解を生成（ランダムな2人を交換）
            neighbor = current.copy()
            
            # ランダムに2人の生徒を選択
            students = neighbor['生徒名'].tolist()
            if len(students) < 2:
                continue
                
            student1, student2 = random.sample(students, 2)
            
            # 生徒のスロット情報を取得
            slot1_col, slot1_val = None, None
            slot2_col, slot2_val = None, None
            
            for col in neighbor.columns:
                if '曜日' in col:
                    if pd.notna(neighbor.loc[neighbor['生徒名'] == student1, col].values[0]):
                        slot1_col = col
                        slot1_val = neighbor.loc[neighbor['生徒名'] == student1, col].values[0]
                    if pd.notna(neighbor.loc[neighbor['生徒名'] == student2, col].values[0]):
                        slot2_col = col
                        slot2_val = neighbor.loc[neighbor['生徒名'] == student2, col].values[0]
            
            # スロットを交換
            if slot1_col and slot2_col:
                idx1 = neighbor[neighbor['生徒名'] == student1].index[0]
                idx2 = neighbor[neighbor['生徒名'] == student2].index[0]
                
                neighbor.at[idx1, slot1_col] = slot2_val
                neighbor.at[idx2, slot2_col] = slot1_val
                
                # 評価
                neighbor_stats = self.calculate_stats(neighbor)
                
                # 目的関数：希望外の数を最小化
                current_unmatched = current_stats['希望外']
                neighbor_unmatched = neighbor_stats['希望外']
                
                delta = neighbor_unmatched - current_unmatched
                
                # 受理判定
                accepted = False
                if delta <= 0 or random.random() < math.exp(-delta / temperature):
                    current = neighbor.copy()
                    current_stats = neighbor_stats.copy()
                    accepted = True
                
                # 最良解の更新
                if current_stats['希望外'] < best_stats['希望外']:
                    best = current.copy()
                    best_stats = current_stats.copy()
                
                # 適応的温度調整
                if adaptive_temp:
                    acceptance_rate = 0.9 * acceptance_rate + 0.1 * (1 if accepted else 0)
                    if acceptance_rate > target_rate:
                        temperature /= temp_adjust_factor
                    else:
                        temperature *= temp_adjust_factor
                else:
                    # 通常の冷却
                    temperature *= cooling_rate
                
                # 再加熱
                if reheating and temperature < min_temp and reheat_count < max_reheats:
                    print(f"\n再加熱を実行します ({reheat_count + 1}/{max_reheats})")
                    temperature = reheat_temp
                    reheat_count += 1
            
            # 進捗表示
            if i % 10 == 0:
                print(f"イテレーション {i}: 現在の希望外 {current_stats['希望外']}名, 最良 {best_stats['希望外']}名")
                print(f"  温度: {temperature:.2f}, 受理率: {acceptance_rate:.2f}")
        
        return best
    
    def optimize(self, 
                max_iterations: int = 30,   # 反復回数を減らす
                chain_probability: float = 0.5,  # 連鎖交換の確率を上げる
                group_probability: float = 0.3,
                annealing_probability: float = 0.2,
                checkpoint_interval: int = 5,
                save_intermediate: bool = True) -> pd.DataFrame:
        """複数の最適化手法を組み合わせて実行"""
        current = self.current_assignments.copy()
        best_assignments = current.copy()
        best_stats = self.calculate_stats(best_assignments)
        
        # 進捗追跡用の辞書
        progress = {
            '改善回数': 0,
            '連鎖交換回数': 0,
            '連鎖交換成功': 0,
            'グループ交換回数': 0,
            'グループ交換成功': 0,
            'アニーリング回数': 0,
            'アニーリング成功': 0,
            '反復回数': [],
            '希望外': [],
            '第1希望': [],
            '第2希望': [],
            '第3希望': []
        }
        
        print("\n=== 後処理最適化を開始 ===\n")
        print("初期状態:")
        initial_stats = best_stats.copy()
        for key, value in initial_stats.items():
            if '率' not in key:
                print(f"{key}: {value}名 ({initial_stats[f'{key}率']:.1f}%)")
        
        start_time = time.time()
        last_save_time = start_time
        
        for i in range(max_iterations):
            # 最適化手法をランダムに選択
            method = random.random()
            
            if method < chain_probability:
                # 連鎖交換を試行
                chains = self.find_chain_exchanges(current, self.max_chain_length)
                progress['連鎖交換回数'] += 1
                
                if chains:
                    chain = random.choice(chains)
                    current = self.apply_exchange(current, chain)
                    progress['連鎖交換成功'] += 1
                    print(f"✓ 連鎖交換成功（{len(chain)}人）")
            
            elif method < chain_probability + group_probability:
                # グループ交換を試行
                group_size = random.randint(3, self.max_group_size)
                groups = self.find_group_exchanges(current, group_size)
                progress['グループ交換回数'] += 1
                
                if groups:
                    group = random.choice(groups)
                    current = self.apply_exchange(current, group)
                    progress['グループ交換成功'] += 1
                    print(f"✓ グループ交換成功（{len(group)}人）")
            
            else:
                # シミュレーテッドアニーリングを試行
                progress['アニーリング回数'] += 1
                temp_result = self.simulated_annealing(
                    initial_temp=100.0,
                    cooling_rate=0.90,
                    iterations=30,
                    adaptive_temp=True,
                    reheating=False
                )
                
                temp_stats = self.calculate_stats(temp_result)
                if temp_stats['希望外'] < self.calculate_stats(current)['希望外']:
                    current = temp_result.copy()
                    progress['アニーリング成功'] += 1
                    print(f"✓ アニーリング成功")
            
            # 改善されたか確認
            current_stats = self.calculate_stats(current)
            if current_stats['希望外'] < best_stats['希望外']:
                best_assignments = current.copy()
                best_stats = current_stats
                progress['改善回数'] += 1
                
                print(f"\n💫 改善！（試行 {i + 1}）")
                print(f"第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
                print(f"第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
                print(f"加重スコア: {best_stats['加重スコア']}点")
                
                # 改善時は中間結果を保存
                if save_intermediate:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = f"results/intermediate_optimization_{timestamp}.csv"
                    best_assignments.to_csv(filename, index=False)
                    print(f"中間結果を保存しました: {filename}")
            
            # 進捗の記録
            if (i + 1) % checkpoint_interval == 0:
                progress['反復回数'].append(i + 1)
                progress['希望外'].append(best_stats['希望外'])
                progress['第1希望'].append(best_stats['第1希望'])
                progress['第2希望'].append(best_stats['第2希望'])
                progress['第3希望'].append(best_stats['第3希望'])
                
                # 前回からの変更を評価
                prev_unmatched = initial_stats['希望外']
                current_unmatched = best_stats['希望外']
                prev_score = initial_stats['加重スコア']
                current_score = best_stats['加重スコア']
                
                if current_unmatched < prev_unmatched:
                    change_status = "⭐ 希望外減少"
                elif current_unmatched > prev_unmatched:
                    change_status = "📉 希望外増加"
                elif current_score > prev_score:
                    change_status = "👍 希望度改善"
                elif current_score < prev_score:
                    change_status = "👎 希望度悪化"
                else:
                    change_status = "→ 変化なし"
                
                print(f"\n試行 {i + 1}/{max_iterations} {change_status} ({(time.time() - start_time):.1f}秒)")
                print(f"第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
                print(f"第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
                print(f"加重スコア: {best_stats['加重スコア']}点 (初期値: {initial_stats['加重スコア']}点)")
                
                if progress['改善回数'] > 0:
                    print(f"累計: {progress['改善回数']}回改善 (連鎖{progress['連鎖交換成功']}, グループ{progress['グループ交換成功']}, アニリング{progress['アニーリング成功']})")
                
                # 定期的な中間結果の保存
                if save_intermediate and time.time() - last_save_time > 300:  # 5分ごと
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = f"results/intermediate_optimization_{timestamp}.csv"
                    best_assignments.to_csv(filename, index=False)
                    print(f"中間結果を保存しました: {filename}")
                    last_save_time = time.time()
        
        # 最終結果の表示
        print("\n=== 最適化完了 ===")
        print(f"総実行時間: {(time.time() - start_time):.1f}秒")
        print(f"総改善回数: {progress['改善回数']}回")
        print("\n最終結果:")
        for key, value in best_stats.items():
            if '率' not in key:
                print(f"{key}: {value}名 ({best_stats[f'{key}率']:.1f}%)")
        
        # 最終結果を保存
        os.makedirs('results', exist_ok=True)
        best_assignments.to_csv('results/improved_optimization_results.csv', index=False)
        print("\n最適化結果を results/improved_optimization_results.csv に保存しました")
        
        return best_assignments

def main():
    """メイン処理"""
    print("=== 改良版スケジュール最適化 v1.0 ===")
    
    optimizer = ImprovedOptimizer()
    
    try:
        # データの読み込み
        optimizer.load_data(
            assignments_file='results/equal_preference_results.csv',
            preferences_file='data/student_preferences.csv'
        )
        
        # 最適化の実行
        improved_assignments = optimizer.optimize(
            max_iterations=30,
            chain_probability=0.5,
            group_probability=0.3,
            annealing_probability=0.2,
            checkpoint_interval=5,
            save_intermediate=True
        )
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
