import pandas as pd
import numpy as np
from schedule_optimizer_v16 import ScheduleOptimizer

def generate_test_data(num_students):
    """テストデータを生成する"""
    # 全ての可能なスロットを生成
    days = ['火曜日', '水曜日', '木曜日', '金曜日']
    times = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
    all_slots = [f"{day}{time}" for day in days for time in times]
    
    # テストデータを生成
    test_data = []
    for i in range(num_students):
        # 3つの異なる希望をランダムに選択
        preferences = np.random.choice(all_slots, size=3, replace=False)
        student_data = {
            'クライアント名': '森ビル',
            '生徒名': f'生徒{i+1}',
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        }
        test_data.append(student_data)
    
    return pd.DataFrame(test_data)

def run_test(num_students, num_iterations):
    """指定された回数だけテストを実行する"""
    optimizer = ScheduleOptimizer()
    success_count = 0
    
    print(f"\n=== テスト開始（生徒数: {num_students}名、繰り返し回数: {num_iterations}回）===\n")
    
    for i in range(num_iterations):
        print(f"\nイテレーション {i+1}/{num_iterations}")
        print("=" * 50)
        
        # テストデータを生成
        print("テストデータを生成中...")
        test_data = generate_test_data(num_students)
        
        try:
            # スケジュール最適化を実行
            results = optimizer.optimize_schedule(test_data)
            
            # 結果を分析
            df = pd.DataFrame(results)
            preference_counts = df['希望順位'].value_counts()
            total = len(df)
            
            print("\n結果:")
            for pref, count in preference_counts.items():
                percentage = (count / total) * 100
                print(f"{pref}: {count}名 ({percentage:.1f}%)")
            
            if '希望外' not in preference_counts:
                success_count += 1
                print("\n✅ このイテレーションは成功です（希望外の割り当てなし）")
            else:
                print("\n❌ このイテレーションは失敗です（希望外の割り当てあり）")
                
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
    
    print("\n=== テスト完了 ===")
    print(f"成功率: {success_count}/{num_iterations} ({(success_count/num_iterations)*100:.1f}%)")

def main():
    print("=== スケジューリングアルゴリズムテスト ===")
    
    while True:
        try:
            num_students = int(input("\n生徒数を入力してください（例: 21）: "))
            if num_students <= 0:
                print("生徒数は1以上の整数を入力してください。")
                continue
            break
        except ValueError:
            print("有効な整数を入力してください。")
    
    while True:
        try:
            num_iterations = int(input("テストの繰り返し回数を入力してください（例: 10）: "))
            if num_iterations <= 0:
                print("繰り返し回数は1以上の整数を入力してください。")
                continue
            break
        except ValueError:
            print("有効な整数を入力してください。")
    
    run_test(num_students, num_iterations)

if __name__ == "__main__":
    main()
