import pandas as pd
import random

DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
NUM_TEACHERS = 5  # 5 teachers available

def generate_dummy_data():
    num_clients = int(input("クライアント数を入力してください: "))
    clients = [f'クライアント{chr(65 + i)}' for i in range(num_clients)]
    num_students = int(input("生徒数を入力してください: "))

    students = []
    for i in range(num_students):
        client = random.choice(clients)
        student_name = f'{client}_生徒{i+1}'
        preferences = random.sample([f"{day}{time}" for day in DAYS for time in TIMES], 3)
        students.append({
            'クライアント名': client,
            '生徒名': student_name,
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })

    df_students = pd.DataFrame(students)
    print("ダミーデータが生成されました！")
    print(df_students.to_string(index=False))
    return df_students

def assign_schedule(df, distribute_evenly=True):
    total_students = len(df)
    
    # Calculate optimal distribution based on total students
    if distribute_evenly:
        # Option 1: Distribute students evenly across all days
        students_per_day = [total_students // len(DAYS) + (1 if i < total_students % len(DAYS) else 0) 
                           for i in range(len(DAYS))]
    else:
        # Option 2: Fill as many days as possible with 7 students
        full_days = total_students // 7
        remaining = total_students % 7
        students_per_day = [7] * full_days + ([remaining] if remaining > 0 else []) + [0] * (len(DAYS) - full_days - (1 if remaining > 0 else 0))
        # Make sure we don't exceed the number of days
        students_per_day = students_per_day[:len(DAYS)]
    
    print(f"配分計画: {dict(zip(DAYS, students_per_day))}")
    
    # Create a dictionary to track which slots are filled
    filled_slots = {day: set() for day in DAYS}
    
    # Create a dictionary to track how many students are assigned to each day
    day_counts = {day: 0 for day in DAYS}
    
    # Allocate maximum capacity per day
    day_capacity = dict(zip(DAYS, students_per_day))
    
    # Shuffle students to ensure fairness
    shuffled_students = df.sample(frac=1).reset_index(drop=True)
    
    assignments = []
    unassigned_students = []
    
    # First pass: Try to assign based on preferences
    for _, student in shuffled_students.iterrows():
        assigned = False
        
        for pref in ['第1希望', '第2希望', '第3希望']:
            requested_day = student[pref][:3]
            requested_time = student[pref][3:]
            
            # Check if day has reached its limit or if slot is already filled
            if day_counts[requested_day] < day_capacity[requested_day] and requested_time not in filled_slots[requested_day]:
                # Assign student
                assignments.append({
                    'クライアント名': student['クライアント名'],
                    '生徒名': student['生徒名'],
                    '割当曜日時間': student[pref],
                    '希望順位': pref,
                    '担当講師': f"先生{(day_counts[requested_day] % NUM_TEACHERS) + 1}"
                })
                
                # Update tracking
                day_counts[requested_day] += 1
                filled_slots[requested_day].add(requested_time)
                assigned = True
                break
        
        # If student couldn't be assigned to any preference
        if not assigned:
            unassigned_students.append(student)
    
    # Second pass: Try to place unassigned students in any available slot
    if unassigned_students:
        # Sort days by how many more students they need
        days_by_need = sorted(DAYS, key=lambda d: day_capacity[d] - day_counts[d], reverse=True)
        
        for student in unassigned_students[:]:
            for day in days_by_need:
                if day_counts[day] < day_capacity[day]:
                    available_times = set(TIMES) - filled_slots[day]
                    if available_times:
                        chosen_time = random.choice(list(available_times))
                        assignments.append({
                            'クライアント名': student['クライアント名'],
                            '生徒名': student['生徒名'],
                            '割当曜日時間': f"{day}{chosen_time}",
                            '希望順位': "予備割当",
                            '担当講師': f"先生{(day_counts[day] % NUM_TEACHERS) + 1}"
                        })
                        
                        # Update tracking
                        day_counts[day] += 1
                        filled_slots[day].add(chosen_time)
                        unassigned_students.remove(student)
                        break
    
    # Final verification: Ensure each day has the planned number of students
    for day, planned in zip(DAYS, students_per_day):
        if day_counts[day] != planned:
            print(f"警告: {day}の生徒数は{day_counts[day]}名です（目標は{planned}名）")
    
    print(f"割り当て完了: {len(assignments)}名")
    if unassigned_students:
        print(f"未割り当て: {len(unassigned_students)}名")
    
    return assignments, unassigned_students

def display_schedule(assignments):
    while True:
        print("\nスケジュールの表示方法を選択してください:")
        print("1: 生徒ごとに表示")
        print("2: 曜日ごとに表示")
        print("3: 先生単位で表示")
        print("4: クライアント単位で表示")
        print("5: 終了")
        choice = input("選択肢 (1/2/3/4/5): ")

        if choice == "1":
            print("📅 生徒ごとのスケジュール:")
            for a in sorted(assignments, key=lambda x: x['生徒名']):
                print(f"{a['生徒名']} - {a['割当曜日時間']} ({a['希望順位']}) - {a['担当講師']}")
        
        elif choice == "2":
            print("📅 曜日ごとのスケジュール:")
            day_schedule = {day: [] for day in DAYS}

            for a in assignments:
                day = a['割当曜日時間'][:3]
                day_schedule[day].append((a['割当曜日時間'][3:], a['クライアント名'], a['生徒名'], a['担当講師']))

            for day, slots in day_schedule.items():
                print(f"\n{day}: {len(slots)}名")
                for slot in sorted(slots):
                    print(f"  {slot[0]} - {slot[1]} ({slot[2]}) - {slot[3]}")
        
        elif choice == "3":
            print("📅 先生ごとのスケジュール:")
            teacher_schedule = {}
            
            for a in assignments:
                if a['担当講師'] not in teacher_schedule:
                    teacher_schedule[a['担当講師']] = {day: [] for day in DAYS}
                
                day = a['割当曜日時間'][:3]
                time = a['割当曜日時間'][3:]
                teacher_schedule[a['担当講師']][day].append((time, a['クライアント名'], a['生徒名']))
            
            for teacher, days in sorted(teacher_schedule.items()):
                print(f"\n👨‍🏫 {teacher}:")
                for day, slots in days.items():
                    if slots:
                        print(f"  {day}: {len(slots)}名")
                        for slot in sorted(slots):
                            print(f"    {slot[0]} - {slot[1]} ({slot[2]})")
        
        elif choice == "4":
            print("📅 クライアントごとのスケジュール:")
            client_schedule = {}
            
            for a in assignments:
                if a['クライアント名'] not in client_schedule:
                    client_schedule[a['クライアント名']] = []
                
                client_schedule[a['クライアント名']].append((a['割当曜日時間'], a['生徒名'], a['担当講師']))
            
            for client, slots in sorted(client_schedule.items()):
                print(f"\n🏢 {client}: {len(slots)}名")
                for slot in sorted(slots):
                    print(f"  {slot[0]} - {slot[1]} - {slot[2]}")
        
        elif choice == "5":
            print("終了します。")
            break
        
        else:
            print("無効な選択肢です。")

def main():
    mode = input("モードを選択してください (1: ダミーモード, 2: 本気モード): ")
    
    if mode == "1":
        df = generate_dummy_data()
    else:
        print("本気モード: データをCSVファイルから読み込みます。")
        try:
            file_path = input("CSVファイルのパスを入力してください: ")
            df = pd.read_csv(file_path)
            print(f"{len(df)}名の生徒データを読み込みました。")
        except Exception as e:
            print(f"エラー: {e}")
            return
    
    distribution_choice = input("生徒の配分方法を選択してください (1: 均等に分ける, 2: できるだけ7名で埋める): ")
    distribute_evenly = (distribution_choice == "1")
    
    assignments, unassigned = assign_schedule(df, distribute_evenly)
    
    if assignments:
        display_schedule(assignments)
        
        # Save to CSV if needed
        save_option = input("スケジュールをCSVファイルに保存しますか？ (y/n): ")
        if save_option.lower() == 'y':
            output_file = input("出力ファイル名を入力してください: ")
            pd.DataFrame(assignments).to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"スケジュールを {output_file} に保存しました。")
    else:
        print("スケジュールを作成できませんでした。")

if __name__ == "__main__":
    main()