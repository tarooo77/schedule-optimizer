"""スケジュール最適化のユーティリティ関数と定数（拡張版）"""

# 基本設定
TIMES = ['10時', '11時', '12時', '14時', '15時', '16時', '17時']
DAYS = ["火曜日", "水曜日", "木曜日", "金曜日"]

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

def get_all_slots(num_students, use_all_days=False):
    """
    生徒数に基づいて必要なスロットを生成
    
    Parameters:
    -----------
    num_students : int
        生徒数
    use_all_days : bool, optional
        True の場合、生徒数に関わらず全ての曜日（火曜から金曜）を使用
        False の場合、生徒数に基づいて必要な曜日のみ使用
    
    Returns:
    --------
    list
        利用可能なスロットのリスト
    """
    # 各ユニットは必ず7スロットを使用
    # 生徒数は7の倍数でなければならない
    if num_students % 7 != 0:
        raise ValueError(f"生徒数は7の倍数でなければなりません。現在: {num_students}")
    
    num_units = num_students // 7  # 生徒数で7で割った値（切り上げなし）
    if num_units > 4 and not use_all_days:
        raise ValueError(f"生徒数が多すぎます。最大生徒数は28名です。現在: {num_students}")
    
    all_slots = []
    days = DAYS
    
    if use_all_days:
        # 全ての曜日を使用
        for day in days:
            for time in TIMES:
                all_slots.append(f'{day}{time}')
    else:
        # 各ユニットに対して7スロットを割り当て
        # 3ユニットの場合は21人分のスロットが必要なので、火・水・木曜日に7スロットずつ割り当てる
        for unit in range(num_units):
            if unit < len(days):  # 曜日の範囲内の場合
                day = days[unit]  # 各ユニットに曜日を割り当て
                for time in TIMES:
                    all_slots.append(f'{day}{time}')
    
    return all_slots

def get_all_slots_full():
    """
    全ての曜日と時間帯のスロットを生成（生徒数に関わらず）
    """
    return get_all_slots(7, use_all_days=True)

def format_results(results):
    """結果を整形して表示用の文字列を生成"""
    if not results['assigned']:
        return "割り当てられた生徒がいません。"
    
    output = []
    output.append("\n=== スケジュール最適化結果 ===")
    output.append(f"割り当て完了: {len(results['assigned'])}名")
    output.append(f"未割り当て: {len(results['unassigned'])}名")
    
    # 希望達成状況
    if 'stats' in results:
        stats = results['stats']
        output.append(f"第1希望: {stats.get('第1希望', 0)}名 ({stats.get('第1希望率', 0):.1f}%)")
        output.append(f"第2希望: {stats.get('第2希望', 0)}名 ({stats.get('第2希望率', 0):.1f}%)")
        output.append(f"第3希望: {stats.get('第3希望', 0)}名 ({stats.get('第3希望率', 0):.1f}%)")
        output.append(f"希望外: {stats.get('希望外', 0)}名 ({stats.get('希望外率', 0):.1f}%)")
    
    # 曜日ごとの割り当て
    output.append("\n【曜日ごとの割り当て】")
    day_assignments = {}
    for student in results['assigned']:
        day = student['割当曜日']
        if day not in day_assignments:
            day_assignments[day] = []
        day_assignments[day].append(student)
    
    for day in sorted(day_assignments.keys()):
        output.append(f"{day}: {len(day_assignments[day])}名")
    
    return "\n".join(output)

def validate_preferences(preferences_df):
    """生徒の希望データをバリデーション"""
    # 全ての生徒が3つの希望を持っているか確認
    required_columns = ['生徒名', '第1希望', '第2希望', '第3希望']
    for col in required_columns:
        if col not in preferences_df.columns:
            raise ValueError(f"データフレームに必要なカラム '{col}' がありません")
    
    # 希望が有効なスロットか確認
    # 注意: 全ての曜日（火曜から金曜）を使用するため、get_all_slots_full()を使用
    valid_slots = get_all_slots_full()
    
    for pref in ['第1希望', '第2希望', '第3希望']:
        invalid_slots = set(preferences_df[pref]) - set(valid_slots)
        if invalid_slots:
            raise ValueError(f"{pref}に無効なスロットが含まれています: {invalid_slots}")
    
    return True
