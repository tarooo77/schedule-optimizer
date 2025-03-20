import pandas as pd
import random

def create_dummy_data(num_students):
    """ダミーデータを生成する関数"""
    from utils import get_all_slots
    all_slots = get_all_slots(num_students)
    
    data = []
    for i in range(num_students):
        # ランダムに3つの希望を選択
        preferences = random.sample(all_slots, 3)
        data.append({
            '生徒名': f'生徒{i+1}',
            '第1希望': preferences[0],
            '第2希望': preferences[1],
            '第3希望': preferences[2]
        })
    return pd.DataFrame(data)

def create_test_data(num_students, specific_preferences=None):
    """テスト用のデータを生成する関数"""
    from utils import get_all_slots
    all_slots = get_all_slots(num_students)
    
    data = []
    
    # 特定の希望パターンが指定されている場合
    if specific_preferences:
        for i, prefs in enumerate(specific_preferences):
            if i >= num_students:
                break
            data.append({
                '生徒名': f'生徒{i+1}',
                '第1希望': prefs[0],
                '第2希望': prefs[1],
                '第3希望': prefs[2]
            })
        
        # 残りの生徒にはランダムな希望を割り当て
        for i in range(len(specific_preferences), num_students):
            preferences = random.sample(all_slots, 3)
            data.append({
                '生徒名': f'生徒{i+1}',
                '第1希望': preferences[0],
                '第2希望': preferences[1],
                '第3希望': preferences[2]
            })
    else:
        # 全生徒にランダムな希望を割り当て
        for i in range(num_students):
            preferences = random.sample(all_slots, 3)
            data.append({
                '生徒名': f'生徒{i+1}',
                '第1希望': preferences[0],
                '第2希望': preferences[1],
                '第3希望': preferences[2]
            })
    
    return pd.DataFrame(data)
