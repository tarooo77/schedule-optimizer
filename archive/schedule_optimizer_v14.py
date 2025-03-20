import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict
import itertools

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        self.MAX_ATTEMPTS = 100
        
        # 各希望のコスト（負の値が大きいほど優先度が高い）
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

    def _initialize_state(self):
        """状態を初期化"""
        self.assignments = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        self.teacher_day_counts = defaultdict(lambda: defaultdict(int))
        self.client_teacher_assignments = defaultdict(set)
        self.student_assignments = {}

    def _parse_time_slot(self, slot_str):
        """時間枠の文字列をday, timeに分解"""
        for day in self.DAYS:
            if slot_str.startswith(day):
                time = slot_str[len(day):]
                if time in self.TIMES:
                    return day, time
        return None, None

    def _get_all_time_slots(self):
        """全ての利用可能な時間枠を生成"""
        slots = []
        for day in self.DAYS:
            for time in self.TIMES:
                for teacher in self.teacher_schedules:
                    if day in self.teacher_schedules[teacher]:
                        slots.append((day, time, teacher))
        return slots

    def _calculate_cost_matrix(self, students, time_slots):
        """コスト行列を計算"""
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

        return cost_matrix

    def _is_valid_assignment(self, assignments, students, time_slots):
        """割り当ての制約チェック"""
        teacher_day_counts = defaultdict(lambda: defaultdict(int))
        
        for student_idx, slot_idx in enumerate(assignments):
            if slot_idx >= 0:  # 割り当てがある場合
                day, _, teacher = time_slots[slot_idx]
                teacher_day_counts[teacher][day] += 1
                
                # 教師の1日あたりの制限をチェック
                if teacher_day_counts[teacher][day] > self.SLOTS_PER_DAY:
                    return False
        
        return True

    def _optimize_with_hungarian(self, students, initial_slots=None):
        """ハンガリアン法による最適化"""
        time_slots = initial_slots if initial_slots else self._get_all_time_slots()
        cost_matrix = self._calculate_cost_matrix(students, time_slots)
        
        # ハンガリアン法で最適化
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 結果が制約を満たすかチェック
        if not self._is_valid_assignment(col_ind, students, time_slots):
            return None, None, float('inf')
        
        # 総コストと希望外の数を計算
        total_cost = cost_matrix[row_ind, col_ind].sum()
        unwanted_count = sum(1 for i, j in zip(row_ind, col_ind) 
                           if cost_matrix[i, j] == self.PREFERENCE_COSTS['希望外'])
        
        return row_ind, col_ind, unwanted_count

    def _create_assignment_result(self, student, day, time, teacher, preference):
        """生徒の割り当て結果を作成"""
        return {
            'クライアント名': student['クライアント名'],
            '生徒名': student['生徒名'],
            '割当曜日': day,
            '割当時間': time,
            '担当講師': teacher,
            '希望順位': preference
        }

    def _get_preference_type(self, student, day, time):
        """割り当ての希望順位を取得"""
        slot_str = day + time
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key in student and student[pref_key] == slot_str:
                return pref_key
        return '希望外'

    def optimize_schedule(self, preferences_df):
        """スケジュールの最適化を実行"""
        students = preferences_df.to_dict('records')
        best_assignments = None
        min_unwanted = float('inf')
        
        # 複数回試行して最良の結果を見つける
        for attempt in range(self.MAX_ATTEMPTS):
            time_slots = self._get_all_time_slots()
            row_ind, col_ind, unwanted_count = self._optimize_with_hungarian(students, time_slots)
            
            if row_ind is not None and unwanted_count < min_unwanted:
                min_unwanted = unwanted_count
                
                # 割り当て結果を作成
                assignments = []
                for student_idx, slot_idx in enumerate(col_ind):
                    if slot_idx >= 0:
                        day, time, teacher = time_slots[slot_idx]
                        student = students[student_idx]
                        preference = self._get_preference_type(student, day, time)
                        assignment = self._create_assignment_result(student, day, time, teacher, preference)
                        assignments.append(assignment)
                
                best_assignments = assignments
                
                # 希望外がない場合は終了
                if unwanted_count == 0:
                    print(f"希望外ゼロの解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
            
            # 次の試行のために時間枠をシャッフル
            np.random.shuffle(time_slots)
        
        if min_unwanted > 0:
            print(f"試行回数{self.MAX_ATTEMPTS}回で希望外{min_unwanted}名が最良の結果でした。")
        
        return {
            'assigned': best_assignments,
            'unassigned': []
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
