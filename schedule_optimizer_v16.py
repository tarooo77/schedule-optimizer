import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict, deque
import itertools
import copy

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        self.MAX_STUDENTS_PER_TEACHER = 21  # 1講師あたりの最大生徒数
        self.MAX_ATTEMPTS = 50  # 試行回数を削減
        self.MAX_RECURSIVE_DEPTH = 5  # 再帰の深さを削減
        self.MAX_CHAIN_LENGTH = 3  # チェーンの長さを削減
        self.LOCAL_SEARCH_ITERATIONS = 20  # 局所探索の反復回数を削減
        self.MAX_SWAP_ATTEMPTS = 10  # スワップ試行回数を削減
        self.MAX_RELAXATION_ATTEMPTS = 3  # 制約緩和の最大試行回数を削減
        
        # 動的コスト設定（初期値）
        self.PREFERENCE_COSTS = {
            '第1希望': -2000,  # より強い選好
            '第2希望': -1000,
            '第3希望': -500,
            '希望外': 500  # ペナルティを軽減
        }
        
        # 各講師は1ヶ月に3スロットまで担当可能
        self.teacher_schedules = {}
        days_patterns = [
            ['火曜日', '水曜日', '木曜日'],  # 金曜日休み
            ['火曜日', '木曜日', '金曜日'],  # 水曜日休み
            ['火曜日', '水曜日', '金曜日'],  # 木曜日休み
            ['水曜日', '木曜日', '金曜日']   # 火曜日休み
        ]
        
        # 34名の講師を設定
        for i in range(34):
            pattern = days_patterns[i % len(days_patterns)]
            self.teacher_schedules[f'先生{i+1}'] = pattern.copy()

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
        max_iterations = 20  # 最大反復回数を制限
        iteration = 0
        
        for slot in problem_slots:
            if iteration >= max_iterations:
                break
                
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
        min_unassigned = float('inf')
        best_cost = float('inf')
        
        # 全スロットの利用可能教師を事前計算
        slot_teachers = {}
        for day in self.DAYS:
            for time in self.TIMES:
                slot = f'{day}{time}'
                available_teachers = [
                    t for t in self.teacher_schedules
                    if day in self.teacher_schedules[t]
                ]
                if available_teachers:
                    slot_teachers[slot] = available_teachers
        
        # 未割り当て＝0かつ希望外＝0の解が見つかるまで繰り返す
        attempt = 0
        while attempt < self.MAX_ATTEMPTS:
            # 各生徒の希望をスコア化
            student_preferences = defaultdict(list)
            for student in students:
                preferences = self._get_slot_preferences(student)
                for slot, pref_type in preferences:
                    if slot in slot_teachers:
                        score = {
                            '第1希望': 100,
                            '第2希望': 50,
                            '第3希望': 25
                        }[pref_type]
                        student_preferences[student['生徒名']].append({
                            'slot': slot,
                            'score': score,
                            'pref_type': pref_type
                        })
            
            # 初期割り当て
            current_assignments = {}
            slot_assignments = defaultdict(list)  # 各スロットの割り当て状況を追跡
            teacher_assignments = defaultdict(int)  # 各講師の担当生徒数を追跡
            current_cost = 0
            
            # 各生徒について、希望順に割り当てを試行
            for student in students:
                student_name = student['生徒名']
                assigned = False
                
                # 各希望をスコア順にソート
                prefs = sorted(
                    student_preferences[student_name],
                    key=lambda x: x['score'],
                    reverse=True
                )
                
                # 各希望について割り当てを試行
                for pref in prefs:
                    slot = pref['slot']
                    # スロットの制約をチェック
                    if len(slot_assignments[slot]) >= 1:  # 1スロットに1名まで
                        continue
                        
                    # そのスロットの講師を確認
                    available_teacher = None
                    for teacher in slot_teachers[slot]:
                        if teacher_assignments[teacher] < self.MAX_STUDENTS_PER_TEACHER:
                            available_teacher = teacher
                            break
                    
                    if available_teacher is not None:
                        current_assignments[student_name] = {
                            'slot': slot,
                            'teacher': available_teacher
                        }
                        slot_assignments[slot].append(student_name)
                        teacher_assignments[available_teacher] += 1
                        current_cost += self.PREFERENCE_COSTS[pref['pref_type']]
                        assigned = True
                        break
                
                if not assigned:
                    # 未割り当ての場合、空いているスロットを探す
                    for slot, assignments in slot_assignments.items():
                        # スロットの制約をチェック
                        if len(assignments) >= 1:  # 1スロットに1名まで
                            continue
                            
                        # そのスロットの講師を確認
                        available_teacher = None
                        for teacher in slot_teachers[slot]:
                            if teacher_assignments[teacher] < self.MAX_STUDENTS_PER_TEACHER:
                                available_teacher = teacher
                                break
                        
                        if available_teacher is not None:
                            current_assignments[student_name] = {
                                'slot': slot,
                                'teacher': available_teacher
                            }
                            slot_assignments[slot].append(student_name)
                            teacher_assignments[available_teacher] += 1
                            current_cost += self.PREFERENCE_COSTS['希望外']
                            break
            
            # 未割り当ての生徒を特定
            unassigned = [s for s in students if s['生徒名'] not in current_assignments]
            
            # 未割り当てがなく、希望外もない解を探す
            if len(unassigned) == 0:
                # 希望外の割り当てがないか確認
                has_unwanted = False
                for student_name, assignment in current_assignments.items():
                    student = next(s for s in students if s['生徒名'] == student_name)
                    slot = assignment['slot']
                    if not any(slot == p[0] for p in self._get_slot_preferences(student)):
                        has_unwanted = True
                        break
                
                if not has_unwanted:
                    print(f"最適な解が見つかりました！（試行回数: {attempt + 1}回）")
                    best_assignments = current_assignments.copy()
                    break
            
            attempt += 1
            
            # 制約をリセット
            self._reset_constraints()
        
        if attempt >= self.MAX_ATTEMPTS:
            raise Exception(f"試行回数{self.MAX_ATTEMPTS}回で最適な解が見つかりませんでした。")
        
        # 結果を整形
        results = []
        for student in students:
            result = {
                'クライアント名': student['クライアント名'],
                '生徒名': student['生徒名'],
                '割当曜日': None,
                '割当時間': None,
                '担当講師': None,
                '希望順位': None
            }
            
            assignment = best_assignments.get(student['生徒名'])
            if assignment:
                slot_str = assignment['slot']
                assigned_teacher = assignment['teacher']
                # 割り当てられた時間枠から曜日と時間を分離
                for day in self.DAYS:
                    if slot_str.startswith(day):
                        time = slot_str[len(day):]
                        result['割当曜日'] = day
                        result['割当時間'] = time
                        result['担当講師'] = assigned_teacher
                        break
                
                # 希望順位を特定
                preference = '希望外'
                for pref_num in [1, 2, 3]:
                    pref_key = f'第{pref_num}希望'
                    if pref_key in student and student[pref_key] == slot_str:
                        preference = pref_key
                        break
                result['希望順位'] = preference
            
            results.append(result)
        
        return results

    def save_results(self, results, output_file):
        """結果を保存して統計を表示"""
        if not results['assigned']:
            print("割り当てられた生徒がいません。")
            return
            
        df = pd.DataFrame(results['assigned'])
        
        day_order = {day: i for i, day in enumerate(self.DAYS)}
        df['day_order'] = df['割当曜日'].map(day_order)
        df = df.sort_values(['クライアント名', 'day_order', '割当時間'])
        df = df.drop('day_order', axis=1)
        
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print("\n=== スケジュール最適化結果 ===")
        print(f"割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        # 希望順位の集計
        print("\n=== 希望順位の集計 ===")
        preference_counts = df['希望順位'].value_counts()
        total_students = len(df)
        for pref, count in preference_counts.items():
            percentage = (count / total_students) * 100
            print(f"{pref}: {count}名 ({percentage:.1f}%)")
        
        # クライアントごとの希望順位の集計
        print("\n=== クライアントごとの希望順位の集計 ===")
        for client in sorted(df['クライアント名'].unique()):
            client_df = df[df['クライアント名'] == client]
            print(f"\n{client}:")
            client_prefs = client_df['希望順位'].value_counts()
            client_total = len(client_df)
            for pref, count in client_prefs.items():
                percentage = (count / client_total) * 100
                print(f"{pref}: {count}名 ({percentage:.1f}%)")
            
            # クライアントごとの先生と曜日の割り当て状況
            print("\n担当講師の割り当て:")
            teacher_day_counts = client_df.groupby(['担当講師', '割当曜日']).size()
            for (teacher, day), count in teacher_day_counts.items():
                print(f"  {teacher} ({day}): {count}名")

def main():
    optimizer = ScheduleOptimizer()
    preferences = pd.read_csv('student_preferences.csv')
    results = optimizer.optimize_schedule(preferences)
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
