import pandas as pd
from tabulate import tabulate

def create_calendar_view(schedule_file):
    # スケジュールを読み込む
    df = pd.read_csv(schedule_file)
    
    # 時間枠の順序
    times = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
    days = ['火曜日', '水曜日', '木曜日', '金曜日']
    
    # 各曜日・時間枠ごとのスケジュールを作成
    calendar_data = []
    
    # ヘッダーを追加
    calendar_data.append(['時間'] + days)
    
    for time in times:
        row = [time]
        for day in days:
            # この時間枠の授業を取得
            classes = df[(df['割当曜日'] == day) & (df['割当時間'] == time)]
            if len(classes) > 0:
                # 授業がある場合、クライアント名と担当講師を表示
                class_info = []
                for _, c in classes.iterrows():
                    info = f"{c['クライアント名']}（{c['担当講師']}）"
                    class_info.append(info)
                cell = '\n'.join(class_info)
            else:
                cell = '---'
            row.append(cell)
        calendar_data.append(row)
    
    # カレンダーを表示
    print("\n=== 週間スケジュール ===")
    print(tabulate(calendar_data, headers='firstrow', tablefmt='grid'))
    
    # 先生ごとの担当数を表示
    print("\n=== 先生ごとの担当状況 ===")
    teacher_summary = df.groupby(['担当講師', '割当曜日']).size().unstack(fill_value=0)
    print(tabulate(teacher_summary, headers='keys', tablefmt='grid'))
    
    # クライアントごとの割り当て状況を表示
    print("\n=== クライアントごとの割り当て状況 ===")
    client_summary = df.groupby(['クライアント名', '割当曜日']).size().unstack(fill_value=0)
    client_summary['合計'] = client_summary.sum(axis=1)
    print(tabulate(client_summary, headers='keys', tablefmt='grid'))

if __name__ == "__main__":
    create_calendar_view('assigned_schedule.csv')
