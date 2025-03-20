import pandas as pd

def print_border():
    print("-" * 120)

def print_calendar_header():
    print("時間      | 火曜日                    | 水曜日                    | 木曜日                    | 金曜日")
    print_border()

def format_cell(classes):
    if len(classes) == 0:
        return "---"
    class_info = [f"{c['クライアント名']}（{c['担当講師']}）" for _, c in classes.iterrows()]
    return ", ".join(class_info)

def create_calendar_view(schedule_file):
    # スケジュールを読み込む
    df = pd.read_csv(schedule_file)
    
    # 時間枠の順序
    times = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
    days = ['火曜日', '水曜日', '木曜日', '金曜日']
    
    # カレンダーを表示
    print("\n=== 週間スケジュール ===")
    print_calendar_header()
    
    for time in times:
        row = [f"{time:<9}"]
        for day in days:
            classes = df[(df['割当曜日'] == day) & (df['割当時間'] == time)]
            cell = format_cell(classes)
            row.append(f" {cell:<25}")
        print("|".join(row))
    print_border()
    
    # 先生ごとの担当状況を表示
    print("\n=== 先生ごとの担当状況 ===")
    print("先生      | 火曜日 | 水曜日 | 木曜日 | 金曜日 | 合計")
    print_border()
    
    teacher_summary = df.groupby(['担当講師', '割当曜日']).size().unstack(fill_value=0)
    teacher_summary['合計'] = teacher_summary.sum(axis=1)
    
    for teacher in sorted(df['担当講師'].unique()):
        if teacher in teacher_summary.index:
            row = [f"{teacher:<9}"]
            for day in days:
                count = teacher_summary.loc[teacher, day] if day in teacher_summary.columns else 0
                row.append(f" {count:>6}")
            row.append(f" {teacher_summary.loc[teacher, '合計']:>6}")
            print("|".join(row))
    print_border()
    
    # クライアントごとの割り当て状況を表示
    print("\n=== クライアントごとの割り当て状況 ===")
    print("クライアント| 火曜日 | 水曜日 | 木曜日 | 金曜日 | 合計")
    print_border()
    
    client_summary = df.groupby(['クライアント名', '割当曜日']).size().unstack(fill_value=0)
    client_summary['合計'] = client_summary.sum(axis=1)
    
    for client in sorted(df['クライアント名'].unique()):
        if client in client_summary.index:
            row = [f"{client:<11}"]
            for day in days:
                count = client_summary.loc[client, day] if day in client_summary.columns else 0
                row.append(f" {count:>6}")
            row.append(f" {client_summary.loc[client, '合計']:>6}")
            print("|".join(row))
    print_border()

if __name__ == "__main__":
    create_calendar_view('assigned_schedule.csv')
