import pandas as pd
import numpy as np
from schedule_optimizer_v14 import ScheduleOptimizer
import generate_dummy_data
import time

def run_test():
    results = []
    
    for test_num in range(10):
        print(f"\nテスト {test_num + 1}/10 開始")
        
        # 新しいダミーデータを生成
        generate_dummy_data.main()
        
        # 最適化を実行
        start_time = time.time()
        optimizer = ScheduleOptimizer()
        preferences = pd.read_csv('student_preferences.csv')
        optimization_results = optimizer.optimize_schedule(preferences)
        end_time = time.time()
        
        # 結果を分析
        df = pd.DataFrame(optimization_results['assigned'])
        preference_counts = df['希望順位'].value_counts()
        total_students = len(df)
        
        # 結果を保存
        test_result = {
            'テスト番号': test_num + 1,
            '処理時間': end_time - start_time,
            '総生徒数': total_students
        }
        
        for pref in ['第1希望', '第2希望', '第3希望', '希望外']:
            count = preference_counts.get(pref, 0)
            percentage = (count / total_students) * 100
            test_result[f'{pref}人数'] = count
            test_result[f'{pref}割合'] = percentage
            
        results.append(test_result)
        
        print(f"処理時間: {test_result['処理時間']:.2f}秒")
        for pref in ['第1希望', '第2希望', '第3希望', '希望外']:
            print(f"{pref}: {test_result[f'{pref}人数']}名 ({test_result[f'{pref}割合']:.1f}%)")
    
    # 全体の統計を計算
    df_results = pd.DataFrame(results)
    print("\n=== 10回のテスト結果の統計 ===")
    print(f"平均処理時間: {df_results['処理時間'].mean():.2f}秒")
    print(f"処理時間の標準偏差: {df_results['処理時間'].std():.2f}秒")
    print("\n希望順位の平均割合:")
    for pref in ['第1希望', '第2希望', '第3希望', '希望外']:
        mean_percentage = df_results[f'{pref}割合'].mean()
        std_percentage = df_results[f'{pref}割合'].std()
        print(f"{pref}: {mean_percentage:.1f}% (±{std_percentage:.1f}%)")
    
    # 詳細な結果をCSVに保存
    df_results.to_csv('optimization_test_results.csv', index=False, encoding='utf-8')
    print("\n詳細な結果は optimization_test_results.csv に保存されました。")

if __name__ == "__main__":
    run_test()
