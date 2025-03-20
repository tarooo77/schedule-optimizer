import pandas as pd
from schedule_optimizer_v16 import create_dummy_data

# 7名のダミーデータを生成して表示
dummy_data = create_dummy_data(7)
print("=== 生成されたダミーデータ ===")
print(dummy_data)

# CSVに保存（オプション）
dummy_data.to_csv('dummy_data.csv', index=False, encoding='utf-8')
print("\nダミーデータをdummy_data.csvに保存しました")
