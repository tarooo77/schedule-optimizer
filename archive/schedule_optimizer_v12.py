import pandas as pd
import random
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        self.MAX_ATTEMPTS = 100  # 最大試行回数
        
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
        self.slot_availability = self._initialize_slot_availability()
        self.reserved_slots = set()  # 第3希望用に予約された時間枠

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

    def _is_slot_available(self, day, time, teacher):
        """指定の時間枠が利用可能かチェック"""
        slot_key = (day, time)
        if slot_key in self.reserved_slots:
            return False
        if day not in self.teacher_schedules[teacher]:
            return False
        if self.teacher_day_counts[teacher][day] >= self.SLOTS_PER_DAY:
            return False
        if self.assignments[day][teacher][time]:
            return False
        return True

    def _find_available_slots(self, student, preference=None):
        """生徒の希望から利用可能なスロットを探す"""
        available_slots = []
        client = student['クライアント名']
        
        # 特定の希望順位のみを確認
        pref_range = [int(preference[1])] if preference else range(1, 4)
        
        for pref_num in pref_range:
            pref_key = f'第{pref_num}希望'
            if pref_key not in student:
                continue
                
            day, time = self._parse_time_slot(student[pref_key])
            if not day or not time:
                continue
            
            # まず、このクライアントを担当している先生を確認
            assigned_teachers = self.client_teacher_assignments[client]
            for teacher in assigned_teachers:
                if self._is_slot_available(day, time, teacher):
                    available_slots.append((day, time, teacher, pref_key))
            
            # 次に、新しい先生を確認
            for teacher in self.teacher_schedules:
                if teacher not in assigned_teachers and self._is_slot_available(day, time, teacher):
                    available_slots.append((day, time, teacher, pref_key))
        
        return available_slots

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

    def _reserve_third_preferences(self, problem_students):
        """問題のある生徒の第3希望を予約"""
        for student in problem_students:
            if '第3希望' in student:
                day, time = self._parse_time_slot(student['第3希望'])
                if day and time:
                    self.reserved_slots.add((day, time))

    def optimize_schedule_once(self, students, problem_students=None):
        """1回のスケジュール最適化を試行"""
        self._initialize_state()
        all_assignments = []
        remaining_students = []
        
        # 問題のある生徒の第3希望を予約
        if problem_students:
            self._reserve_third_preferences(problem_students)
            # 問題のある生徒を第3希望で割り当て
            for student in problem_students:
                slots = self._find_available_slots(student, preference='第3希望')
                if slots:
                    day, time, teacher, pref = random.choice(slots)
                    assignment = self._assign_student(student, day, time, teacher, pref)
                    all_assignments.append(assignment)
                else:
                    remaining_students.append(student)
        
        # 残りの生徒をランダムな順序で処理
        other_students = [s for s in students if s not in (problem_students or [])]
        random.shuffle(other_students)
        
        for student in other_students:
            # 利用可能な全てのスロットを取得
            available_slots = self._find_available_slots(student)
            
            if available_slots:
                # ランダムに選択（ただし第1希望を優先）
                first_choice_slots = [s for s in available_slots if s[3] == '第1希望']
                second_choice_slots = [s for s in available_slots if s[3] == '第2希望']
                third_choice_slots = [s for s in available_slots if s[3] == '第3希望']
                
                if first_choice_slots and random.random() < 0.7:  # 70%の確率で第1希望を選択
                    day, time, teacher, pref = random.choice(first_choice_slots)
                elif second_choice_slots and random.random() < 0.8:  # 残りの80%で第2希望
                    day, time, teacher, pref = random.choice(second_choice_slots)
                elif third_choice_slots:  # それ以外は第3希望
                    day, time, teacher, pref = random.choice(third_choice_slots)
                else:  # どれもなければランダムに選択
                    day, time, teacher, pref = random.choice(available_slots)
                
                assignment = self._assign_student(student, day, time, teacher, pref)
                all_assignments.append(assignment)
            else:
                remaining_students.append(student)
        
        # 残りの生徒を空いている時間枠に割り当て
        for student in remaining_students:
            assigned = False
            for day in self.DAYS:
                if assigned:
                    break
                for time in self.TIMES:
                    if assigned:
                        break
                    for teacher in self.teacher_schedules:
                        if self._is_slot_available(day, time, teacher):
                            assignment = self._assign_student(student, day, time, teacher, '希望外')
                            all_assignments.append(assignment)
                            assigned = True
                            break
        
        return all_assignments

    def optimize_schedule(self, preferences_df):
        """希望外がゼロになるまで最適化を繰り返す"""
        students = preferences_df.to_dict('records')
        best_assignments = None
        min_unwanted = float('inf')
        problem_students = None
        
        # まず通常の最適化を試みる
        for attempt in range(self.MAX_ATTEMPTS):
            assignments = self.optimize_schedule_once(students)
            unwanted_count = len([a for a in assignments if a['希望順位'] == '希望外'])
            
            if unwanted_count < min_unwanted:
                min_unwanted = unwanted_count
                best_assignments = assignments
                
                if unwanted_count == 0:
                    print(f"希望外ゼロの解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
        
        # 希望外が出た場合、それらの生徒の第3希望を優先して再試行
        if min_unwanted > 0:
            print(f"第1段階: 希望外{min_unwanted}名が最良の結果でした。第3希望優先で再試行します。")
            
            # 希望外になった生徒を特定
            problem_students = [
                s for s in students 
                if s['生徒名'] in [a['生徒名'] for a in best_assignments if a['希望順位'] == '希望外']
            ]
            
            # 第3希望を優先して再試行
            min_unwanted = float('inf')
            for attempt in range(self.MAX_ATTEMPTS):
                assignments = self.optimize_schedule_once(students, problem_students)
                unwanted_count = len([a for a in assignments if a['希望順位'] == '希望外'])
                
                if unwanted_count < min_unwanted:
                    min_unwanted = unwanted_count
                    best_assignments = assignments
                    
                    if unwanted_count == 0:
                        print(f"希望外ゼロの解が見つかりました！（第3希望優先、試行回数: {attempt + 1}回）")
                        break
            
            if min_unwanted > 0:
                print(f"第2段階: 希望外{min_unwanted}名が最良の結果でした。")
        
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
