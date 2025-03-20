#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スケジュール最適化の結果表示モジュール
"""

def format_assignment_results(results):
    """
    割り当て結果を整形して表示する
    
    Args:
        results (dict): 割り当て結果の辞書
        
    Returns:
        str: 整形された結果の文字列
    """
    output_lines = []
    
    # 割り当て結果の表示
    output_lines.append("\n=== 割り当て結果 ===")
    
    # 割り当て済み件数を表示
    assigned_count = len(results['assigned'])
    output_lines.append(f"\n割り当て済み件数: {assigned_count}")
    
    # 曜日ごとに整理して表示
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    
    # 各曜日の割り当てを取得
    for day in days:
        day_assignments = [s for s in results['assigned'] if s['割当曜日'] == day]
        if day_assignments:
            output_lines.append(f"\n{day}: ({len(day_assignments)}件)")
            
            # 時間帯ごとに整理
            output_lines.append("----------------------------------------")
            times = ["10時", "11時", "12時", "14時", "15時", "16時", "17時"]
            for time in times:
                time_assignments = [s for s in day_assignments if s['割当時間'] == time]
                for student in time_assignments:
                    output_lines.append(f"{time}: {student['生徒名']}({student['希望順位']})")            
            output_lines.append("----------------------------------------")
        else:
            output_lines.append(f"\n{day}: (0件)")
    
    return "\n".join(output_lines)

def get_assignments_list(results):
    """
    割り当て結果をリスト形式で取得する
    
    Args:
        results (dict): 割り当て結果の辞書
        
    Returns:
        list: 割り当て結果のリスト
    """
    assignments = []
    for student in results['assigned']:
        name = student['生徒名']
        day = student['割当曜日']
        time = student['割当時間']
        pref = student['希望順位']
        assignments.append(f"{name}: {day}{time} ({pref})")
    
    return sorted(assignments)

def format_single_result_summary(results):
    """
    個別の割り当て結果のサマリーを整形して表示する
    
    Args:
        results (dict): 割り当て結果の辞書
        
    Returns:
        str: 整形されたサマリーの文字列
    """
    output_lines = []
    
    # 基本情報
    assigned_count = len(results['assigned'])
    unassigned_count = len(results['unassigned'])
    
    # 希望別の集計
    preference_counts = {'第1希望': 0, '第2希望': 0, '第3希望': 0, '希望外': 0}
    for student in results['assigned']:
        pref = student['希望順位']
        preference_counts[pref] += 1
    
    # 結果サマリーの作成
    output_lines.append("\n=== 結果サマリー ===")
    output_lines.append(f"割り当て済み: {assigned_count}名")
    output_lines.append(f"未割り当て: {unassigned_count}名")
    
    total_students = assigned_count
    for pref, count in preference_counts.items():
        percentage = count / total_students * 100 if total_students > 0 else 0
        output_lines.append(f"{pref}: {count}名 ({percentage:.1f}%)")
    
    # 曜日ごとの割り当て数
    days = ["火曜日", "水曜日", "木曜日", "金曜日"]
    output_lines.append("\n曜日ごとの割り当て:")
    for day in days:
        day_count = len([s for s in results['assigned'] if s['割当曜日'] == day])
        output_lines.append(f"{day}: {day_count}名")
    
    return "\n".join(output_lines)

def format_results_summary(results_data):
    """
    複数のテスト結果のサマリーを整形する
    
    Args:
        results_data (list): テスト結果のリスト
        
    Returns:
        str: 整形されたサマリーの文字列
    """
    output_lines = []
    
    # テストケースごとに集計
    test_cases = {}
    for result in results_data:
        case_name = result['テストケース']
        if case_name not in test_cases:
            test_cases[case_name] = []
        test_cases[case_name].append(result)
    
    # 各テストケースの統計を計算
    results_summary = {}
    for name, case_results in test_cases.items():
        if not case_results:
            continue
            
        num_students = case_results[0]['生徒数']
        
        # 各希望の割合を数値として取得
        first_prefs = [r['第1希望'] for r in case_results]
        second_prefs = [r['第2希望'] for r in case_results]
        third_prefs = [r['第3希望'] for r in case_results]
        unwanted = [r['希望外'] for r in case_results]
        
        results_summary[name] = {
            'num_students': num_students,
            'iterations': len(case_results),
            'avg_first': sum(first_prefs) / len(first_prefs),
            'avg_second': sum(second_prefs) / len(second_prefs),
            'avg_third': sum(third_prefs) / len(third_prefs),
            'avg_unwanted': sum(unwanted) / len(unwanted),
            'max_first': max(first_prefs),
            'min_unwanted': min(unwanted)
        }
    
    # 結果のサマリを表示
    output_lines.append("\n=== 全テストケースの結果サマリ ===\n")
    for name, stats in results_summary.items():
        output_lines.append(f"\n{name} ({stats['num_students']}名):")
        output_lines.append("-" * 40)
        output_lines.append(f"実行回数: {stats['iterations']}回")
        output_lines.append(f"第1希望平均: {stats['avg_first']/stats['num_students']*100:.1f}%")
        output_lines.append(f"第2希望平均: {stats['avg_second']/stats['num_students']*100:.1f}%")
        output_lines.append(f"第3希望平均: {stats['avg_third']/stats['num_students']*100:.1f}%")
        output_lines.append(f"希望外平均: {stats['avg_unwanted']/stats['num_students']*100:.1f}%")
        output_lines.append(f"第1希望最高: {stats['max_first']/stats['num_students']*100:.1f}%")
        output_lines.append(f"希望外最小: {stats['min_unwanted']/stats['num_students']*100:.1f}%")
    
    return "\n".join(output_lines)

def find_best_result(results_data):
    """
    最適な結果を見つける
    
    Args:
        results_data (list): テスト結果のリスト
        
    Returns:
        dict: 最適な結果
    """
    best_result = None
    best_score = -1

    # テストケースごとに集計
    test_cases = {}
    for result in results_data:
        case_name = result['テストケース']
        if case_name not in test_cases:
            test_cases[case_name] = []
        test_cases[case_name].append(result)
    
    # 各テストケースで最適な結果を探す
    for name, case_results in test_cases.items():
        if not case_results:
            continue
            
        num_students = case_results[0]['生徒数']
        
        # 最適な結果を保存
        for result in case_results:
            # 希望外が最小の結果を優先
            unwanted = result['希望外']
            first_pref = result['第1希望']
            
            # スコア計算: 希望外が少ない結果を優先し、同じ場合は第1希望が多い結果を優先
            current_score = -unwanted * 1000 + first_pref
            
            if current_score > best_score:
                best_score = current_score
                # 割り当て情報を取得
                assignments_list = []
                if 'assignments_list' in result:
                    assignments_list = result['assignments_list']
                elif 'assigned' in result:
                    # 割り当て情報を生成
                    for student in result['assigned']:
                        day = student['割当曜日']
                        time = student['割当時間']
                        name = student['生徒名']
                        pref = student['希望順位']
                        assignments_list.append(f"{name}: {day}{time} ({pref})")
                    assignments_list = sorted(assignments_list)
                
                # 結果に割り当て情報を追加
                result_with_assignments = result.copy()
                result_with_assignments['assignments_list'] = assignments_list
                
                best_result = {
                    'case_name': name,
                    'num_students': num_students,
                    'result': result_with_assignments
                }
    
    return best_result

def format_best_result(best_result):
    """
    最適な結果を整形する
    
    Args:
        best_result (dict): 最適な結果の辞書
        
    Returns:
        str: 整形された結果の文字列
    """
    if not best_result:
        return "最適な結果は見つかりませんでした。"
    
    output_lines = []
    
    # 最適な結果の例を表示
    output_lines.append("\n=== 最適な割り当て結果の例 ===\n")
    output_lines.append(f"テストケース: {best_result['case_name']} ({best_result['num_students']}名)")
    output_lines.append("-" * 40)
    
    result = best_result['result']
    output_lines.append(f"第1希望: {result['第1希望']}名 ({result['第1希望']/best_result['num_students']*100:.1f}%)")
    output_lines.append(f"第2希望: {result['第2希望']}名 ({result['第2希望']/best_result['num_students']*100:.1f}%)")
    output_lines.append(f"第3希望: {result['第3希望']}名 ({result['第3希望']/best_result['num_students']*100:.1f}%)")
    output_lines.append(f"希望外: {result['希望外']}名 ({result['希望外']/best_result['num_students']*100:.1f}%)")
    
    return "\n".join(output_lines)
