import pandas as pd
import random

# 曜日と時間枠の定義
DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']

# 各クライアントに割り当てる生徒数（7の倍数）
clients = ['森ビル', '三菱商事', 'ソニー']
client_distribution = [35, 35, 35]  # 7の倍数で合計105になるように設定

students = []
student_id = 1

for client, num_students in zip(clients, client_distribution):
    for _ in range(num_students):
        student_name = f'生徒{student_id:03d}'
        preferences = random.sample([f"{day}{time}" for day in DAYS for time in TIMES], 3)
        students.append({
            'クライアント名': client,
            '生徒名': student_name,
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })
        student_id += 1

# DataFrameとして保存
df_students = pd.DataFrame(students)
df_students.to_csv('student_preferences.csv', index=False, encoding='utf-8-sig')

print("✅ 105名分のダミーデータ生成完了: 'student_preferences.csv'")
