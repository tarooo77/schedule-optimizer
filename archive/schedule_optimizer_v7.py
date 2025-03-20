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

    def _parse_time_slot(self, slot_str):
        """時間枠の文字列を曜日と時間に分解"""
        for day in self.DAYS:
            if slot_str.startswith(day):
                time = slot_str[len(day):]
                if time in self.TIMES:
                    return day, time
        return None, None

    def _is_slot_available(self, teacher, day, time):
        """指定の時間枠が利用可能かチェック"""
        if day not in self.teacher_schedules[teacher]:
            return False
        if self.teacher_day_counts[teacher][day] >= self.SLOTS_PER_DAY:
            return False
        if self.assignments[day][teacher].get(time):
            return False
        return True

    def _find_best_slot_for_student(self, student, preferences):
        """生徒の希望に基づいて最適な時間枠を探す"""
        # 希望順に試行
        for pref_num in [1, 2, 3]:
            pref_key = f'第{pref_num}希望'
            if pref_key not in preferences:
                continue
                
            slot = preferences[pref_key]
            day, time = self._parse_time_slot(slot)
            if not day or not time:
                continue
            
            # 各先生について試行
            for teacher in self.teacher_schedules.keys():
                if self._is_slot_available(teacher, day, time):
                    return teacher, day, time, pref_key
        
        # 希望の時間枠が取れない場合は空いている時間枠を探す
        for teacher in self.teacher_schedules.keys():
            for day in self.DAYS:
                if day not in self.teacher_schedules[teacher]:
                    continue
                for time in self.TIMES:
                    if self._is_slot_available(teacher, day, time):
                        return teacher, day, time, '希望外'
        
        return None, None, None, None

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
            
            for student in students:
                teacher, day, time, preference = self._find_best_slot_for_student(
                    student['生徒名'],
                    student
                )
                
                if teacher and day and time:
                    # 割り当てを記録
                    self.assignments[day][teacher][time] = student['生徒名']
                    self.teacher_day_counts[teacher][day] += 1
                    self.client_teacher_assignments[client].add(teacher)
                    
                    all_assignments.append({
                        'クライアント名': client,
                        '生徒名': student['生徒名'],
                        '割当曜日': day,
                        '割当時間': time,
                        '担当講師': teacher,
                        '希望順位': preference
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
            
            # クライアントごとの先生の割り当て状況
            print("\n担当講師の割り当て:")
            teacher_counts = client_df.groupby(['担当講師', '割当曜日']).size()
            for (teacher, day), count in teacher_counts.items():
                print(f"  {teacher} ({day}): {count}名")

def main():
    optimizer = ScheduleOptimizer()
    preferences = pd.read_csv('student_preferences.csv')
    results = optimizer.optimize_schedule(preferences)
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
