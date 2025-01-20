import json

file_path = 'reports/comprehensive_report.json'

with open(file_path, 'r') as file:
    data = json.load(file)
    print(data)