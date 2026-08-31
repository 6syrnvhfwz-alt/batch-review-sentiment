import requests
import json

url = 'http://localhost:11434/api/generate'
body = {
    'model': 'qwen2:7b',
    'prompt': '对这条电商评价做情感分析，判断是正面/负面/中性。\n评价：衣服质量很好 穿着很舒服\n请严格按JSON格式返回：{"情感": "正面/负面/中性", "理由": "一句话解释"}\n不要输出其他内容。',
    'stream': False
}

r = requests.post(url, json=body)
raw = r.json()['response']
print('=== 模型原始返回 ===')
print(raw)
print()

# 清理可能出现的 markdown 代码块
cleaned = raw.strip().strip('`').strip()
if cleaned.startswith('json'):
    cleaned = cleaned[4:].strip()
result = json.loads(cleaned)
print('=== 解析后 ===')
print(result)