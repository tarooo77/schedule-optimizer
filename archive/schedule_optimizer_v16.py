import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
import random

class ScheduleOptimizer:
    def __init__(self):
        # 基本設定
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        
        # 全スロットを生成（28スロット）
        self.all_slots = []
        for day in self.DAYS:
            for time in self.TIMES:
                self.all_slots.append(f'{day}{time}')
        
        # 希望の重み付け（より強いペナルティを設定）
        self.PREFERENCE_COSTS = {
            '第1希望': -1000,
            '第2希望': -500,
            '第3希望': -100,
            '希望外': 5000
        }
        
        # 最大試行回数を増やす
        self.MAX_ATTEMPTS = 1000
        self.MAX_LOCAL_ATTEMPTS = 50

    def _adjust_preference_costs(self, unassigned_count):
        """未割り当て数に応じてコストを動的に調整"""
        if unassigned_count > 0:
            # より積極的な調整
            self.PREFERENCE_COSTS['第3希望'] = -500 - (unassigned_count * 100)
            self.PREFERENCE_COSTS['第2希望'] = -1000 - (unassigned_count * 50)
            self.PREFERENCE_COSTS['第1希望'] = -2000 - (unassigned_count * 25)
            # 希望外のペナルティを調整
            self.PREFERENCE_COSTS['希望外'] = max(500 - (unassigned_count * 10), 100)
    
    def _relax_constraints(self):
        """制約を段階的に緩和"""
        # 希望外のコストを軽減
        self.PREFERENCE_COSTS['希望外'] = max(
            self.PREFERENCE_COSTS['希望外'] * 0.9,
            100
        )
        
    def _reset_constraints(self):
        """制約を初期状態にリセット"""
        self.PREFERENCE_COSTS = {
            '第1希望': -2000,
            '第2希望': -1000,
            '第3希望': -500,
            '希望外': 500
        }

    def _get_slot_preferences(self, student):
        """生徒の希望時間枠を取得"""
        preferences = []
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key in student and student[pref_key]:
                preferences.append((student[pref_key], pref_key))
        return preferences

    def _get_students_by_slot(self, students, slot):
        """特定の時間枠を希望している生徒を取得"""
        interested_students = []
        for student in students:
            for pref, pref_type in self._get_slot_preferences(student):
                if pref == slot:
                    interested_students.append((student, pref_type))
                    break
        return interested_students

    def _try_local_reassignment(self, assignments, students, problem_slots):
        """局所的な再割り当てを試行"""
        improved = False
        iteration = 0
        
        # 各問題スロットに対して再割り当てを試みる
        while iteration < self.MAX_LOCAL_ATTEMPTS and not improved:
            for slot in problem_slots:
                interested_students = self._get_students_by_slot(students, slot)
                if not interested_students:
                    continue
            
            # 現在の割り当てを持つ生徒を優先度順にソート
            interested_students.sort(key=lambda x: {
                '第1希望': 3,
                '第2希望': 2,
                '第3希望': 1,
                '希望外': 0
            }[x[1]])
            
            # 上位5件のみを処理
            for student, pref_type in interested_students[:5]:
                if student['生徒名'] not in assignments:
                    # 他の生徒との交換を試みる
                    for assigned_student, assignment in assignments.items():
                        if assignment['slot'] == slot:
                            assigned_student_obj = next(
                                s for s in students if s['生徒名'] == assigned_student
                            )
                            
                            # 他の希望を確認（上位3つのみ）
                            other_preferences = self._get_slot_preferences(assigned_student_obj)[:3]
                            
                            for other_slot, _ in other_preferences:
                                # そのスロットが空いているか確認
                                if not any(a['slot'] == other_slot for a in assignments.values()):
                                    # 教師を適切に選択
                                    for day in self.DAYS:
                                        if other_slot.startswith(day):
                                            available_teachers = [
                                                t for t in self.teacher_schedules
                                                if day in self.teacher_schedules[t]
                                            ]
                                            if available_teachers:
                                                # 交換を実行
                                                assignments[assigned_student] = {
                                                    'slot': other_slot,
                                                    'teacher': available_teachers[0]
                                                }
                                                assignments[student['生徒名']] = {
                                                    'slot': slot,
                                                    'teacher': assignment['teacher']
                                                }
                                                improved = True
                                                break
                                    
                                    if improved:
                                        break
                            
                            if improved:
                                break
                    
                    if improved:
                        break
                        
                iteration += 1
                if iteration >= max_iterations:
                    break
        
        return improved

    def _optimize_with_hungarian(self, students, time_slots):
        """ハンガリアン法による最適化"""
        num_students = len(students)
        num_slots = len(time_slots)
        
        # 大きな有限値を使用（np.inf は使用しない）
        LARGE_COST = 1e6
        
        # コスト行列を初期化（デフォルトは希望外のコスト）
        cost_matrix = np.full((num_students, num_slots), LARGE_COST, dtype=np.float64)
        
        for student_idx, student in enumerate(students):
            for slot_idx, (day, time, teacher) in enumerate(time_slots):
                # 教師の制約をチェック
                if day not in self.teacher_schedules[teacher]:
                    continue
                
                slot_str = day + time
                cost = self.PREFERENCE_COSTS['希望外']
                
                # 各希望について確認
                for pref_num in [1, 2, 3]:
                    pref_key = f'第{pref_num}希望'
                    if pref_key in student and student[pref_key] == slot_str:
                        cost = self.PREFERENCE_COSTS[pref_key]
                        break
                
                cost_matrix[student_idx, slot_idx] = cost
        
        # コスト行列の値を確認
        if not np.isfinite(cost_matrix).all():
            # 無限大の値があれば大きな有限値に置き換え
            cost_matrix[~np.isfinite(cost_matrix)] = LARGE_COST
        
        # 数値の範囲を確認
        if np.any(cost_matrix > LARGE_COST) or np.any(cost_matrix < -LARGE_COST):
            # 範囲外の値を制限
            cost_matrix = np.clip(cost_matrix, -LARGE_COST, LARGE_COST)
        
        try:
            # ハンガリアン法で最適化
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        except ValueError as e:
            print(f"Warning: 最適化中にエラーが発生しました: {e}")
            print("コスト行列を調整して再試行します...")
            
            # コスト行列を正規化して再試行
            cost_matrix = (cost_matrix - cost_matrix.min()) / (cost_matrix.max() - cost_matrix.min()) * 2000 - 1000
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        return row_ind, col_ind, cost_matrix

    def _find_chain_reassignment(self, assignments, unassigned_student, students, visited=None, chain=None, current_depth=0):
        """再帰的なチェーン再割り当てを探索"""
        if visited is None:
            visited = set()
        if chain is None:
            chain = []
        
        if len(chain) > self.MAX_CHAIN_LENGTH or current_depth > self.MAX_RECURSIVE_DEPTH:
            return None
        
        preferences = [p[0] for p in self._get_slot_preferences(unassigned_student)]
        
        for pref in preferences:
            # 割り当てられたスロットを取得
            assigned_slots = {v['slot'] for v in assignments.values()}
            
            # 空いている時間枠を見つけた場合
            if pref not in assigned_slots:
                new_assignments = copy.deepcopy(assignments)
                
                # チェーン内のすべての割り当てを適用
                current_slot = pref
                for student in reversed(chain):
                    prev_assignment = assignments[student['生徒名']]
                    new_assignments[student['生徒名']] = {
                        'slot': current_slot,
                        'teacher': prev_assignment['teacher']
                    }
                    current_slot = prev_assignment['slot']
                
                # 末尾の生徒に割り当て
                # 教師を適切に選択
                for day in self.DAYS:
                    if pref.startswith(day):
                        available_teachers = [
                            t for t in self.teacher_schedules
                            if day in self.teacher_schedules[t]
                        ]
                        if available_teachers:
                            new_assignments[unassigned_student['生徒名']] = {
                                'slot': pref,
                                'teacher': available_teachers[0]
                            }
                            return new_assignments
                        break
            
            # その時間枠に割り当てられている生徒を探す
            for assigned_student_name, assignment in assignments.items():
                if assignment['slot'] == pref:
                    assigned_student = next(s for s in students if s['生徒名'] == assigned_student_name)
                    
                    if assigned_student['生徒名'] not in visited:
                        visited.add(assigned_student['生徒名'])
                        new_chain = chain + [assigned_student]
                        
                        result = self._find_chain_reassignment(
                            assignments,
                            assigned_student,
                            students,
                            visited,
                            new_chain,
                            current_depth + 1
                        )
                        
                        if result is not None:
                            return result
        
        return None

    def optimize_schedule(self, preferences_df):
        """スケジュールの最適化を実行"""
        students = preferences_df.to_dict('records')
        best_assignments = None
        min_unwanted = float('inf')
        num_students = len(students)
        num_slots = len(self.all_slots)
        
        # 最適化の試行回数をカウント
        attempt = 0
        
        while attempt < self.MAX_ATTEMPTS:
            # コスト行列を作成（生徒×スロット）
            cost_matrix = np.zeros((num_students, num_slots))
            
            # 各生徒の各スロットに対するコストを計算
            for i, student in enumerate(students):
                for j, slot in enumerate(self.all_slots):
                    # デフォルトは希望外のコスト
                    cost = self.PREFERENCE_COSTS['希望外']
                    
                    # 希望に応じてコストを設定
                    for pref_num in [1, 2, 3]:
                        pref_key = f'第{pref_num}希望'
                        if pref_key in student and student[pref_key] == slot:
                            cost = self.PREFERENCE_COSTS[pref_key]
                            break
                    
                    cost_matrix[i, j] = cost
            
            # ハンガリアン法で最適な割り当てを計算
            row_ind, col_ind = linear_sum_assignment(cost_matrix)
            
            # 割り当て結果を保存
            assignments = {}
            unwanted_count = 0
            
            for i, student in enumerate(students):
                student_name = student['生徒名']
                assigned_slot = self.all_slots[col_ind[i]]
                
                # 割り当てられたスロットが希望のどれに該当するか確認
                pref_type = '希望外'
                for pref_num in [1, 2, 3]:
                    pref_key = f'第{pref_num}希望'
                    if pref_key in student and student[pref_key] == assigned_slot:
                        pref_type = pref_key
                        break
                
                if pref_type == '希望外':
                    unwanted_count += 1
                
                assignments[student_name] = {
                    'slot': assigned_slot,
                    'pref_type': pref_type
                }
            
            # より良い解が見つかった場合は更新
            if unwanted_count < min_unwanted:
                min_unwanted = unwanted_count
                best_assignments = assignments.copy()
                
                if unwanted_count == 0:
                    print(f"最適な解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
                else:
                    print(f"改善された解が見つかりました（希望外: {unwanted_count}名）")
            
            # コストを動的に調整
            if unwanted_count > 0:
                self.PREFERENCE_COSTS['希望外'] *= 1.1
            
            attempt += 1
        
        if attempt >= self.MAX_ATTEMPTS:
            if best_assignments is None:
                raise Exception(f"試行回数{self.MAX_ATTEMPTS}回で有効な解が見つかりませんでした。")
            else:
                print(f"試行回数{self.MAX_ATTEMPTS}回で希望外{min_unwanted}名の解が最良でした。")
                
        # 結果を整形
        assigned = []
        unassigned = []
        
        for student in students:
            result = {
                '生徒名': student['生徒名'],
                '割当曜日': None,
                '割当時間': None,
                '希望順位': None
            }
            
            assignment = best_assignments.get(student['生徒名'])
            if assignment:
                slot_str = assignment['slot']
                # 割り当てられた時間枠から曜日と時間を分離
                for day in self.DAYS:
                    if slot_str.startswith(day):
                        time = slot_str[len(day):]
                        result['割当曜日'] = day
                        result['割当時間'] = time
                        break
                
                result['希望順位'] = assignment['pref_type']
                assigned.append(result)
            else:
                unassigned.append(result)
        
        return {'assigned': assigned, 'unassigned': unassigned}

    def display_results(self, results):
        """結果を表示する"""
        if not results['assigned']:
            print("割り当てられた生徒がいません。")
            return
            
        df = pd.DataFrame(results['assigned'])
        
        # 曜日順にソート
        day_order = {day: i for i, day in enumerate(self.DAYS)}
        df['day_order'] = df['割当曜日'].map(day_order)
        df = df.sort_values(['day_order', '割当時間'])
        df = df.drop('day_order', axis=1)
        
        # 結果を表示
        print("\n=== 最適化されたスケジュール ===")
        print(df.to_string(index=False))
        
        # 統計情報を表示
        print("\n=== スケジュール最適化結果 ===")
        print(f"割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        # 希望順位の集計
        print("\n=== 希望順位の集計 ===")
        preference_counts = df['希望順位'].value_counts()
        total_students = len(df)
        for pref, count in preference_counts.items():
            percentage = count / total_students * 100
            print(f"{pref}: {count}名 ({percentage:.1f}%)")
        


def create_dummy_data(num_students):
    """ダミーデータを生成する関数"""
    optimizer = ScheduleOptimizer()
    data = []
    for i in range(num_students):
        # ランダムに3つの希望を選択
        preferences = random.sample(optimizer.all_slots, 3)
        data.append({
            '生徒名': f'生徒{i+1}',
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })
    return pd.DataFrame(data)

def main():
    print("スケジュール最適化プログラム\n")
    
    print("選択肢:")
    print("1: ダミーデータでスケジュールを作成")
    print("2: 実データを手動入力してスケジュールを作成")
    
    choice = input("\n選択肢を入力してください (1 or 2): ")
    
    optimizer = ScheduleOptimizer()
    
    if choice == '1':
        # ダミーデータを生成
        num_students = int(input("生徒数を入力してください: "))
        preferences_df = create_dummy_data(num_students)
        print(f"\nダミーデータを生成しました（{num_students}名）")
        
        # 生成されたダミーデータを表示
        print("\n=== 生成されたダミーデータ ===")
        print(preferences_df.to_string(index=False))
        
    elif choice == '2':
        # 実データを手動入力
        print("\n生徒の希望を手動で入力します")
        num_students = int(input("生徒数を入力してください: "))
        
        data = []
        
        # 全スロットを表示
        print("\n利用可能なスロット:")
        for i, slot in enumerate(optimizer.all_slots):
            print(f"{i+1}: {slot}")
        
        for i in range(num_students):
            print(f"\n生徒{i+1}の情報を入力:")
            student_name = input("生徒名: ")
            if not student_name:
                student_name = f"生徒{i+1}"
                
            # 希望スロットの入力
            preferences = []
            for j in range(3):
                while True:
                    try:
                        slot_idx = int(input(f"第{j+1}希望のスロット番号: "))
                        if 1 <= slot_idx <= len(optimizer.all_slots):
                            preferences.append(optimizer.all_slots[slot_idx-1])
                            break
                        else:
                            print(f"無効な番号です。1から{len(optimizer.all_slots)}の間で入力してください。")
                    except ValueError:
                        print("数字を入力してください。")
            
            data.append({
                '生徒名': student_name,
                '第1希望': preferences[0],
                '第2希望': preferences[1],
                '第3希望': preferences[2]
            })
        
        preferences_df = pd.DataFrame(data)
        print("\n=== 入力されたデータ ===")
        print(preferences_df.to_string(index=False))
        
    else:
        print("無効な選択肢です。")
        return
    
    # スケジュールを最適化
    results = optimizer.optimize_schedule(preferences_df)
    
    # 結果を表示
    optimizer.display_results(results)

if __name__ == "__main__":
    main()
