"""スケジュール最適化のユーティリティ関数と定数"""

# 基本設定
TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']

def get_unit_name(unit_num):
    """ユニット番号から曜日を生成（火曜から金曜の4日間のみ）"""
    days = ['火', '水', '木', '金']
    return f"{days[unit_num % 4]}曜日"

# コスト設定
DEFAULT_PREFERENCE_COSTS = {
    '第1希望': -300,  # 第1希望と第2希望の差を縮小
    '第2希望': -250,  # 第2希望と第3希望の差も縮小
    '第3希望': -200,  # 第3希望までは比較的近い値に
    '希望外': 5000    # 希望外は依然として大きなペナルティ
}

def get_all_slots(num_students):
    """生徒数に基づいて必要なスロットを生成（火曜から金曜の4日間のみ）"""
    # 各ユニットは必ず7スロットを使用
    # 生徒数は7の倍数でなければならない
    if num_students % 7 != 0:
        raise ValueError(f"生徒数は7の倍数でなければなりません。現在: {num_students}")
    
    num_units = num_students // 7  # 生徒数で7で割った値（切り上げなし）
    if num_units > 4:
        raise ValueError(f"生徒数が多すぎます。最大生徒数は28名です。現在: {num_students}")
    
    all_slots = []
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    
    # 各ユニットに対して7スロットを割り当て
    # 3ユニットの場合は21人分のスロットが必要なので、火・水・木曜日に7スロットずつ割り当てる
    for unit in range(num_units):
        if unit < len(days):  # 曜日の範囲内の場合
            day = days[unit]  # 各ユニットに曜日を割り当て
            for time in TIMES:
                all_slots.append(f'{day}{time}')
    
    return all_slots

def format_results(results):
    """結果を整形して表示用の文字列を生成"""
    if not results['assigned']:
        return "割り当てられた生徒がいません。"
    
    output = []
    output.append("\n=== スケジュール最適化結果 ===")
    output.append(f"割り当て完了: {len(results['assigned'])}名")
    output.append(f"未割り当て: {len(results['unassigned'])}名")
    
    # 希望順位の集計
    preference_counts = {
        '第1希望': 0,
        '第2希望': 0,
        '第3希望': 0,
        '希望外': 0
    }
    
    for student in results['assigned']:
        pref = student['希望順位']
        if pref in preference_counts:
            preference_counts[pref] += 1
    
    output.append("\n=== 希望順位の集計 ===")
    total_students = len(results['assigned'])
    for pref, count in preference_counts.items():
        if total_students > 0:
            percentage = count / total_students * 100
            output.append(f"{pref}: {count}名 ({percentage:.1f}%)")
    
    return "\n".join(output)

def validate_preferences(preferences_df):
    """生徒の希望データをバリデーション"""
    required_columns = ['生徒名', '第1希望', '第2希望', '第3希望']
    
    # 必要なカラムが存在するか確認
    for col in required_columns:
        if col not in preferences_df.columns:
            raise ValueError(f"必要なカラム '{col}' がデータフレームにありません。")
    
    # 生徒名が重複していないか確認
    if preferences_df['生徒名'].duplicated().any():
        raise ValueError("生徒名が重複しています。")
    
    # 各生徒の希望が有効なスロットか確認
    num_students = len(preferences_df)
    all_slots = set(get_all_slots(num_students))
    for pref in ['第1希望', '第2希望', '第3希望']:
        invalid_slots = set(preferences_df[pref]) - all_slots
        if invalid_slots:
            raise ValueError(f"{pref}に無効なスロットが含まれています: {invalid_slots}")
    
    return True
