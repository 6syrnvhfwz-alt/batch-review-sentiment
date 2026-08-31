"""
第2周 Day 1 任务：批量电商评价情感分析脚本
===========================================

【今天的学习目标】
1. 学会用 Python 读取 CSV 文件
2. 学会用 for 循环逐条处理数据
3. 学会把调用大模型 API 的结果保存回文件
4. 学会做简单的统计汇总

【任务拆解】
任务1: 读取 '评价数据.csv' 的所有评价
任务2: 对每条评价调用大模型判断情感（正面/负面/中性）
任务3: 把结果写入 '评价分析结果.csv'（id, 评价内容, 情感, 理由）
任务4: 统计正面/负面/中性各多少条
任务5: 把负面评价单独提取到 '负面评价汇总.txt'

【学习顺序】
先做任务1（文件读取）-> 跑通了再做任务2（调API）-> 依次往下
不要一次写完，一步一步来，每一步都运行看结果

【文件说明】
- 评价数据.csv       : 今天的输入数据（35条模拟电商评价）
- 评价分析结果.csv   : 输出文件（任务3完成后生成）
- 负面评价汇总.txt   : 输出文件（任务5完成后生成）
"""

# ============================================================
# 任务1：读取 CSV 文件
# ============================================================
# 【学习要点】：
#   - 用 import csv 导入 csv 模块
#   - 用 with open() 打开文件，文件会自动关闭
#   - csv.DictReader 可以把每行读成字典，方便用列名访问
#
# 【要完成】：
#   把 '评价数据.csv' 读进来，打印前 3 条看看格式对不对

import csv

def load_reviews(filepath):
    """读取评价CSV文件，返回评价列表"""
    reviews = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reviews.append(row)
    return reviews


# 测试任务1
if __name__ == '__main__':
    print('=== 任务1：读取 CSV ===')
    reviews = load_reviews('评价数据.csv')
    print(f'共读取 {len(reviews)} 条评价')
    print('前3条：')
    for r in reviews[:3]:
        print(r)
    print()


# ============================================================
# 任务2：调用大模型判断情感
# ============================================================
# 【学习要点】：
#   - 用 requests 库发 HTTP 请求调用 Ollama
#   - 把 prompt 写清楚，让模型只返回 JSON 格式
#   - 用 try/except 处理网络错误，别让一条错全挂
#
# 【要完成】：
#   对一条评价调用 Ollama API，拿到情感分类结果
#
# 【Ollama API 信息】
#   URL: http://localhost:11434/api/generate
#   模型: qwen2:7b（本地跑的）
#   方法: POST
#   Body: {"model": "qwen2:7b", "prompt": "...", "stream": false}

import requests
import json

def analyze_sentiment(review_text):
    """
    调用 Ollama 本地大模型，对一条评价做情感分析
    返回：{'情感': '正面'/'负面'/'中性', '理由': '一句话解释'}
    """
    url = 'http://localhost:11434/api/generate'
    prompt = f"""请对以下电商评价做情感分析，判断是正面/负面/中性。
评价内容：{review_text}
请严格按JSON格式返回：{{"情感": "正面/负面/中性", "理由": "一句话解释"}}
不要输出其他内容。"""

    body = {'model': 'qwen2:7b', 'prompt': prompt, 'stream': False}

    try:
        r = requests.post(url, json=body, timeout=60)
        raw = r.json()['response']
        # 清理 markdown 代码块包裹
        cleaned = raw.strip().strip('`').strip()
        if cleaned.startswith('json'):
            cleaned = cleaned[4:].strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f'  [调用失败] {review_text[:20]}... 错误: {e}')
        return {'情感': '未知', '理由': f'调用失败: {e}'}


# ============================================================
# 任务3：批量处理 + 保存结果
# ============================================================
# 【学习要点】：
#   - for 循环遍历所有评价
#   - 每条评价调用 analyze_sentiment()
#   - 用 csv.DictWriter 把结果写回文件
#
# 【要完成】：
#   把所有评价分析完，结果写到 '评价分析结果.csv'
#   输出文件表头：id, 评价内容, 情感, 理由

def batch_analyze(reviews, output_path):
    """批量分析评价，结果保存到CSV"""
    results = []

    for i, r in enumerate(reviews):
        print(f'  处理中... {i+1}/{len(reviews)}')
        sentiment = analyze_sentiment(r['评价内容'])
        row = {
            'id': r['id'],
            '评价内容': r['评价内容'],
            '情感': sentiment.get('情感', '未知'),
            '理由': sentiment.get('理由', '')
        }
        results.append(row)

    # 写入 CSV，utf-8-sig 避免 Excel 中文乱码
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', '评价内容', '情感', '理由'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return results


# ============================================================
# 任务4：统计汇总
# ============================================================
# 【学习要点】：
#   - 用一个字典计数：{'正面': 0, '负面': 0, '中性': 0}
#   - 算占比：某类数量 / 总数 * 100

def summarize(results):
    """统计情感分布"""
    counts = {'正面': 0, '负面': 0, '中性': 0, '未知': 0}
    for r in results:
        emo = r['情感']
        if emo in counts:
            counts[emo] += 1
    total = len(results)
    print('\n=== 情感统计 ===')
    for k, v in counts.items():
        if v > 0:
            pct = v / total * 100
            print(f'{k}: {v} 条 ({pct:.1f}%)')
    print(f'总计: {total} 条')


# ============================================================
# 任务5：提取负面评价
# ============================================================
# 【学习要点】：
#   - 用列表过滤：[x for x in list if 条件]
#   - 写入 txt 文件

def export_negative(results, output_path):
    """把负面评价单独提取到一个文件"""
    negative = [r for r in results if r['情感'] == '负面']
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'负面评价汇总（共 {len(negative)} 条）\n')
        f.write('=' * 50 + '\n')
        for r in negative:
            f.write(f"[{r['id']}] {r['评价内容']}\n")
            f.write(f"    理由：{r['理由']}\n\n")
    print(f'\n负面评价已导出到 {output_path}，共 {len(negative)} 条')


# ============================================================
# 主流程（所有任务写完后，在这里串起来）
# ============================================================
if __name__ == '__main__':
    print('=== 开始批量情感分析 ===')

    reviews = load_reviews('评价数据.csv')
    results = batch_analyze(reviews, '评价分析结果.csv')
    summarize(results)
    export_negative(results, '负面评价汇总.txt')

    print('\n=== 全部完成 ===')
