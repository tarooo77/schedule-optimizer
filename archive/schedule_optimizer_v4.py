import pandas as pd
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7  # 1日の授業枠数
        
        # 先生の勤務スケジュール（各先生の休日を設定）
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
        
    def _can_assign_teacher_to_day(self, teacher, day):
        """先生が指定の曜日に割り当て可能かチェック"""
        if day not in self.teacher_schedules[teacher]:
            return False
        return self.teacher_day_counts[teacher][day] < self.SLOTS_PER_DAY

    def _find_available_slot(self, client_size):
        """クライアントの生徒全員を収容できる曜日と先生の組み合わせを探す"""
        needed_days = (client_size + self.SLOTS_PER_DAY - 1) // self.SLOTS_PER_DAY
        best_assignments = []
        
        # 各先生の各曜日での空き状況を確認
        for teacher in self.teacher_schedules.keys():
            available_days = []
            for day in self.teacher_schedules[teacher]:
                if self._can_assign_teacher_to_day(teacher, day):
                    available_slots = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
                    if available_slots == self.SLOTS_PER_DAY:  # 完全に空いている日を優先
                        available_days.append((day, available_slots))
            
            # この先生が担当可能な日数が十分あれば記録
            if len(available_days) >= needed_days:
                best_assignments.append((teacher, available_days))
        
        # 最も効率的な割り当てを返す
        best_assignments.sort(key=lambda x: len(x[1]), reverse=True)
        return best_assignments[0] if best_assignments else (None, [])

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化"""
        assignments = []
        unassigned = []
        
        # クライアントごとにグループ化して処理
        for client, group in preferences_df.groupby('クライアント名'):
            students = group.to_dict('records')
            num_students = len(students)
            
            # このクライアントに最適な先生と曜日の組み合わせを見つける
            teacher, available_days = self._find_available_slot(num_students)
            
            if not teacher:
                unassigned.extend(students)
                continue
            
            # 生徒を割り当て
            student_index = 0
            for day, _ in available_days:
                if student_index >= num_students:
                    break
                    
                # この日に割り当て可能な生徒数を計算
                remaining_slots = self.SLOTS_PER_DAY - self.teacher_day_counts[teacher][day]
                students_for_day = min(remaining_slots, num_students - student_index)
                
                # 生徒を時間枠に割り当て
                for time_index in range(students_for_day):
                    student = students[student_index]
                    time = self.TIMES[self.teacher_day_counts[teacher][day]]
                    
                    # 割り当てを記録
                    assignments.append({
                        'クライアント名': client,
                        '生徒名': student['生徒名'],
                        '割当曜日': day,
                        '割当時間': time,
                        '担当講師': teacher
                    })
                    
                    # カウンターを更新
                    self.teacher_day_counts[teacher][day] += 1
                    student_index += 1
            
            # 割り当てできなかった生徒を記録
            if student_index < num_students:
                unassigned.extend(students[student_index:])
        
        return {
            'assigned': assignments,
            'unassigned': unassigned
        }

    def save_results(self, results, output_file):
        """結果をCSVファイルに保存"""
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
        for client, group in df.groupby('クライアント名'):
            print(f"\n{client}:")
            for (day, teacher), subgroup in group.groupby(['割当曜日', '担当講師']):
                print(f"  {day} - {teacher}: {len(subgroup)}名")

def main():
    # スケジュール最適化クラスのインスタンスを作成
    optimizer = ScheduleOptimizer()
    
    # 生徒の希望を読み込む
    preferences = pd.read_csv('student_preferences.csv')
    
    # スケジュールを最適化
    results = optimizer.optimize_schedule(preferences)
    
    # 結果を保存
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
