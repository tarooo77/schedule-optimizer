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
        self.MAX_ATTEMPTS = 100
        self.MAX_RECURSIVE_DEPTH = 5
        self.MAX_CHAIN_LENGTH = 4
        
        # コスト設定（より細かい優先度）
        self.PREFERENCE_COSTS = {
            '第1希望': -1000,
            '第2希望': -500,
            '第3希望': -100,
            '希望外': 1000
        }
        
        self.teacher_schedules = {
            '先生1': ['火曜日', '水曜日', '木曜日'],  # 金曜日休み
            '先生2': ['火曜日', '木曜日', '金曜日'],  # 水曜日休み
            '先生3': ['火曜日', '水曜日', '金曜日'],  # 木曜日休み
            '先生4': ['水曜日', '木曜日', '金曜日'],  # 火曜日休み
            '先生5': ['火曜日', '水曜日', '木曜日']   # 金曜日休み
        }

    def _get_slot_preferences(self, student):
        """生徒の希望時間枠を取得"""
        preferences = []
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key in student and student[pref_key]:
                preferences.append(student[pref_key])
        return preferences

    def _get_students_by_slot(self, students, slot):
        """特定の時間枠を希望している生徒を取得"""
        interested_students = []
        for student in students:
            preferences = self._get_slot_preferences(student)
            if slot in preferences:
                interested_students.append(student)
        return interested_students

    def _find_alternative_assignments(self, current_assignments, unassigned_student, students, depth=0):
        """再帰的に代替の割り当てを探索"""
        if depth >= self.MAX_RECURSIVE_DEPTH:
            return None

        # 現在の割り当てをコピー
        assignments = copy.deepcopy(current_assignments)
        
        # 未割り当ての生徒の希望を取得
        preferences = self._get_slot_preferences(unassigned_student)
        
        for pref in preferences:
            # その時間枠に割り当てられている生徒を探す
            for assigned_student, slot in assignments.items():
                if slot == pref:
                    # 割り当てられている生徒の他の希望を探す
                    other_preferences = self._get_slot_preferences(assigned_student)
                    
                    for other_pref in other_preferences:
                        if other_pref not in assignments.values():
                            # 空いている時間枠を見つけた場合
                            new_assignments = copy.deepcopy(assignments)
                            new_assignments[assigned_student] = other_pref
                            new_assignments[unassigned_student] = pref
                            return new_assignments
                        else:
                            # 再帰的に探索
                            temp_assignments = copy.deepcopy(assignments)
                            temp_assignments.pop(assigned_student)
                            result = self._find_alternative_assignments(
                                temp_assignments,
                                assigned_student,
                                students,
                                depth + 1
                            )
                            if result is not None:
                                result[unassigned_student] = pref
                                return result
        return None

    def _try_swap_chain(self, assignments, unassigned_student, students):
        """スワップチェーンを試行"""
        visited = set()
        queue = deque([(unassigned_student, [], {})])
        
        while queue:
            current_student, chain, current_assignments = queue.popleft()
            
            if len(chain) > self.MAX_CHAIN_LENGTH:
                continue
                
            preferences = self._get_slot_preferences(current_student)
            
            for pref in preferences:
                # 空いている時間枠を見つけた場合
                if pref not in current_assignments.values():
                    new_assignments = copy.deepcopy(assignments)
                    new_assignments.update(current_assignments)
                    new_assignments[current_student] = pref
                    
                    # チェーン内のすべての割り当てを適用
                    for i in range(len(chain)):
                        student = chain[i]
                        if i + 1 < len(chain):
                            next_student = chain[i + 1]
                            new_assignments[student] = new_assignments[next_student]
                    
                    return new_assignments
                
                # その時間枠に割り当てられている生徒を探す
                for assigned_student, slot in assignments.items():
                    if slot == pref and assigned_student not in visited:
                        visited.add(assigned_student)
                        new_chain = chain + [assigned_student]
                        new_assignments = copy.deepcopy(current_assignments)
                        queue.append((assigned_student, new_chain, new_assignments))
        
        return None

    def _optimize_with_hungarian(self, students, time_slots):
        """ハンガリアン法による最適化"""
        num_students = len(students)
        num_slots = len(time_slots)
        cost_matrix = np.full((num_students, num_slots), self.PREFERENCE_COSTS['希望外'])
        
        for student_idx, student in enumerate(students):
            for slot_idx, (day, time, teacher) in enumerate(time_slots):
                slot_str = day + time
                
                # 各希望について確認
                for pref_num in [1, 2, 3]:
                    pref_key = f'第{pref_num}希望'
                    if pref_key in student and student[pref_key] == slot_str:
                        cost_matrix[student_idx, slot_idx] = self.PREFERENCE_COSTS[pref_key]
                        break
                
                # 教師の制約をチェック
                if day not in self.teacher_schedules[teacher]:
                    cost_matrix[student_idx, slot_idx] = float('inf')
        
        # ハンガリアン法で最適化
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        return row_ind, col_ind, cost_matrix

    def _create_initial_assignments(self, students, time_slots):
        """初期割り当ての作成"""
        row_ind, col_ind, cost_matrix = self._optimize_with_hungarian(students, time_slots)
        
        assignments = {}
        unassigned = []
        
        for student_idx, slot_idx in enumerate(col_ind):
            student = students[student_idx]
            day, time, teacher = time_slots[slot_idx]
            slot_str = day + time
            
            if cost_matrix[student_idx, slot_idx] == self.PREFERENCE_COSTS['希望外']:
                unassigned.append(student)
            else:
                assignments[student['生徒名']] = slot_str
        
        return assignments, unassigned

    def _improve_assignments(self, assignments, unassigned, students):
        """割り当ての改善"""
        improved_assignments = copy.deepcopy(assignments)
        remaining_unassigned = []
        
        for student in unassigned:
            # スワップチェーンを試行
            new_assignments = self._try_swap_chain(improved_assignments, student, students)
            
            if new_assignments is None:
                # 代替の割り当てを探索
                new_assignments = self._find_alternative_assignments(improved_assignments, student, students)
            
            if new_assignments is not None:
                improved_assignments = new_assignments
            else:
                remaining_unassigned.append(student)
        
        return improved_assignments, remaining_unassigned

    def optimize_schedule(self, preferences_df):
        """スケジュールの最適化を実行"""
        students = preferences_df.to_dict('records')
        best_assignments = None
        min_unassigned = float('inf')
        
        # 複数回試行して最良の結果を見つける
        for attempt in range(self.MAX_ATTEMPTS):
            time_slots = []
            for day in self.DAYS:
                for time in self.TIMES:
                    for teacher in self.teacher_schedules:
                        if day in self.teacher_schedules[teacher]:
                            time_slots.append((day, time, teacher))
            
            # ランダムに並び替え
            np.random.shuffle(time_slots)
            
            # 初期割り当ての作成
            current_assignments, unassigned = self._create_initial_assignments(students, time_slots)
            
            if len(unassigned) < min_unassigned:
                min_unassigned = len(unassigned)
                best_assignments = current_assignments
                
                if min_unassigned == 0:
                    print(f"希望外ゼロの解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
            
            # 割り当ての改善を試みる
            improved_assignments, remaining_unassigned = self._improve_assignments(current_assignments, unassigned, students)
            
            if len(remaining_unassigned) < min_unassigned:
                min_unassigned = len(remaining_unassigned)
                best_assignments = improved_assignments
                
                if min_unassigned == 0:
                    print(f"改善により希望外ゼロの解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
        
        if min_unassigned > 0:
            print(f"試行回数{self.MAX_ATTEMPTS}回で希望外{min_unassigned}名が最良の結果でした。")
        
        # 結果を整形
        results = []
        for student in students:
            slot_str = best_assignments.get(student['生徒名'])
            if slot_str:
                # 割り当てられた時間枠から曜日と時間を分離
                for day in self.DAYS:
                    if slot_str.startswith(day):
                        time = slot_str[len(day):]
                        break
                
                # 希望順位を特定
                preference = '希望外'
                for pref_num in [1, 2, 3]:
                    pref_key = f'第{pref_num}希望'
                    if pref_key in student and student[pref_key] == slot_str:
                        preference = pref_key
                        break
                
                # 教師を割り当て（この部分は簡略化しています）
                teacher = '先生1'  # 実際には適切な教師を割り当てる必要があります
                
                results.append({
                    'クライアント名': student['クライアント名'],
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher,
                    '希望順位': preference
                })
        
        return {
            'assigned': results,
            'unassigned': [s['生徒名'] for s in students if s['生徒名'] not in best_assignments]
        }

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
