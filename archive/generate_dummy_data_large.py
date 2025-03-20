import csv
import random

# 定数定義
DAYS = ['火曜日', '水曜日', '木曜日', '金曜日']
TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']

# クライアントデータ定義（規模を拡大）
CLIENTS = {
    '森ビル': 60,      # 従来の3倍
    '三菱商事': 140,   # 従来の3倍弱
    'ソニー': 100,     # 従来の3倍弱
}

def generate_preferences():
    """生徒の希望時間を生成する"""
    # すべての可能な時間枠をリストアップ
    all_slots = [f"{day}{time}" for day in DAYS for time in TIMES]
    # ランダムに3つ選択（重複なし）
    return random.sample(all_slots, 3)

def main():
    # 出力するデータを格納するリスト
    data = []
    
    # ヘッダー行を追加
    data.append(['クライアント名', '生徒名', '第1希望', '第2希望', '第3希望'])
    
    # クライアントごとにデータを生成
    for client, num_students in CLIENTS.items():
        for i in range(num_students):
            # 生徒名を生成（例：森ビル_生徒1）
            student_name = f"{client}_生徒{i+1}"
            
            # 希望時間を生成
            preferences = generate_preferences()
            
            # データを追加
            data.append([
                client,
                student_name,
                preferences[0],
                preferences[1],
                preferences[2]
            ])
    
    # CSVファイルに書き出し
    with open('student_preferences.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    print(f"ダミーデータを生成しました。")
    print(f"合計生徒数: {sum(CLIENTS.values())}名")
    for client, num in CLIENTS.items():
        print(f"{client}: {num}名")

if __name__ == "__main__":
    main()
