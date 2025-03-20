import pandas as pd
import random
from collections import defaultdict
import csv

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.NUM_TEACHERS = 5
        
        # 先生の勤務日を設定（各先生は3日勤務）
        self.teacher_schedules = self._initialize_teacher_schedules()
        
        # 各時間枠での利用可能な先生の数を追跡
        self.available_slots = self._initialize_available_slots()
        
    def _initialize_teacher_schedules(self):
        """先生の勤務スケジュールを初期化（各先生は1日休み）"""
        schedules = {}
        days_off = ['火曜日', '水曜日', '木曜日', '金曜日', '金曜日']  # 5人目は金曜日固定
        
        for teacher_id in range(self.NUM_TEACHERS):
            if teacher_id < 4:
                day_off = days_off[teacher_id]  # 最初の4人は異なる曜日を休みに
            else:
                day_off = days_off[4]  # 5人目は金曜日
            
            working_days = [day for day in self.DAYS if day != day_off]
            schedules[f'先生{teacher_id + 1}'] = working_days
        
        return schedules
    
    def _initialize_available_slots(self):
        """各時間枠で利用可能な先生数を初期化"""
        available_slots = {}
        for day in self.DAYS:
            available_slots[day] = {}
            for time in self.TIMES:
                # その時間枠で勤務可能な先生の数をカウント
                count = sum(1 for teacher, days in self.teacher_schedules.items() if day in days)
                available_slots[day][time] = count
        return available_slots

    def load_preferences(self, file_path):
        """生徒の希望をCSVファイルから読み込む"""
        return pd.read_csv(file_path)

    def optimize_schedule(self, preferences_df):
        """スケジュールを最適化"""
        assignments = []
        unassigned = []
        
        # クライアントごとにグループ化
        for client, group in preferences_df.groupby('クライアント名'):
            # 各クライアントの生徒を処理
            client_assignments = self._assign_client_students(client, group)
            assignments.extend(client_assignments['assigned'])
            unassigned.extend(client_assignments['unassigned'])
        
        return {
            'assigned': assignments,
            'unassigned': unassigned
        }

    def _assign_client_students(self, client, students):
        """1つのクライアントの生徒をまとめて割り当て"""
        assignments = []
        unassigned = []
        
        # 各曜日の利用可能な先生と枠を追跡
        available_teachers = defaultdict(lambda: defaultdict(int))
        for teacher, days in self.teacher_schedules.items():
            for day in days:
                available_teachers[day][teacher] = 7  # 各先生は1日7コマまで
        
        # 生徒の希望を処理
        students_list = students.to_dict('records')
        
        # まず第1希望で試行
        for student in students_list:
            assigned = False
            for pref_num in range(1, 4):  # 第1〜第3希望を試行
                pref = student[f'第{pref_num}希望']
                day = pref[:3]  # '火曜日' など
                time = pref[3:]  # '10時' など
                
                # その日に利用可能な先生を探す
                for teacher, slots in available_teachers[day].items():
                    if slots > 0:  # まだ枠が残っている先生が見つかった
                        assignments.append({
                            'クライアント名': student['クライアント名'],
                            '生徒名': student['生徒名'],
                            '割当曜日': day,
                            '割当時間': time,
                            '担当講師': teacher,
                            '希望順位': f'第{pref_num}希望'
                        })
                        available_teachers[day][teacher] -= 1
                        assigned = True
                        break
                
                if assigned:
                    break
            
            if not assigned:
                unassigned.append(student)
        
        return {
            'assigned': assignments,
            'unassigned': unassigned
        }

    def save_results(self, results, output_file):
        """結果をCSVファイルに保存"""
        # 割り当て結果を保存
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['クライアント名', '生徒名', '割当曜日', '割当時間', '担当講師', '希望順位'])
            writer.writeheader()
            for assignment in results['assigned']:
                writer.writerow(assignment)
        
        # 未割り当ての生徒がいれば表示
        if results['unassigned']:
            print("\n未割り当ての生徒:")
            for student in results['unassigned']:
                print(f"- {student['生徒名']} ({student['クライアント名']})")

def main():
    # スケジュール最適化クラスのインスタンスを作成
    optimizer = ScheduleOptimizer()
    
    # 生徒の希望を読み込む
    preferences = optimizer.load_preferences('student_preferences.csv')
    
    # スケジュールを最適化
    results = optimizer.optimize_schedule(preferences)
    
    # 結果を保存
    optimizer.save_results(results, 'assigned_schedule.csv')
    
    print("スケジュール最適化が完了しました。")
    print(f"割り当て完了: {len(results['assigned'])}名")
    print(f"未割り当て: {len(results['unassigned'])}名")

if __name__ == "__main__":
    main()
