import pandas as pd
import random
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.NUM_TEACHERS = 5
        
        # 先生の勤務日を設定（各先生は3日勤務）
        self.teacher_schedules = self._initialize_teacher_schedules()
        
        # 各時間枠での割り当て状況を追跡
        self.assignments_by_slot = defaultdict(lambda: defaultdict(dict))
        
        # クライアントと先生の割り当てを追跡
        self.client_teacher_assignments = defaultdict(lambda: defaultdict(int))
        
    def _initialize_teacher_schedules(self):
        """先生の勤務スケジュールを初期化（各先生は1日休み）"""
        schedules = {}
        # 先生ごとの休日を固定
        off_days = {
            '先生1': '金曜日',
            '先生2': '水曜日',
            '先生3': '木曜日',
            '先生4': '火曜日',
            '先生5': '金曜日'
        }
        
        for teacher, day_off in off_days.items():
            working_days = [day for day in self.DAYS if day != day_off]
            schedules[teacher] = working_days
        
        return schedules

    def load_preferences(self, file_path):
        """生徒の希望をCSVファイルから読み込む"""
        return pd.read_csv(file_path)

    def _is_slot_available(self, teacher, day, time):
        """指定の時間枠が利用可能かチェック"""
        # 先生の勤務日かチェック
        if day not in self.teacher_schedules[teacher]:
            return False
            
        # その時間枠が既に埋まっているかチェック
        if time in self.assignments_by_slot[day][teacher]:
            return False
            
        # その日の担当数が7名未満かチェック
        day_count = sum(1 for t in self.assignments_by_slot[day][teacher].values())
        if day_count >= 7:
            return False
            
        return True

    def _find_best_day_for_client(self, client_group):
        """クライアントに最適な曜日と先生を見つける"""
        best_slots = []
        
        for teacher in self.teacher_schedules.keys():
            for day in self.DAYS:
                if day not in self.teacher_schedules[teacher]:
                    continue
                    
                # その日の担当数をカウント
                current_count = sum(1 for t in self.assignments_by_slot[day][teacher].values())
                
                if current_count == 0:  # まだ誰も割り当てられていない日
                    available_slots = len(self.TIMES)  # 全時間枠が利用可能
                    best_slots.append((day, teacher, available_slots))
        
        # 利用可能な時間枠が多い順にソート
        best_slots.sort(key=lambda x: x[2], reverse=True)
        
        return best_slots[0] if best_slots else (None, None, 0)

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化"""
        assignments = []
        unassigned = []
        
        # クライアントごとにグループ化して処理
        for client, group in preferences_df.groupby('クライアント名'):
            students = group.to_dict('records')
            num_students = len(students)
            
            # このクライアントに最適な曜日と先生を見つける
            best_day, best_teacher, _ = self._find_best_day_for_client(students)
            
            if best_day and best_teacher:
                # 利用可能な時間枠を取得
                available_times = [t for t in self.TIMES 
                                 if t not in self.assignments_by_slot[best_day][best_teacher]]
                
                # 生徒を時間枠に割り当て
                for i, student in enumerate(students):
                    if i < len(available_times):
                        time = available_times[i]
                        
                        # 割り当てを記録
                        self.assignments_by_slot[best_day][best_teacher][time] = student['生徒名']
                        
                        assignments.append({
                            'クライアント名': client,
                            '生徒名': student['生徒名'],
                            '割当曜日': best_day,
                            '割当時間': time,
                            '担当講師': best_teacher,
                            '希望順位': '配置済み'
                        })
                    else:
                        unassigned.append(student)
            else:
                unassigned.extend(students)
        
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
        
        # 結果の概要を表示
        print("\n=== スケジュール最適化結果 ===")
        print(f"割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        # クライアントごとの集計
        print("\n=== クライアントごとの割り当て状況 ===")
        client_summary = df.groupby(['クライアント名', '割当曜日', '担当講師']).size().reset_index(name='生徒数')
        for _, row in client_summary.iterrows():
            print(f"{row['クライアント名']}: {row['割当曜日']} - {row['担当講師']} ({row['生徒数']}名)")

def main():
    # スケジュール最適化クラスのインスタンスを作成
    optimizer = ScheduleOptimizer()
    
    # 生徒の希望を読み込む
    preferences = optimizer.load_preferences('student_preferences.csv')
    
    # スケジュールを最適化
    results = optimizer.optimize_schedule(preferences)
    
    # 結果を保存
    optimizer.save_results(results, 'assigned_schedule.csv')

if __name__ == "__main__":
    main()
