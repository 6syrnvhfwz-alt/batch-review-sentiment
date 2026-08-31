"""
第 2 周 Day 4 —— Web 界面 + 实时 AI 分析
========================================
在 Day 3 的基础上增加：
  - 网页上有输入框，粘贴评价 → 点按钮
  - 后端实时调用 Ollama 大模型分析
  - 结果直接显示在网页上

新知识点：
  - HTML 表单（form）：用户在网页上输入内容
  - POST 请求：把用户输入的数据发给服务器
  - request.form：Flask 接收表单数据
  - 网页同步等待：AI 分析需要时间，点按钮后网页会转圈，正常现象
"""

from flask import Flask, render_template, request
import csv
import os
import requests
import json
from collections import Counter

app = Flask(__name__)

# Ollama 配置（跟 Day 1 的脚本一样）
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2:7b"


# ============================================
# AI 分析函数（从 Day 1 的 batch_sentiment 搬过来）
# ============================================
def analyze_sentiment(review_text):
    """调用本地 Ollama 大模型，分析一条评价的情感。返回：(情感, 理由)"""
    prompt = f"""请分析以下电商评价的情感倾向，只回复 JSON 格式：
{{"情感": "正面/负面/中性", "理由": "简短理由"}}

评价：{review_text}"""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    result = response.json()
    answer = result['response'].strip()

    # 去掉 AI 可能加的 ```json 标记
    if '```' in answer:
        parts = answer.split('```')
        answer = parts[1] if len(parts) > 1 else answer
        if answer.startswith('json'):
            answer = answer[4:]
        answer = answer.strip()

    # 尝试解析 JSON
    sentiment = "中性"
    reason = answer
    try:
        data = json.loads(answer)
        sentiment = data.get('情感', '中性')
        reason = data.get('理由', answer)
    except Exception:
        # JSON 解析失败时退回到关键词判断
        if "正面" in answer:
            sentiment = "正面"
        elif "负面" in answer:
            sentiment = "负面"

    return sentiment, reason



# ============================================
# 首页（Day 3 已有 + 新增输入表单）
# ============================================
@app.route('/')
def index():
    sentiment_counts = Counter()
    reviews = []
    if os.path.exists('评价分析结果.csv'):
        with open('评价分析结果.csv', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(row)
                sentiment_counts[row['情感']] += 1

    keywords = []
    if os.path.exists('关键词汇总.txt'):
        with open('关键词汇总.txt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '": 出现' in line:
                    keyword = line.split('"')[1]
                    count = int(line.split('出现')[1].replace('次', '').strip())
                    keywords.append({'keyword': keyword, 'count': count})

    data = {
        'total': len(reviews),
        'positive': sentiment_counts.get('正面', 0),
        'negative': sentiment_counts.get('负面', 0),
        'neutral': sentiment_counts.get('中性', 0),
        'keywords': keywords[:10],
        'dashboard_exists': os.path.exists('分析看板.png')
    }
    return render_template('index.html', data=data)


# ============================================
# 负面评价列表页（Day 3 已有）
# ============================================
@app.route('/negative')
def negative_reviews():
    negatives = []
    if os.path.exists('评价分析结果.csv'):
        with open('评价分析结果.csv', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['情感'] == '负面':
                    negatives.append({
                        'text': row['评价内容'],
                        'reason': row['理由']
                    })
    return render_template('negative.html', negatives=negatives)


# ============================================
# 任务：实时分析页（今天的新内容）
# ============================================
# TODO：实现 analyze 函数
# 功能：
#   1. 接收网页表单发来的评价文本（request.form）
#   2. 按换行拆分成多条评价
#   3. 循环调用 analyze_sentiment() 分析每条
#   4. 把结果传给 result.html 显示
@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. 接收表单数据（textarea 的 name 是 "reviews"）
    text = request.form.get('reviews','')

    # 2. 按换行拆分，去掉空行
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # 3. 逐条调用 AI 分析
    results = []
    for line in lines:
        sentiment,reason = analyze_sentiment(line)
        results.append({
            'text':line,
            'sentiment':sentiment,
            'reason':reason
        })

    # 4.渲染结果页
    return render_template('result.html',results=results)


if __name__ == '__main__':
    print("=" * 50)
    print("🌐 电商评价情感分析系统 · 实时AI版")
    print("=" * 50)
    print("\n打开浏览器访问: http://localhost:5000")
    print("确保 Ollama 正在运行（ollama list 能看到 qwen2:7b）")
    print("按 Ctrl+C 停止服务\n")
    app.run(debug=True, port=5000)
