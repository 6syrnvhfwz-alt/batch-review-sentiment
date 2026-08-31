"""
第 2 周 Day 3 —— 电商评价情感分析 · Web 界面
============================================
把命令行工具变成网页工具：
  - 用 Flask 框架搭一个网站
  - 打开浏览器就能看到分析结果
  - 还能上传新的 CSV 重新分析

前置条件：
  pip install flask
"""

from flask import Flask, render_template, request
import csv
import os
from collections import Counter

# ============================================
# 任务 1：理解 Flask 基础结构
# ============================================
# Flask 是一个"微型网站框架"。
# 你只需要做两件事：
#   1. 创建一个 Flask 应用（下面这行）
#   2. 定义"路由"—— 用户访问某个网址时，执行什么函数
#
# 比如：
#   @app.route('/')        → 用户访问 http://localhost:5000/ 时
#   def index():           → 执行 index() 函数
#   return render_template('index.html')  → 返回 index.html 页面

app = Flask(__name__)


# ============================================
# 任务 2：定义首页路由
# ============================================
# TODO：实现 index 函数
# 功能：读取分析结果文件，把数据传给网页
#
# 提示：
#   - 读取 评价分析结果.csv，统计正面/负面/中性数量
#   - 读取 关键词汇总.txt，获取关键词数据
#   - 用 render_template() 把数据传给 index.html
#
# 示例代码（取消注释并修改）：
@app.route('/')
def index():
    # 统计情感分布
    sentiment_counts = Counter()
    reviews = []
    if os.path.exists('评价分析结果.csv'):
        with open('评价分析结果.csv', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(row)
                sentiment_counts[row['情感']] += 1

    # 读取关键词
    keywords = []
    if os.path.exists('关键词汇总.txt'):
        with open('关键词汇总.txt', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if '": 出现' in line:
                    keyword = line.split('"')[1]
                    count = int(line.split('出现')[1].replace('次', '').strip())
                    keywords.append({'keyword': keyword, 'count': count})

    # 传给网页的数据
    data = {
        'total': len(reviews),
        'positive': sentiment_counts.get('正面', 0),
        'negative': sentiment_counts.get('负面', 0),
        'neutral': sentiment_counts.get('中性', 0),
        'keywords': keywords[:10],  # Top 10
        'dashboard_exists': os.path.exists('分析看板.png')
    }
    return render_template('index.html', data=data)

# ============================================
# 任务 3：定义负面评价列表页
# ============================================
# TODO：实现 negative_reviews 函数
# 功能：只显示负面评价，带理由
#
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
# 主程序入口
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("🌐 电商评价情感分析 · Web 界面")
    print("=" * 50)
    print("\n启动中...")
    print("打开浏览器访问: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")
    # debug=True 表示代码修改后自动重启（开发模式）
    app.run(debug=True, port=5000)
