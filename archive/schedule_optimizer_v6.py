import pandas as pd
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        
        self.teacher_schedules = {
            '先生1': ['火曜日', '水曜日', '木曜日'],  # 金曜日休み
            '先生2': ['火曜日', '木曜日', '金曜日'],  # 水曜日休み
            '先生3': ['火曜日', '水曜日', '金曜日'],  # 木曜日休み
            '先生4': ['水曜日', '木曜日', '金曜日'],  # 火曜日休み
            '先生5': ['火曜日', '水曜日', '木曜日']   # 金曜日休み
        }
        
        self.assignments = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        self.teacher_day_counts = defaultdict(lambda: defaultdict(int))
        self.client_teacher_assignments = defaultdict(set)

    def _get_preference_match(self, student, day, time):
        """生徒の希望と実際の割り当ての一致を確認"""
        slot = f"{day}{time}"
        if slot == student['第1希望']:
            return '第1希望'
        elif slot == student['第2希望']:
            return '第2希望'
        elif slot == student['第3希望']:
            return '第3希望'
        return '希望外'

    def _get_teacher_availability(self):
        availability = {}
        for teacher in self.teacher_schedules:
            available_slots = 0
            for day in self.teacher_schedules[teacher]:
                available_slots += self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
            availability[teacher] = available_slots
        return availability

    def _get_best_teacher_for_client(self, client, needed_slots):
        if client in self.client_teacher_assignments:
            assigned_teachers = self.client_teacher_assignments[client]
            for teacher in assigned_teachers:
                avail = sum(self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day] 
                          for day in self.teacher_schedules[teacher])
                if avail >= needed_slots:
                    return teacher
        
        availability = self._get_teacher_availability()
        best_teacher = max(availability.items(), key=lambda x: x[1])[0]
        return best_teacher

    def _assign_students_to_teacher(self, teacher, students, client):
        assignments = []
        student_index = 0
        
        for day in self.teacher_schedules[teacher]:
            if student_index >= len(students):
                break
                
            available_slots = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
            if available_slots == 0:
                continue
                
            students_for_day = min(available_slots, len(students) - student_index)
            
            for _ in range(students_for_day):
                student = students[student_index]
                time = self.TIMES[self.teacher_day_counts[teacher][day]]
                
                # 希望順位を確認
                preference_match = self._get_preference_match(student, day, time)
                
                assignments.append({
                    'クライアント名': client,
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher,
                    '希望順位': preference_match
                })
                
                self.teacher_day_counts[teacher][day] += 1
                student_index += 1
                
        return assignments, students[student_index:]

    def optimize_schedule(self, preferences_df):
        all_assignments = []
        unassigned = []
        
        client_groups = sorted(
            preferences_df.groupby('クライアント名'),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for client, group in client_groups:
            remaining_students = group.to_dict('records')
            
            while remaining_students:
                needed_slots = len(remaining_students)
                best_teacher = self._get_best_teacher_for_client(client, needed_slots)
                
                new_assignments, remaining_students = self._assign_students_to_teacher(
                    best_teacher, remaining_students, client
                )
                
                if new_assignments:
                    all_assignments.extend(new_assignments)
                    self.client_teacher_assignments[client].add(best_teacher)
                else:
                    unassigned.extend(remaining_students)
                    break
        
        return {
            'assigned': all_assignments,
            'unassigned': unassigned
        }

    def save_results(self, results, output_file):
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
        
        # 希望順位の集計を追加
        print("\n=== 希望順位の集計 ===")
        preference_counts = df['希望順位'].value_counts()
        total_students = len(df)
        for pref, count in preference_counts.items():
            percentage = (count / total_students) * 100
            print(f"{pref}: {count}名 ({percentage:.1f}%)")
        
        print("\n=== クライアントごとの希望順位の集計 ===")
        for client in df['クライアント名'].unique():
            client_df = df[df['クライアント名'] == client]
            print(f"\n{client}:")
            client_prefs = client_df['希望順位'].value_counts()
            client_total = len(client_df)
            for pref, count in client_prefs.items():
                percentage = (count / client_total) * 100
                print(f"{pref}: {count}名 ({percentage:.1f}%)")

def main():
    optimizer = ScheduleOptimizer()
    preferences = pd.read_csv('student_preferences.csv')
    results = optimizer.optimize_schedule(preferences)
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
