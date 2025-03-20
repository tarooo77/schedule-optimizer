#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
割り当て後の高度な最適化プログラム v1.0

このプログラムは、既存の割り当て結果を読み込み、複数の高度な最適化手法を
組み合わせて更なる改善を試みます。

最適化手法：
1. 拡張連鎖交換（より長い連鎖を探索）
2. グループ交換（3人以上の循環的な交換）
3. シミュレーテッドアニーリング（局所解からの脱出）
4. タブーサーチ（同じ状態への戻りを防止）
"""

import pandas as pd
import numpy as np
import random
import time
import math
from typing import List, Dict, Tuple, Set
import copy

class PostAssignmentOptimizer:
    def __init__(self):
        self.current_assignments = None
        self.preferences_df = None
        self.all_slots = []
        self.tabu_list = []
        self.tabu_size = 1000
        self.max_chain_length = 5
        self.max_group_size = 4
        
    def load_data(self, assignments_file: str, preferences_file: str) -> None:
        """割り当て結果と希望データを読み込む"""
        try:
            # 割り当て結果の読み込みと検証
            self.current_assignments = pd.read_csv(assignments_file)
            required_columns = ['生徒名', '割り当て時間', '希望順位']
            day_columns = ['火曜日', '水曜日', '木曜日', '金曜日']
            
            # 必須列の存在確認
            missing_columns = [col for col in required_columns if col not in self.current_assignments.columns]
            if missing_columns:
                raise ValueError(f"割り当てファイルに必要な列が不足しています: {', '.join(missing_columns)}")
            
            # 曜日列の存在確認
            missing_days = [day for day in day_columns if day not in self.current_assignments.columns]
            if missing_days:
                raise ValueError(f"割り当てファイルに曜日の列が不足しています: {', '.join(missing_days)}")
            
            # 希望データの読み込みと検証
            self.preferences_df = pd.read_csv(preferences_file)
            pref_columns = ['生徒名', '第1希望', '第2希望', '第3希望']
            
            missing_pref_columns = [col for col in pref_columns if col not in self.preferences_df.columns]
            if missing_pref_columns:
                raise ValueError(f"希望ファイルに必要な列が不足しています: {', '.join(missing_pref_columns)}")
            
            # 生徒名の整合性チェック
            assigned_students = set(self.current_assignments['生徒名'])
            preference_students = set(self.preferences_df['生徒名'])
            
            if assigned_students != preference_students:
                missing_in_assignments = preference_students - assigned_students
                missing_in_preferences = assigned_students - preference_students
                error_msg = []
                
                if missing_in_assignments:
                    error_msg.append(f"割り当てファイルに存在しない生徒: {', '.join(missing_in_assignments)}")
                if missing_in_preferences:
                    error_msg.append(f"希望ファイルに存在しない生徒: {', '.join(missing_in_preferences)}")
                
                raise ValueError('\n'.join(error_msg))
            
            # 全スロットの取得と検証
            days = set()
            times = set()
            
            for col in day_columns:
                for slot in self.current_assignments[col].dropna():
                    try:
                        if '時' not in slot:
                            raise ValueError(f"無効な時間形式です: {slot}")
                        day, time = slot.split('時')[0], f"{slot.split('時')[1]}時"
                        days.add(day)
                        times.add(time)
                    except Exception as e:
                        raise ValueError(f"スロット '{slot}' の解析に失敗しました: {str(e)}")
            
            self.all_slots = [f"{day}{time}" for day in sorted(days) for time in sorted(times)]
            
            print("データの読み込みが完了しました:")
            print(f"- 生徒数: {len(assigned_students)}名")
            print(f"- 利用可能なスロット数: {len(self.all_slots)}個")
            
        except pd.errors.EmptyDataError:
            raise ValueError("ファイルが空です")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSVファイルの解析に失敗しました: {str(e)}")
        except Exception as e:
            raise ValueError(f"データの読み込み中にエラーが発生しました: {str(e)}")
    
    def calculate_stats(self, assignments: pd.DataFrame) -> Dict:
        """割り当ての統計情報を計算"""
        stats = {
            '第1希望': 0,
            '第2希望': 0,
            '第3希望': 0,
            '希望外': 0
        }
        
        for _, row in assignments.iterrows():
            student = row['生徒名']
            # 割り当て時間列から直接取得を試みる
            if '割り当て時間' in assignments.columns and pd.notna(row['割り当て時間']):
                assigned_slot = row['割り当て時間']
            else:
                # 従来の方法：曜日の列から取得
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
            elif assigned_slot == prefs['第2希望']:
                stats['第2希望'] += 1
            elif assigned_slot == prefs['第3希望']:
                stats['第3希望'] += 1
            else:
                stats['希望外'] += 1
        
        # 統計情報をコピーして割合を追加
        result_stats = stats.copy()
        total = len(assignments)  # 全生徒数を使用
        
        # 割合を計算して追加
        for key, value in stats.items():
            result_stats[f'{key}率'] = value / total * 100
            
        return result_stats
    
    def find_chain_exchanges(self, assignments: pd.DataFrame, max_length: int = 5) -> List[List[Tuple]]:
        """連鎖交換の可能性を探索"""
        chains = []
        visited = set()
        
        def get_student_slot(student: str) -> str:
            """生徒の現在の割り当てスロットを取得"""
            student_row = assignments[assignments['生徒名'] == student].iloc[0]
            # 割り当て時間列から取得を試みる
            if '割り当て時間' in assignments.columns and pd.notna(student_row['割り当て時間']):
                return student_row['割り当て時間']
            # 従来の方法：曜日の列から取得
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
            
            for pref in preferences:
                if pref == current_slot:
                    continue
                    
                # そのスロットに割り当てられている生徒を探す
                for _, row in assignments.iterrows():
                    next_student = row['生徒名']
                    if next_student == start_student:
                        continue
                        
                    next_slot = get_student_slot(next_student)
                    if next_slot == pref:
                        # 連鎖が完成するかチェック
                        if len(current_chain) > 0 and next_student == current_chain[0][0]:
                            if len(current_chain) >= 2:  # 最低2回の交換が必要
                                chains.append(current_chain + [(start_student, next_slot)])
                            return
                            
                        # 連鎖をまだ続ける
                        if next_student not in visited:
                            visited.add(next_student)
                            find_chain(next_student, 
                                     current_chain + [(start_student, next_slot)],
                                     length + 1)
                            visited.remove(next_student)
        
        # 希望外の生徒から優先的に探索
        stats = self.calculate_stats(assignments)
        for _, row in assignments.iterrows():
            student = row['生徒名']
            current_slot = get_student_slot(student)
            preferences = get_preferences(student)
            
            if current_slot not in preferences:  # 希望外の生徒
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
            # 割り当て時間列から取得を試みる
            if '割り当て時間' in assignments.columns and pd.notna(student_row['割り当て時間']):
                return student_row['割り当て時間']
            # 従来の方法：曜日の列から取得
            for col in assignments.columns:
                if '曜日' in col and pd.notna(student_row[col]):
                    return student_row[col]
            return None
        
        def get_preferences(student: str) -> List[str]:
            prefs = self.preferences_df[self.preferences_df['生徒名'] == student].iloc[0]
            return [prefs['第1希望'], prefs['第2希望'], prefs['第3希望']]
        
        def find_group(start_student: str, current_group: List[Tuple], size: int):
            if len(current_group) == size:
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
                        visited.add(next_student)
                        find_group(next_student, 
                                 current_group + [(start_student, next_slot)],
                                 size)
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
        new_assignments = assignments.copy()
        
        # 交換前の状態をタブーリストに追加
        state_hash = hash(str(assignments.values.tobytes()))
        self.tabu_list.append(state_hash)
        if len(self.tabu_list) > self.tabu_size:
            self.tabu_list.pop(0)
        
        # 交換を実行
        for i, (student, new_slot) in enumerate(exchange):
            # 現在のスロットを見つけて更新
            student_row = new_assignments[new_assignments['生徒名'] == student].index[0]
            for col in new_assignments.columns:
                if '曜日' in col:
                    if pd.notna(new_assignments.at[student_row, col]):
                        new_assignments.at[student_row, col] = pd.NA
                    if new_slot in str(col):
                        new_assignments.at[student_row, col] = new_slot
        
        return new_assignments
    
    def simulated_annealing(self, 
                          initial_temp: float = 100.0,
                          cooling_rate: float = 0.95,
                          iterations: int = 1000,
                          adaptive_temp: bool = True,
                          reheating: bool = True) -> pd.DataFrame:
        """シミュレーテッドアニーリングによる最適化
        
        Args:
            initial_temp: 初期温度
            cooling_rate: 冷却率
            iterations: 反復回数
            adaptive_temp: 適応的な温度調整を行うか
            reheating: 局所解からの脱出のために再加熱を行うか
        """
        current = self.current_assignments.copy()
        best = current.copy()
        current_cost = self.calculate_stats(current)['希望外']
        best_cost = current_cost
        temperature = initial_temp
        no_improvement_count = 0
        reheating_count = 0
        max_reheating = 3
        
        # タブーリストの初期化
        self.tabu_list = []
        
        # 適応的な温度調整のための変数
        acceptance_ratio = 0.0
        target_ratio = 0.3  # 目標受理率
        temp_adjust_factor = 1.1  # 温度調整係数
        
        for i in range(iterations):
            accepted_moves = 0
            total_moves = 0
            
            # 近傍解を生成（ランダムな2名の交換）
            new_solution = current.copy()
            students = new_solution['生徒名'].tolist()
            s1, s2 = random.sample(students, 2)
            
            # 交換を実行
            idx1 = new_solution[new_solution['生徒名'] == s1].index[0]
            idx2 = new_solution[new_solution['生徒名'] == s2].index[0]
            
            for col in new_solution.columns:
                if '曜日' in col:
                    if pd.notna(new_solution.at[idx1, col]) or pd.notna(new_solution.at[idx2, col]):
                        new_solution.at[idx1, col], new_solution.at[idx2, col] = \
                            new_solution.at[idx2, col], new_solution.at[idx1, col]
            
            # タブーリストのチェック
            state_hash = hash(str(new_solution.values.tobytes()))
            if state_hash in self.tabu_list:
                continue
            
            # 新しい解の評価
            new_cost = self.calculate_stats(new_solution)['希望外']
            total_moves += 1
            
            # 受理判定
            delta = new_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temperature):
                current = new_solution
                current_cost = new_cost
                accepted_moves += 1
                
                # タブーリストに追加
                self.tabu_list.append(state_hash)
                if len(self.tabu_list) > self.tabu_size:
                    self.tabu_list.pop(0)
                
                if current_cost < best_cost:
                    best = current.copy()
                    best_cost = current_cost
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
            else:
                no_improvement_count += 1
            
            # 適応的な温度調整
            if adaptive_temp and total_moves > 0:
                acceptance_ratio = accepted_moves / total_moves
                if acceptance_ratio > target_ratio:
                    temperature /= temp_adjust_factor
                elif acceptance_ratio < target_ratio:
                    temperature *= temp_adjust_factor
            else:
                # 通常の冷却
                temperature *= cooling_rate
            
            # 再加熱の判定
            if reheating and no_improvement_count > iterations // 10:
                if reheating_count < max_reheating:
                    print(f"\n再加熱を実行します ({reheating_count + 1}/{max_reheating})")
                    temperature = initial_temp
                    no_improvement_count = 0
                    reheating_count += 1
            
            if i % 100 == 0:
                print(f"イテレーション {i}: 現在の希望外 {current_cost}名, 最良 {best_cost}名")
                if adaptive_temp:
                    print(f"  温度: {temperature:.2f}, 受理率: {acceptance_ratio:.2f}")
        
        return best
    
    def optimize(self, 
                assignments: pd.DataFrame = None,
                preferences_df: pd.DataFrame = None,
                max_iterations: int = 50,   # 反復回数をさらに減らす
                chain_probability: float = 0.4,
                group_probability: float = 0.3,
                annealing_probability: float = 0.3,
                checkpoint_interval: int = 5,   # より頻繁に進捗を表示
                save_intermediate: bool = True) -> pd.DataFrame:
        """複数の最適化手法を組み合わせて実行
        
        Args:
            max_iterations: 最大反復回数
            chain_probability: 連鎖交換を選択する確率
            group_probability: グループ交換を選択する確率
            annealing_probability: シミュレーテッドアニーリングを選択する確率
            checkpoint_interval: 中間結果を保存する間隔
            save_intermediate: 中間結果を保存するかどうか
        """
        # 外部から渡された割り当てと希望データがあれば使用する
        if assignments is not None:
            self.current_assignments = assignments.copy()
        if preferences_df is not None:
            self.preferences_df = preferences_df.copy()
            
        # 必要なデータが設定されているか確認
        if self.current_assignments is None or self.preferences_df is None:
            raise ValueError("assignmentsとpreferences_dfの両方が必要です")
            
        best_assignments = self.current_assignments.copy()
        best_stats = self.calculate_stats(best_assignments)
        
        # 進捗記録用の変数
        progress = {
            '反復回数': [],
            '希望外': [],
            '第1希望': [],
            '第2希望': [],
            '第3希望': [],
            '改善回数': 0,
            '連鎖交換回数': 0,
            'グループ交換回数': 0,
            'アニーリング回数': 0
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
            current = best_assignments.copy()
            method = random.random()
            
            if method < chain_probability:
                # 連鎖交換を試行
                chains = self.find_chain_exchanges(current, self.max_chain_length)
                if chains:
                    chain = random.choice(chains)
                    current = self.apply_exchange(current, chain)
                    progress['連鎖交換回数'] += 1
            
            elif method < chain_probability + group_probability:
                # グループ交換を試行
                size = random.randint(3, self.max_group_size)
                groups = self.find_group_exchanges(current, size)
                if groups:
                    group = random.choice(groups)
                    current = self.apply_exchange(current, group)
                    progress['グループ交換回数'] += 1
            
            else:
                # シミュレーテッドアニーリングを試行
                current = self.simulated_annealing(
                    initial_temp=100.0,  # より高い初期温度
                    cooling_rate=0.90,   # より速い冷却
                    iterations=50,       # より少ない反復回数
                    adaptive_temp=True,
                    reheating=False      # 再加熱を無効化
                )
                progress['アニーリング回数'] += 1
            
            # 改善されたか確認
            current_stats = self.calculate_stats(current)
            if current_stats['希望外'] < best_stats['希望外']:
                best_assignments = current.copy()
                best_stats = current_stats
                progress['改善回数'] += 1
                
                print(f"\n💫 大きな改善！（試行 {i + 1}）")
                print(f"第1希望: {best_stats['第1希望']}名, 第2希望: {best_stats['第2希望']}名")
                print(f"第3希望: {best_stats['第3希望']}名, 希望外: {best_stats['希望外']}名")
                
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
                
                # 前回からの変更を計算
                changes = {}
                for key in ['第1希望', '第2希望', '第3希望', '希望外']:
                    prev_value = progress[key][-1] if progress[key] else initial_stats[key]
                    current_value = best_stats[key]
                    changes[key] = current_value - prev_value
                
                print(f"\n=== イテレーション {i + 1}/{max_iterations} ===")
                print(f"経過時間: {(time.time() - start_time):.1f}秒")
                print(f"最適化手法: 連鎖{progress['連鎖交換回数']}回, グループ{progress['グループ交換回数']}回, アニーリング{progress['アニーリング回数']}回")
                print("\n【現在の割り当て状況】")
                for key, value in best_stats.items():
                    if '率' not in key:
                        change = changes[key]
                        change_str = f"({'↑' if change > 0 else '↓' if change < 0 else '→'}{abs(change)})"
                        print(f"{key}: {value}名 ({best_stats[f'{key}率']:.1f}%) {change_str}")
                
                if progress['改善回数'] > 0:
                    print(f"\n累計改善回数: {progress['改善回数']}回")
                
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
        
        return best_assignments

def main():
    """メイン処理"""
    print("=== 割り当て後の高度な最適化 v1.0 ===\n")
    
    # オプティマイザーの初期化
    optimizer = PostAssignmentOptimizer()
    
    # 最新の割り当て結果を読み込む
    latest_results = "results/equal_preference_results.csv"  # 最新の結果ファイル
    preferences_file = "data/student_preferences.csv"  # 希望データファイル
    
    try:
        optimizer.load_data(latest_results, preferences_file)
    except Exception as e:
        print(f"データの読み込みに失敗しました: {e}")
        return
    
    # 最適化を実行
    improved_assignments = optimizer.optimize(
        max_iterations=1000,
        chain_probability=0.4,
        group_probability=0.3,
        annealing_probability=0.3
    )
    
    # 結果を保存
    output_file = "results/post_optimization_results.csv"
    improved_assignments.to_csv(output_file, index=False)
    print(f"\n最適化結果を {output_file} に保存しました")

if __name__ == "__main__":
    main()
