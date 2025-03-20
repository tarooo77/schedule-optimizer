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
        self.slot_availability = self._initialize_slot_availability()

    def _initialize_slot_availability(self):
        """各時間枠の利用可能状況を初期化"""
        availability = defaultdict(lambda: defaultdict(lambda: defaultdict(bool)))
        for day in self.DAYS:
            for time in self.TIMES:
                for teacher in self.teacher_schedules:
                    if day in self.teacher_schedules[teacher]:
                        availability[day][time][teacher] = True
        return availability

    def _parse_time_slot(self, slot_str):
        for day in self.DAYS:
            if slot_str.startswith(day):
                time = slot_str[len(day):]
                if time in self.TIMES:
                    return day, time
        return None, None

    def _get_slot_conflicts(self, students):
        """時間枠ごとの競合数をカウント"""
        conflicts = defaultdict(lambda: defaultdict(int))
        for student in students:
            for pref_num in [1, 2, 3]:
                pref_key = f'第{pref_num}希望'
                if pref_key not in student:
                    continue
                day, time = self._parse_time_slot(student[pref_key])
                if day and time:
                    conflicts[day][time] += 1
        return conflicts

    def _find_alternative_slot(self, student, excluded_slots=None):
        """競合の少ない代替スロットを探す"""
        if excluded_slots is None:
            excluded_slots = set()
        
        client = student['クライアント名']
        best_day = None
        best_time = None
        best_teacher = None
        best_pref = None
        min_conflicts = float('inf')
        
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key not in student:
                continue
                
            day, time = self._parse_time_slot(student[pref_key])
            if not day or not time:
                continue
                
            slot_key = (day, time)
            if slot_key in excluded_slots:
                continue
                
            # この時間枠で利用可能な先生を探す
            for teacher in self.teacher_schedules:
                if (day in self.teacher_schedules[teacher] and 
                    self.slot_availability[day][time][teacher] and
                    self.teacher_day_counts[teacher][day] < self.SLOTS_PER_DAY):
                    
                    current_conflicts = len([
                        1 for t in self.teacher_schedules 
                        if not self.slot_availability[day][time][t]
                    ])
                    
                    if current_conflicts < min_conflicts:
                        min_conflicts = current_conflicts
                        best_day = day
                        best_time = time
                        best_teacher = teacher
                        best_pref = pref_key
        
        return best_day, best_time, best_teacher, best_pref

    def _assign_student(self, student, day, time, teacher, pref):
        """生徒を時間枠に割り当て"""
        client = student['クライアント名']
        self.assignments[day][teacher][time] = student['生徒名']
        self.slot_availability[day][time][teacher] = False
        self.teacher_day_counts[teacher][day] += 1
        self.client_teacher_assignments[client].add(teacher)
        
        return {
            'クライアント名': client,
            '生徒名': student['生徒名'],
            '割当曜日': day,
            '割当時間': time,
            '担当講師': teacher,
            '希望順位': pref
        }

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化"""
        all_assignments = []
        students = preferences_df.to_dict('records')
        
        # 競合状況を分析
        conflicts = self._get_slot_conflicts(students)
        
        # 第1希望での割り当てを試みる（競合が少ない順）
        remaining_students = []
        assigned_slots = set()
        
        for student in students:
            if '第1希望' not in student:
                remaining_students.append(student)
                continue
                
            day, time = self._parse_time_slot(student['第1希望'])
            if not day or not time:
                remaining_students.append(student)
                continue
            
            # 競合が多い時間枠は第2希望以降を試みる
            if conflicts[day][time] > 5:  # 競合閾値を調整可能
                day, time, teacher, pref = self._find_alternative_slot(student)
                if day and time and teacher:
                    assignment = self._assign_student(student, day, time, teacher, pref)
                    all_assignments.append(assignment)
                    assigned_slots.add((day, time))
                else:
                    remaining_students.append(student)
            else:
                # 競合が少ない場合は第1希望を試みる
                found_teacher = None
                for teacher in self.teacher_schedules:
                    if (day in self.teacher_schedules[teacher] and 
                        self.slot_availability[day][time][teacher] and
                        self.teacher_day_counts[teacher][day] < self.SLOTS_PER_DAY):
                        found_teacher = teacher
                        break
                
                if found_teacher:
                    assignment = self._assign_student(student, day, time, found_teacher, '第1希望')
                    all_assignments.append(assignment)
                    assigned_slots.add((day, time))
                else:
                    remaining_students.append(student)
        
        # 残りの生徒を第2希望、第3希望で割り当て
        still_remaining = []
        for student in remaining_students:
            day, time, teacher, pref = self._find_alternative_slot(student, assigned_slots)
            if day and time and teacher:
                assignment = self._assign_student(student, day, time, teacher, pref)
                all_assignments.append(assignment)
                assigned_slots.add((day, time))
            else:
                still_remaining.append(student)
        
        # まだ割り当てられていない生徒を空いている時間枠に割り当て
        unassigned = []
        for student in still_remaining:
            assigned = False
            for day in self.DAYS:
                if assigned:
                    break
                for time in self.TIMES:
                    if assigned:
                        break
                    for teacher in self.teacher_schedules:
                        if (day in self.teacher_schedules[teacher] and 
                            self.slot_availability[day][time][teacher] and
                            self.teacher_day_counts[teacher][day] < self.SLOTS_PER_DAY):
                            
                            assignment = self._assign_student(student, day, time, teacher, '希望外')
                            all_assignments.append(assignment)
                            assigned = True
                            break
            
            if not assigned:
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
