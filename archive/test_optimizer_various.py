import pandas as pd
import numpy as np
from schedule_optimizer_v16 import ScheduleOptimizer
import time
import csv
from collections import defaultdict

def generate_dummy_data(client_counts):
    """
    指定されたクライアントごとの生徒数でダミーデータを生成
    
    Args:
        client_counts (dict): クライアント名をキー、ユニット数を値とする辞書
    """
    data = []
    student_id = 1
    days = ['火曜日', '水曜日', '木曜日', '金曜日']
    times = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
    
    # 全ての可能なスロットを生成
    all_slots = [day + time for day in days for time in times]
    
    for client, units in client_counts.items():
        # 各ユニットについて
        for unit in range(units):
            # 7名の生徒を生成
            for i in range(7):
                # 3つの希望をランダムに選択
                preferences = np.random.choice(all_slots, size=3, replace=False)
                first_pref = preferences[0]
                second_pref = preferences[1]
                third_pref = preferences[2]
                
                data.append({
                    'クライアント名': client,
                    '生徒名': f'生徒{student_id}',
                    '第1希望': first_pref,
                    '第2希望': second_pref,
                    '第3希望': third_pref
                })
                student_id += 1
    
    return pd.DataFrame(data)

def run_test(test_name, client_counts):
    """
    指定されたテストケースを実行
    
    Args:
        test_name (str): テストケース名
        client_counts (dict): クライアント名をキー、生徒数を値とする辞書
    """
    print(f"\n=== {test_name} ===")
    print("ダミーデータを生成しています...")
    
    # データ生成
    preferences_df = generate_dummy_data(client_counts)
    total_students = sum(client_counts.values()) * 7  # 1ユニット = 7名
    print(f"合計生徒数: {total_students}名")
    for client, units in client_counts.items():
        students = units * 7
        print(f"{client}: {students}名 ({units}ユニット)")
    
    # スケジュール最適化
    optimizer = ScheduleOptimizer()
    start_time = time.time()
    results = optimizer.optimize_schedule(preferences_df)
    end_time = time.time()
    processing_time = end_time - start_time
    
    # 結果の集計
    preference_counts = defaultdict(int)
    assigned_count = len(results['assigned'])
    unassigned_count = len(results['unassigned'])
    
    for result in results['assigned']:
        preference_counts[result['希望順位']] += 1
    
    # 結果の表示
    print(f"\n処理時間: {processing_time:.2f}秒")
    print(f"未割り当て: {unassigned_count}名")
    
    for pref in ['第1希望', '第2希望', '第3希望', '希望外']:
        count = preference_counts[pref]
        percentage = (count / assigned_count * 100) if assigned_count > 0 else 0
        print(f"{pref}: {count}名 ({percentage:.1f}%)")
    
    return {
        'test_name': test_name,
        'total_students': total_students,
        'processing_time': processing_time,
        'unassigned': unassigned_count,
        'first_choice': preference_counts['第1希望'],
        'second_choice': preference_counts['第2希望'],
        'third_choice': preference_counts['第3希望'],
        'no_preference': preference_counts['希望外']
    }

def main():
    # テストケースの定義
    iterations_per_case = 10  # 各ケースの繰り返し回数
    
    test_cases = [
        ("基本ケース（21名）", {'森ビル': 3}),  # 21名（3ユニット）
        ("やや多めのケース（25名）", {'森ビル': 4}),  # 25名（4ユニットに分散）
        ("4ユニット分（28名）", {'森ビル': 4})  # 28名（4ユニットに分散）
    ]
    
    # 各テストケースを10回ずつ実行
    all_results = []
    for test_name, client_counts in test_cases:
        print(f"\n{'='*50}")
        print(f"テストケース: {test_name}")
        print(f"{'='*50}")
        
        for i in range(10):
            print(f"\nイテレーション {i+1}/{iterations_per_case}")
            result = run_test(test_name, client_counts)
            all_results.append(result)
    
    # 結果をCSVファイルに保存
    with open('optimization_test_results_various.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'test_name', 'total_students', 'processing_time', 'unassigned',
            'first_choice', 'second_choice', 'third_choice', 'no_preference'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    
    print("\n全てのテスト結果は optimization_test_results_various.csv に保存されました。")

if __name__ == "__main__":
    main()
