import pandas as pd
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        
        # 先生の勤務スケジュール
        self.teacher_schedules = {
            '先生1': ['火曜日', '水曜日', '木曜日'],  # 金曜日休み
            '先生2': ['火曜日', '木曜日', '金曜日'],  # 水曜日休み
            '先生3': ['火曜日', '水曜日', '金曜日'],  # 木曜日休み
            '先生4': ['水曜日', '木曜日', '金曜日'],  # 火曜日休み
            '先生5': ['火曜日', '水曜日', '木曜日']   # 金曜日休み
        }
        
        # 割り当て状況を管理
        self.assignments = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        self.teacher_day_counts = defaultdict(lambda: defaultdict(int))
        self.client_teacher_assignments = defaultdict(set)
        
    def _get_teacher_availability(self):
        """各先生の空き状況を取得"""
        availability = {}
        for teacher in self.teacher_schedules:
            available_slots = 0
            for day in self.teacher_schedules[teacher]:
                available_slots += self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
            availability[teacher] = available_slots
        return availability

    def _get_best_teacher_for_client(self, client, needed_slots):
        """クライアントに最適な先生を選択"""
        # すでにこのクライアントに割り当てられている先生がいれば、その先生を優先
        if client in self.client_teacher_assignments:
            assigned_teachers = self.client_teacher_assignments[client]
            for teacher in assigned_teachers:
                avail = sum(self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day] 
                          for day in self.teacher_schedules[teacher])
                if avail >= needed_slots:
                    return teacher
        
        # 利用可能なスロット数が最も多い先生を選択
        availability = self._get_teacher_availability()
        best_teacher = max(availability.items(), key=lambda x: x[1])[0]
        return best_teacher

    def _assign_students_to_teacher(self, teacher, students, client):
        """生徒を先生の空き枠に割り当て"""
        assignments = []
        student_index = 0
        
        # 各曜日に対して割り当てを試みる
        for day in self.teacher_schedules[teacher]:
            if student_index >= len(students):
                break
                
            available_slots = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
            if available_slots == 0:
                continue
                
            # この日に割り当て可能な生徒数を計算
            students_for_day = min(available_slots, len(students) - student_index)
            
            # 生徒を時間枠に割り当て
            for _ in range(students_for_day):
                student = students[student_index]
                time = self.TIMES[self.teacher_day_counts[teacher][day]]
                
                assignments.append({
                    'クライアント名': client,
                    '生徒名': student['生徒名'],
                    '割当曜日': day,
                    '割当時間': time,
                    '担当講師': teacher
                })
                
                self.teacher_day_counts[teacher][day] += 1
                student_index += 1
                
        return assignments, students[student_index:]

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
            remaining_students = group.to_dict('records')
            
            while remaining_students:
                # 残りの生徒数に基づいて最適な先生を選択
                needed_slots = len(remaining_students)
                best_teacher = self._get_best_teacher_for_client(client, needed_slots)
                
                # 生徒を割り当て
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
        """結果をCSVファイルに保存"""
        if not results['assigned']:
            print("割り当てられた生徒がいません。")
            return
            
        # 結果をDataFrameに変換
        df = pd.DataFrame(results['assigned'])
        
        # 曜日と時間でソート
        day_order = {day: i for i, day in enumerate(self.DAYS)}
        df['day_order'] = df['割当曜日'].map(day_order)
        df = df.sort_values(['クライアント名', 'day_order', '割当時間'])
        df = df.drop('day_order', axis=1)
        
        # CSVに保存
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # 結果の詳細を表示
        print("\n=== スケジュール最適化結果 ===")
        print(f"割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        # クライアントごとの詳細な集計
        print("\n=== クライアントごとの割り当て状況 ===")
        client_summary = df.groupby(['クライアント名', '割当曜日', '担当講師']).size()
        
        for client in sorted(df['クライアント名'].unique()):
            print(f"\n{client}:")
            client_data = client_summary[client]
            for (day, teacher), count in client_data.items():
                print(f"  {day} - {teacher}: {count}名")
            total = client_data.sum()
            print(f"  合計: {total}名")

def main():
    optimizer = ScheduleOptimizer()
    preferences = pd.read_csv('student_preferences.csv')
    results = optimizer.optimize_schedule(preferences)
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
