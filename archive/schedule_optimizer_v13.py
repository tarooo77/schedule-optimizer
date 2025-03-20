import pandas as pd
import random
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self):
        self.DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
        self.TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
        self.SLOTS_PER_DAY = 7
        self.MAX_ATTEMPTS = 100
        self.MAX_SWAP_ATTEMPTS = 50  # 交換試行の最大回数
        
        self.teacher_schedules = {
            '先生1': ['火曜日', '水曜日', '木曜日'],  # 金曜日休み
            '先生2': ['火曜日', '木曜日', '金曜日'],  # 水曜日休み
            '先生3': ['火曜日', '水曜日', '金曜日'],  # 木曜日休み
            '先生4': ['水曜日', '木曜日', '金曜日'],  # 火曜日休み
            '先生5': ['火曜日', '水曜日', '木曜日']   # 金曜日休み
        }

    def _initialize_state(self):
        self.assignments = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        self.teacher_day_counts = defaultdict(lambda: defaultdict(int))
        self.client_teacher_assignments = defaultdict(set)
        self.slot_availability = self._initialize_slot_availability()
        self.reserved_slots = set()
        self.student_assignments = {}  # 生徒の割り当て情報を保持

    def _reserve_third_preferences(self, problem_students):
        """問題のある生徒の第3希望を予約"""
        for student in problem_students:
            if '第3希望' in student:
                day, time = self._parse_time_slot(student['第3希望'])
                if day and time:
                    self.reserved_slots.add((day, time))

    def _initialize_slot_availability(self):
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

    def _is_slot_available(self, day, time, teacher, ignore_reserved=False):
        slot_key = (day, time)
        if not ignore_reserved and slot_key in self.reserved_slots:
            return False
        if day not in self.teacher_schedules[teacher]:
            return False
        if self.teacher_day_counts[teacher][day] >= self.SLOTS_PER_DAY:
            return False
        if self.assignments[day][teacher][time]:
            return False
        return True

    def _find_available_slots(self, student, preference=None):
        available_slots = []
        client = student['クライアント名']
        
        pref_range = [int(preference[1])] if preference else range(1, 4)
        
        for pref_num in pref_range:
            pref_key = f'第{pref_num}希望'
            if pref_key not in student:
                continue
                
            day, time = self._parse_time_slot(student[pref_key])
            if not day or not time:
                continue
            
            assigned_teachers = self.client_teacher_assignments[client]
            for teacher in assigned_teachers:
                if self._is_slot_available(day, time, teacher):
                    available_slots.append((day, time, teacher, pref_key))
            
            for teacher in self.teacher_schedules:
                if teacher not in assigned_teachers and self._is_slot_available(day, time, teacher):
                    available_slots.append((day, time, teacher, pref_key))
        
        return available_slots

    def _assign_student(self, student, day, time, teacher, pref):
        client = student['クライアント名']
        student_name = student['生徒名']
        self.assignments[day][teacher][time] = student_name
        self.slot_availability[day][time][teacher] = False
        self.teacher_day_counts[teacher][day] += 1
        self.client_teacher_assignments[client].add(teacher)
        
        # 生徒の割り当て情報を保存
        assignment = {
            'クライアント名': client,
            '生徒名': student_name,
            '割当曜日': day,
            '割当時間': time,
            '担当講師': teacher,
            '希望順位': pref,
            'student_data': student  # 元の生徒データを保持
        }
        self.student_assignments[student_name] = assignment
        return assignment

    def _unassign_student(self, student_name):
        """生徒の割り当てを解除"""
        if student_name not in self.student_assignments:
            return None
        
        assignment = self.student_assignments[student_name]
        day = assignment['割当曜日']
        time = assignment['割当時間']
        teacher = assignment['担当講師']
        
        # 割り当ての解除
        self.assignments[day][teacher][time] = ""
        self.slot_availability[day][time][teacher] = True
        self.teacher_day_counts[teacher][day] -= 1
        
        # 他の生徒がいない場合は先生の割り当ても解除
        if all(not self.assignments[day][teacher][t] for t in self.TIMES):
            self.client_teacher_assignments[assignment['クライアント名']].remove(teacher)
        
        return assignment

    def _try_swap_students(self, problem_student_name):
        """希望外の生徒と他の生徒の交換を試みる"""
        if problem_student_name not in self.student_assignments:
            return False
        
        problem_assignment = self.student_assignments[problem_student_name]
        problem_student = problem_assignment['student_data']
        
        # 問題の生徒の希望時間枠を取得
        desired_slots = []
        for pref_num in range(1, 4):
            pref_key = f'第{pref_num}希望'
            if pref_key in problem_student:
                day, time = self._parse_time_slot(problem_student[pref_key])
                if day and time:
                    desired_slots.append((day, time, pref_key))
        
        # 各希望時間枠で交換可能な生徒を探す
        for desired_day, desired_time, pref_key in desired_slots:
            for teacher in self.teacher_schedules:
                current_student_name = self.assignments[desired_day][teacher][desired_time]
                if not current_student_name:
                    continue
                
                current_assignment = self.student_assignments[current_student_name]
                current_student = current_assignment['student_data']
                
                # 現在の生徒が問題の生徒の時間枠で満足できるか確認
                problem_day = problem_assignment['割当曜日']
                problem_time = problem_assignment['割当時間']
                problem_teacher = problem_assignment['担当講師']
                
                # 両方の生徒の元の割り当てを解除
                self._unassign_student(current_student_name)
                self._unassign_student(problem_student_name)
                
                # 交換を試みる
                success = True
                
                # 問題の生徒を希望の時間枠に割り当て
                if self._is_slot_available(desired_day, desired_time, teacher, ignore_reserved=True):
                    self._assign_student(problem_student, desired_day, desired_time, teacher, pref_key)
                else:
                    success = False
                
                # 現在の生徒を問題の生徒の時間枠に割り当て
                if success and self._is_slot_available(problem_day, problem_time, problem_teacher, ignore_reserved=True):
                    # 現在の生徒の新しい希望順位を確認
                    new_pref = '希望外'
                    for pref_num in range(1, 4):
                        pref_key = f'第{pref_num}希望'
                        if pref_key in current_student:
                            check_day, check_time = self._parse_time_slot(current_student[pref_key])
                            if check_day == problem_day and check_time == problem_time:
                                new_pref = pref_key
                                break
                    
                    self._assign_student(current_student, problem_day, problem_time, problem_teacher, new_pref)
                else:
                    success = False
                
                if success:
                    return True
                
                # 交換が失敗した場合、元の状態に戻す
                self._unassign_student(current_student_name)
                self._unassign_student(problem_student_name)
                self._assign_student(current_student, desired_day, desired_time, teacher, current_assignment['希望順位'])
                self._assign_student(problem_student, problem_day, problem_time, problem_teacher, problem_assignment['希望順位'])
        
        return False

    def optimize_schedule_once(self, students, problem_students=None):
        self._initialize_state()
        all_assignments = []
        remaining_students = []
        
        if problem_students:
            self._reserve_third_preferences(problem_students)
            for student in problem_students:
                slots = self._find_available_slots(student, preference='第3希望')
                if slots:
                    day, time, teacher, pref = random.choice(slots)
                    assignment = self._assign_student(student, day, time, teacher, pref)
                    all_assignments.append(assignment)
                else:
                    remaining_students.append(student)
        
        other_students = [s for s in students if s not in (problem_students or [])]
        random.shuffle(other_students)
        
        for student in other_students:
            available_slots = self._find_available_slots(student)
            
            if available_slots:
                first_choice_slots = [s for s in available_slots if s[3] == '第1希望']
                second_choice_slots = [s for s in available_slots if s[3] == '第2希望']
                third_choice_slots = [s for s in available_slots if s[3] == '第3希望']
                
                if first_choice_slots and random.random() < 0.7:
                    day, time, teacher, pref = random.choice(first_choice_slots)
                elif second_choice_slots and random.random() < 0.8:
                    day, time, teacher, pref = random.choice(second_choice_slots)
                elif third_choice_slots:
                    day, time, teacher, pref = random.choice(third_choice_slots)
                else:
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
                        if self._is_slot_available(day, time, teacher, ignore_reserved=True):
                            assignment = self._assign_student(student, day, time, teacher, '希望外')
                            all_assignments.append(assignment)
                            assigned = True
                            break
        
        return all_assignments

    def optimize_schedule(self, preferences_df):
        students = preferences_df.to_dict('records')
        best_assignments = None
        min_unwanted = float('inf')
        problem_students = None
        
        # 第1段階: 通常の最適化
        for attempt in range(self.MAX_ATTEMPTS):
            assignments = self.optimize_schedule_once(students)
            unwanted_count = len([a for a in assignments if a['希望順位'] == '希望外'])
            
            if unwanted_count < min_unwanted:
                min_unwanted = unwanted_count
                best_assignments = assignments
                
                if unwanted_count == 0:
                    print(f"希望外ゼロの解が見つかりました！（試行回数: {attempt + 1}回）")
                    break
        
        # 第2段階: 希望外の生徒の第3希望を優先
        if min_unwanted > 0:
            print(f"第1段階: 希望外{min_unwanted}名が最良の結果でした。第3希望優先で再試行します。")
            
            problem_students = [
                s for s in students 
                if s['生徒名'] in [a['生徒名'] for a in best_assignments if a['希望順位'] == '希望外']
            ]
            
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
                print(f"第2段階: 希望外{min_unwanted}名が最良の結果でした。交換による最適化を試みます。")
        
        # 第3段階: 希望外の生徒と他の生徒の交換を試みる
        if min_unwanted > 0:
            self._initialize_state()
            for assignment in best_assignments:
                student = next(s for s in students if s['生徒名'] == assignment['生徒名'])
                self._assign_student(student, 
                                   assignment['割当曜日'],
                                   assignment['割当時間'],
                                   assignment['担当講師'],
                                   assignment['希望順位'])
            
            # 希望外の生徒それぞれについて交換を試みる
            unwanted_students = [a['生徒名'] for a in best_assignments if a['希望順位'] == '希望外']
            swaps_made = 0
            
            for student_name in unwanted_students:
                for _ in range(self.MAX_SWAP_ATTEMPTS):
                    if self._try_swap_students(student_name):
                        swaps_made += 1
                        break
            
            if swaps_made > 0:
                print(f"第3段階: {swaps_made}件の交換に成功しました。")
                best_assignments = [assignment for assignment in self.student_assignments.values()]
        
        return {
            'assigned': best_assignments,
            'unassigned': []
        }

    def save_results(self, results, output_file):
        if not results['assigned']:
            print("割り当てられた生徒がいません。")
            return
            
        df = pd.DataFrame(results['assigned'])
        df = df.drop('student_data', axis=1, errors='ignore')
        
        day_order = {day: i for i, day in enumerate(self.DAYS)}
        df['day_order'] = df['割当曜日'].map(day_order)
        df = df.sort_values(['クライアント名', 'day_order', '割当時間'])
        df = df.drop('day_order', axis=1)
        
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print("\n=== スケジュール最適化結果 ===")
        print(f"割り当て完了: {len(results['assigned'])}名")
        print(f"未割り当て: {len(results['unassigned'])}名")
        
        print("\n=== 希望順位の集計 ===")
        preference_counts = df['希望順位'].value_counts()
        total_students = len(df)
        for pref, count in preference_counts.items():
            percentage = (count / total_students) * 100
            print(f"{pref}: {count}名 ({percentage:.1f}%)")
        
        print("\n=== クライアントごとの希望順位の集計 ===")
        for client in sorted(df['クライアント名'].unique()):
            client_df = df[df['クライアント名'] == client]
            print(f"\n{client}:")
            client_prefs = client_df['希望順位'].value_counts()
            client_total = len(client_df)
            for pref, count in client_prefs.items():
                percentage = (count / client_total) * 100
                print(f"{pref}: {count}名 ({percentage:.1f}%)")
            
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
