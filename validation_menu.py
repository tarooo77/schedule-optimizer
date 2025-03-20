#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最適化後の検証メニュー
equal_preference_optimizer.py から呼び出される
"""

import sys
from assignment_validator import run_validation

def show_validation_menu():
    """
    検証メニューを表示し、ユーザーの選択に応じて処理を実行する
    
    Returns:
    --------
    bool
        True: メインメニューに戻る, False: プログラムを終了
    """
    print("\n" + "=" * 60)
    print("🔍 最終チェックメニュー")
    print("=" * 60)
    
    print("\n次のオプションから選択してください:")
    print("1: 最終割り当てデータをダブルチェックする")
    print("2: 同じデータでもう一度最適化を実行する")
    print("3: プログラムを終了する")
    
    choice = input("\n選択してください (1-3): ").strip()
    
    if choice == "1":
        # 検証処理を実行
        continue_program = run_validation()
        return continue_program  # run_validationの結果に応じてメインメニューに戻るか終了する
    elif choice == "2":
        return True  # メインメニューに戻る (再最適化のため)
    else:  # choice == "3" またはその他
        print("\nプログラムを終了します。お疲れ様でした！")
        sys.exit(0)
        return False  # プログラム終了

if __name__ == "__main__":
    show_validation_menu()
