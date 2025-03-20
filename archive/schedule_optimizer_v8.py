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

    def _calculate_client_preferred_days(self, client_students):
        """クライアントの生徒が最も希望する曜日を計算"""
        day_preferences = defaultdict(int)
        for student in client_students:
            for pref_num in [1, 2, 3]:
                pref_key = f'第{pref_num}希望'
                if pref_key not in student:
                    continue
                day, _ = self._parse_time_slot(student[pref_key])
                if day:
                    # 第1希望は重み3、第2希望は重み2、第3希望は重み1
                    day_preferences[day] += 4 - pref_num
        
        # 希望の多い順にソート
        return sorted(day_preferences.items(), key=lambda x: x[1], reverse=True)

    def _find_best_teacher_for_day(self, day, needed_slots, client):
        """指定の曜日で最適な先生を見つける"""
        best_teacher = None
        max_available = 0
        
        # すでにこのクライアントを担当している先生を優先
        if client in self.client_teacher_assignments:
            for teacher in self.client_teacher_assignments[client]:
                if day in self.teacher_schedules[teacher]:
                    available = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
                    if available >= needed_slots and available > max_available:
                        best_teacher = teacher
                        max_available = available
        
        # 他の先生も検討
        if not best_teacher:
            for teacher in self.teacher_schedules:
                if day in self.teacher_schedules[teacher]:
                    available = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
                    if available >= needed_slots and available > max_available:
                        best_teacher = teacher
                        max_available = available
        
        return best_teacher

    def _assign_students_to_slots(self, students, day, teacher, client):
        """生徒を指定の曜日・先生の時間枠に割り当て"""
        assignments = []
        remaining_students = []
        assigned_count = 0
        
        # 利用可能な時間枠を取得
        available_slots = []
        for time in self.TIMES:
            if not self.assignments[day][teacher].get(time):
                available_slots.append(time)
        
        # 各生徒の希望に基づいて割り当て
        for student in students:
            if assigned_count >= self.SLOTS_PER_DAY:
                remaining_students.append(student)
                continue
                
            assigned = False
            # まず希望の時間枠に割り当てを試みる
            for pref_num in [1, 2, 3]:
                pref_key = f'第{pref_num}希望'
                if pref_key not in student:
                    continue
                    
                pref_day, pref_time = self._parse_time_slot(student[pref_key])
                if pref_day == day and pref_time in available_slots:
                    assignments.append({
                        'クライアント名': client,
                        '生徒名': student['生徒名'],
                        '割当曜日': day,
                        '割当時間': pref_time,
                        '担当講師': teacher,
                        '希望順位': pref_key
                    })
                    available_slots.remove(pref_time)
                    self.assignments[day][teacher][pref_time] = student['生徒名']
                    assigned_count += 1
                    assigned = True
                    break
            
            # 希望の時間枠に入れられなかった場合、空いている時間枠に割り当て
            if not assigned and available_slots:
                time = available_slots[0]
                assignments.append({
                    'クライアント名': client,
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher,
                    '希望順位': '希望外'
                })
                available_slots.remove(time)
                self.assignments[day][teacher][time] = student['生徒名']
                assigned_count += 1
            elif not assigned:
                remaining_students.append(student)
        
        self.teacher_day_counts[teacher][day] = assigned_count
        self.client_day_assignments[client][day] += assigned_count
        self.client_teacher_assignments[client].add(teacher)
        
        return assignments, remaining_students

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
        
        for client, group in client_groups:
            students = group.to_dict('records')
            remaining_students = students.copy()
            
            # このクライアントの希望が多い曜日を特定
            preferred_days = self._calculate_client_preferred_days(students)
            
            # 各曜日に生徒を割り当て
            for day, _ in preferred_days:
                if not remaining_students:
                    break
                    
                # この曜日に割り当て可能な生徒数を計算
                needed_slots = min(len(remaining_students), self.SLOTS_PER_DAY)
                
                # 最適な先生を見つける
                teacher = self._find_best_teacher_for_day(day, needed_slots, client)
                if not teacher:
                    continue
                
                # 生徒を割り当て
                new_assignments, remaining_students = self._assign_students_to_slots(
                    remaining_students, day, teacher, client
                )
                
                if new_assignments:
                    all_assignments.extend(new_assignments)
            
            # 残りの生徒を他の空き枠に割り当て
            while remaining_students:
                assigned = False
                for day in self.DAYS:
                    if assigned:
                        break
                    for teacher in self.teacher_schedules:
                        if day not in self.teacher_schedules[teacher]:
                            continue
                        if self.teacher_day_counts[teacher][day] >= self.SLOTS_PER_DAY:
                            continue
                            
                        new_assignments, remaining_students = self._assign_students_to_slots(
                            remaining_students, day, teacher, client
                        )
                        
                        if new_assignments:
                            all_assignments.extend(new_assignments)
                            assigned = True
                            break
                
                if not assigned:
                    unassigned.extend(remaining_students)
                    break
        
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
