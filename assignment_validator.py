#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
割り当て結果の検証ツール
最終割り当てデータが学生の希望と一致しているかをダブルチェックする
"""

import os
import sys
import pandas as pd
import tabulate

def validate_assignments(assignments_file, preferences_file):
    """
    割り当て結果が学生の希望（第1～第3希望）と一致しているかを検証する
    
    Parameters:
    -----------
    assignments_file : str
        割り当て結果のCSVファイルパス
    preferences_file : str
        学生の希望データのCSVファイルパス
        
    Returns:
    --------
    dict
        検証結果の統計情報
    """
    try:
        # ファイルの読み込み
        assignments_df = pd.read_csv(assignments_file)
        preferences_df = pd.read_csv(preferences_file)
        
        # 結果を格納するリスト
        validation_results = []
        errors = []
        
        # 各割り当てについて検証
        for _, row in assignments_df.iterrows():
            student_name = row['生徒名']
            assigned_time = row['割り当て時間']
            preference_type = row['希望順位']
            
            # 該当する学生の希望を取得
            student_prefs = preferences_df[preferences_df['生徒名'] == student_name]
            
            if student_prefs.empty:
                errors.append(f"エラー: {student_name} が希望データに存在しません")
                continue
                
            # 希望データから実際の希望を取得
            pref1 = student_prefs['第1希望'].values[0]
            pref2 = student_prefs['第2希望'].values[0]
            pref3 = student_prefs['第3希望'].values[0]
            
            # 実際の希望順位を確認
            actual_pref = None
            if assigned_time == pref1:
                actual_pref = '第1希望'
            elif assigned_time == pref2:
                actual_pref = '第2希望'
            elif assigned_time == pref3:
                actual_pref = '第3希望'
            else:
                actual_pref = '希望外'
            
            # 表示されている希望順位と実際の希望順位が一致しているか確認
            if preference_type != actual_pref:
                errors.append(f"エラー: {student_name} の {assigned_time} は{preference_type}と表示されていますが、実際には{actual_pref}です")
                
                # 希望順位を修正する
                preference_type = actual_pref
            
            # 検証結果を追加
            validation_results.append({
                '生徒名': student_name,
                '割り当て時間': assigned_time,
                '希望順位': actual_pref,  # 実際の希望順位を使用
                '第1希望': pref1,
                '第2希望': pref2,
                '第3希望': pref3,
                '検証結果': '一致'
            })
        
        # 統計情報の計算
        stats = {
            '総生徒数': len(validation_results),
            '検証成功': len([r for r in validation_results if r['検証結果'] == '一致']),
            '検証エラー': len(errors),
            'エラー詳細': errors,
            '検証結果': validation_results
        }
        
        return stats
    
    except Exception as e:
        print(f"検証中にエラーが発生しました: {e}")
        return {
            '総生徒数': 0,
            '検証成功': 0,
            '検証エラー': 1,
            'エラー詳細': [f"検証処理エラー: {str(e)}"],
            '検証結果': []
        }

def display_validation_results(stats):
    """
    検証結果を表示する
    
    Parameters:
    -----------
    stats : dict
        検証結果の統計情報
    """
    print("\n" + "=" * 60)
    print("🔍 最終割り当てデータの検証結果")
    print("=" * 60)
    
    print(f"\n総生徒数: {stats['総生徒数']}名")
    print(f"検証成功: {stats['検証成功']}名")
    print(f"検証エラー: {stats['検証エラー']}件")
    
    if stats['検証エラー'] > 0:
        print("\n⚠️ 検出されたエラー:")
        for error in stats['エラー詳細']:
            print(f"  - {error}")
    else:
        print("\n✅ すべての割り当てが希望データと一致しています！")
    
    # 最終割り当て結果をテーブル形式で表示
    if stats['検証結果']:
        print("\n📋 最終割り当て結果:")
        
        # 表示用のデータ整形
        table_data = []
        for result in stats['検証結果']:
            table_data.append([
                result['生徒名'],
                result['割り当て時間'],
                result['希望順位'],
                '✓' if result['検証結果'] == '一致' else '✗'
            ])
        
        # テーブル形式で表示
        headers = ['生徒名', '割り当て時間', '希望順位', '検証']
        print(tabulate.tabulate(table_data, headers=headers, tablefmt='grid'))
        
        # 希望順位の統計を計算
        pref_stats = {
            '第1希望': 0,
            '第2希望': 0,
            '第3希望': 0,
            '希望外': 0
        }
        for result in stats['検証結果']:
            pref_stats[result['希望順位']] += 1
        
        print("\n📊 希望順位の統計:")
        print(f"第1希望: {pref_stats['第1希望']}名")
        print(f"第2希望: {pref_stats['第2希望']}名")
        print(f"第3希望: {pref_stats['第3希望']}名")
        print(f"希望外: {pref_stats['希望外']}名")
        
        # コピペしやすい形式でも表示（曜日・時間順に並べ替え）
        print("\n📋 コピペ用の最終割り当て結果（曜日・時間順）:")
        
        # 曜日の順序を定義
        day_order = {'月曜日': 1, '火曜日': 2, '水曜日': 3, '木曜日': 4, '金曜日': 5, '土曜日': 6, '日曜日': 7}
        
        # 結果を曜日と時間でソート
        sorted_results = []
        for result in stats['検証結果']:
            day = result['割り当て時間'].split('日')[0] + '日'
            time = result['割り当て時間'].split('日')[1]
            time_int = int(time.split('時')[0])
            sorted_results.append({
                'result': result,
                'day': day,
                'time': time,
                'time_int': time_int,
                'day_order': day_order.get(day, 99)
            })
        
        # 曜日と時間でソート
        sorted_results.sort(key=lambda x: (x['day_order'], x['time_int']))
        
        # 曜日ごとの生徒数をカウント
        day_counts = {}
        for item in sorted_results:
            day = item['day']
            if day not in day_counts:
                day_counts[day] = 0
            day_counts[day] += 1
        
        # 曜日ごとにユニット数を決定
        # 生徒数に応じてユニット数を決定
        day_units = {}
        for day, count in day_counts.items():
            # 生徒数に応じてユニット数を決定
            # 7人以下は1ユニット、それ以上は生徒数を7で割った値を切り上げ
            units = max(1, (count + 6) // 7)  # 切り上げ除算
            day_units[day] = units
        
        # 曜日をユニットに分ける
        new_day_order = {}
        order_index = 1
        
        # 新しい曜日順序を生成
        for day in sorted(day_order.keys(), key=lambda d: day_order[d]):
            units = day_units.get(day, 1)
            if units == 1:
                new_day_order[day] = order_index
                order_index += 1
            else:
                for i in range(1, units + 1):
                    new_day_order[f"{day}{i}"] = order_index
                    order_index += 1
        
        # 生徒をユニットに割り当てる
        for day, units in day_units.items():
            if units > 1:
                # 同じ曜日の生徒を取得
                day_students = [item for item in sorted_results if item['day'] == day]
                
                # 時間ごとに生徒をグループ化
                time_groups = {}
                for student in day_students:
                    time_int = student['time_int']
                    if time_int not in time_groups:
                        time_groups[time_int] = []
                    time_groups[time_int].append(student)
                
                # 各ユニットに割り当てる生徒を格納するリスト
                unit_students = [[] for _ in range(units)]
                
                # 時間ごとに生徒を各ユニットに振り分ける
                for time_int in sorted(time_groups.keys()):
                    students = time_groups[time_int]
                    # 各時間帯の生徒を各ユニットに割り当てる
                    for i, student in enumerate(students):
                        unit_idx = i % units  # 循環的に割り当てる
                        unit_students[unit_idx].append(student)
                
                # 生徒にユニット番号を割り当てる
                for unit_idx, students in enumerate(unit_students):
                    unit_num = unit_idx + 1
                    for student in students:
                        # 元のリスト内の生徒の曜日を更新
                        for item in sorted_results:
                            if item == student:
                                item['day'] = f"{day}{unit_num}"
        
        # 結果を曜日と時間で再ソート
        for item in sorted_results:
            item['day_order'] = new_day_order.get(item['day'], 99)
        
        sorted_results.sort(key=lambda x: (x['day_order'], x['time_int']))
        
        # 同じ曜日・時間に対するカウンターを追跡
        counters = {}
        
        # 曜日ごとにグループ化して表示
        current_day = None
        for item in sorted_results:
            result = item['result']
            day = item['day']
            time = item['time']
            key = (day, time)
            
            if day != current_day:
                print(f"\n# {day}")
                current_day = day
                # 新しい曜日になったらカウンターをリセット
                counters = {}
            
            # 時間と生徒名、希望順位を表示
            print(f"{time},{result['生徒名']},{result['希望順位']}")

def run_validation():
    """
    検証処理を実行する
    
    Returns:
    --------
    bool
        True: メインメニューに戻る, False: プログラムを終了する
    """
    # 最新の結果ディレクトリを探す
    results_dir = 'results'
    if not os.path.exists(results_dir):
        print(f"エラー: 結果ディレクトリ {results_dir} が見つかりません")
        return True  # エラーの場合はメインメニューに戻る
    
    # 最新の最終結果ファイルを探す
    final_result_file = None
    
    # まず、サブディレクトリ内の final_best_result.csv を探す
    subdirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir) 
               if os.path.isdir(os.path.join(results_dir, d)) and d.startswith('optimization_run_')]
    
    if subdirs:
        # 最新のサブディレクトリを取得
        latest_subdir = max(subdirs, key=os.path.getmtime)
        potential_file = os.path.join(latest_subdir, 'final_best_result.csv')
        if os.path.exists(potential_file):
            final_result_file = potential_file
    
    # サブディレクトリで見つからなければ、直接 results ディレクトリ内を探す
    if not final_result_file:
        potential_files = [
            os.path.join(results_dir, 'equal_preference_results.csv'),
            os.path.join(results_dir, 'multi_results.csv'),
            os.path.join(results_dir, 'genetic_results.csv'),
            os.path.join(results_dir, 'chain_exchange_results.csv')
        ]
        
        existing_files = [f for f in potential_files if os.path.exists(f)]
        if existing_files:
            final_result_file = max(existing_files, key=os.path.getmtime)
    
    if not final_result_file:
        print("エラー: 最終割り当て結果ファイルが見つかりません")
        return True  # エラーの場合はメインメニューに戻る
    
    # 希望データファイル
    preferences_file = 'data/student_preferences.csv'
    if not os.path.exists(preferences_file):
        print(f"エラー: 希望データファイル {preferences_file} が見つかりません")
        return True  # エラーの場合はメインメニューに戻る
    
    print(f"\n最終割り当てファイル: {final_result_file}")
    print(f"希望データファイル: {preferences_file}")
    
    # 検証実行
    stats = validate_assignments(final_result_file, preferences_file)
    
    # 結果表示
    display_validation_results(stats)
    
    # 終了確認
    print("\nプログラムを終了しますか？")
    print("1: はい")
    print("2: いいえ、メインメニューに戻る")
    
    choice = input("\n選択してください (1/2): ").strip()
    
    if choice == "1":
        print("\nプログラムを終了します。お疲れ様でした！")
        sys.exit(0)
        return False  # プログラム終了（実際にはsys.exitで終了するのでここには到達しない）
    else:
        print("\nメインメニューに戻ります...")
        return True  # メインメニューに戻る

if __name__ == "__main__":
    run_validation()
