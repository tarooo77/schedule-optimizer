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
        self.client_day_assignments = defaultdict(lambda: defaultdict(int))

    def _parse_time_slot(self, slot_str):
        for day in self.DAYS:
            if slot_str.startswith(day):
                time = slot_str[len(day):]
                if time in self.TIMES:
                    return day, time
        return None, None

    def _is_slot_available(self, day, time, teacher):
        """指定の時間枠が利用可能かチェック"""
        if day not in self.teacher_schedules[teacher]:
            return False
        if self.teacher_day_counts[teacher][day] >= self.SLOTS_PER_DAY:
            return False
        if self.assignments[day][teacher][time]:
            return False
        return True

    def _find_best_slot_for_student(self, student, preference_num=None):
        """生徒の希望に基づいて最適な時間枠を見つける"""
        client = student['クライアント名']
        pref_range = [preference_num] if preference_num else range(1, 4)
        
        for pref_num in pref_range:
            pref_key = f'第{pref_num}希望'
            if pref_key not in student:
                continue
                
            day, time = self._parse_time_slot(student[pref_key])
            if not day or not time:
                continue

            # まず、すでにこのクライアントを担当している先生を確認
            assigned_teachers = self.client_teacher_assignments[client]
            for teacher in assigned_teachers:
                if self._is_slot_available(day, time, teacher):
                    return day, time, teacher, pref_key

            # 次に、新しい先生を探す
            for teacher in self.teacher_schedules:
                if teacher not in assigned_teachers and self._is_slot_available(day, time, teacher):
                    return day, time, teacher, pref_key
                    
        return None, None, None, None

    def _find_any_available_slot(self, student):
        """空いている時間枠を探す（希望外）"""
        client = student['クライアント名']
        assigned_teachers = self.client_teacher_assignments[client]
        
        # まず、すでに割り当てられている曜日と先生を優先
        for day in self.DAYS:
            if self.client_day_assignments[client][day] > 0:
                for teacher in assigned_teachers:
                    for time in self.TIMES:
                        if self._is_slot_available(day, time, teacher):
                            return day, time, teacher

        # 次に、新しい曜日でも既存の先生を使う
        for teacher in assigned_teachers:
            for day in self.DAYS:
                for time in self.TIMES:
                    if self._is_slot_available(day, time, teacher):
                        return day, time, teacher

        # 最後に、完全に新しいスロットを探す
        for teacher in self.teacher_schedules:
            for day in self.DAYS:
                for time in self.TIMES:
                    if self._is_slot_available(day, time, teacher):
                        return day, time, teacher
                        
        return None, None, None

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化"""
        all_assignments = []
        unassigned = []
        
        # クライアントを生徒数の多い順にソート
        client_groups = sorted(
            preferences_df.groupby('クライアント名'),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        # まず第1希望で割り当て
        remaining_students = []
        for client, group in client_groups:
            students = group.to_dict('records')
            for student in students:
                day, time, teacher, pref = self._find_best_slot_for_student(student, 1)
                if day and time and teacher:
                    self.assignments[day][teacher][time] = student['生徒名']
                    self.teacher_day_counts[teacher][day] += 1
                    self.client_teacher_assignments[client].add(teacher)
                    self.client_day_assignments[client][day] += 1
                    
                    all_assignments.append({
                        'クライアント名': client,
                        '生徒名': student['生徒名'],
                        '割当曜日': day,
                        '割当時間': time,
                        '担当講師': teacher,
                        '希望順位': pref
                    })
                else:
                    remaining_students.append(student)

        # 第2希望、第3希望で割り当て
        still_remaining = []
        for student in remaining_students:
            day, time, teacher, pref = self._find_best_slot_for_student(student)
            if day and time and teacher:
                self.assignments[day][teacher][time] = student['生徒名']
                self.teacher_day_counts[teacher][day] += 1
                self.client_teacher_assignments[student['クライアント名']].add(teacher)
                self.client_day_assignments[student['クライアント名']][day] += 1
                
                all_assignments.append({
                    'クライアント名': student['クライアント名'],
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher,
                    '希望順位': pref
                })
            else:
                still_remaining.append(student)

        # 残りの生徒を空いている時間枠に割り当て
        for student in still_remaining:
            day, time, teacher = self._find_any_available_slot(student)
            if day and time and teacher:
                self.assignments[day][teacher][time] = student['生徒名']
                self.teacher_day_counts[teacher][day] += 1
                self.client_teacher_assignments[student['クライアント名']].add(teacher)
                self.client_day_assignments[student['クライアント名']][day] += 1
                
                all_assignments.append({
                    'クライアント名': student['クライアント名'],
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher,
                    '希望順位': '希望外'
                })
            else:
                unassigned.append(student)
        
        return {
            'assigned': all_assignments,
            'unassigned': unassigned
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
