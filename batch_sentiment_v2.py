"""
第2周 进阶：批量电商评价情感分析工具 V2
========================================

【今天升级了 4 个能力】
升级1: 支持命令行参数（argparse）
升级2: 支持进度条（tqdm）
升级3: 支持 JSON 格式输入
升级4: 自动提取负面评价高频问题关键词
"""

import csv
import json
import argparse
import requests
import os

try:
    from tqdm import tqdm
except ImportError:
    print('[提示] tqdm 未安装，进度条功能降级为普通打印。')
    print('安装命令: pip install tqdm')
    tqdm = lambda x, **kwargs: x


def load_reviews(filepath):
    """根据文件扩展名自动选择 CSV 或 JSON 读取"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.json':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        reviews = []
        for item in data:
            if isinstance(item, dict):
                if 'id' in item and '评价内容' in item:
                    reviews.append({'id': item['id'], '评价内容': item['评价内容']})
                else:
                    for k, v in item.items():
                        reviews.append({'id': k, '评价内容': v})
                        break
            else:
                raise ValueError(f'JSON 格式不支持: {item}')
        return reviews
    else:
        reviews = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(row)
        return reviews


def analyze_sentiment(review_text):
    """调用 Ollama 做情感分析"""
    url = 'http://localhost:11434/api/generate'
    prompt = f"""请对以下电商评价做情感分析，判断是正面/负面/中性。
评价内容：{review_text}
请严格按JSON格式返回：{{"情感": "正面/负面/中性", "理由": "一句话解释"}}
不要输出其他内容。"""
    body = {'model': 'qwen2:7b', 'prompt': prompt, 'stream': False}
    try:
        r = requests.post(url, json=body, timeout=60)
        raw = r.json()['response']
        cleaned = raw.strip().strip('`').strip()
        if cleaned.startswith('json'):
            cleaned = cleaned[4:].strip()
        return json.loads(cleaned)
    except Exception as e:
        return {'情感': '未知', '理由': f'调用失败: {e}'}


def batch_analyze(reviews, output_path):
    """批量分析，带 tqdm 进度条"""
    results = []
    for r in tqdm(reviews, desc='情感分析中', unit='条', ncols=70):
        sentiment = analyze_sentiment(r['评价内容'])
        row = {
            'id': r['id'],
            '评价内容': r['评价内容'],
            '情感': sentiment.get('情感', '未知'),
            '理由': sentiment.get('理由', '')
        }
        results.append(row)
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', '评价内容', '情感', '理由'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    return results


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


def export_negative(results, output_path):
    """把负面评价单独导出"""
    negative = [r for r in results if r['情感'] == '负面']
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'负面评价汇总（共 {len(negative)} 条）\n')
        f.write('=' * 50 + '\n')
        for r in negative:
            f.write(f"[{r['id']}] {r['评价内容']}\n")
            f.write(f"    理由：{r['理由']}\n\n")
    print(f'\n负面评价已导出到 {output_path}，共 {len(negative)} 条')
    return negative


def _ai_extract_category(review_text):
    """用 AI 判断这条负面评价属于哪个问题类别"""
    url = 'http://localhost:11434/api/generate'
    prompt = f"""请判断以下电商负面评价属于哪个问题类别。
类别只能是以下之一：质量问题、物流问题、色差问题、尺寸问题、服务问题、设计问题、其他。

评价内容：{review_text}
请直接回复类别名称，不要输出其他内容。"""
    body = {'model': 'qwen2:7b', 'prompt': prompt, 'stream': False}
    try:
        r = requests.post(url, json=body, timeout=60)
        category = r.json()['response'].strip()
        for c in ['。', '.', ' ', '：', ':']:
            category = category.split(c)[0]
        return category
    except Exception:
        return '其他'


def extract_keywords(results, negative_list, output_path, use_ai=False):
    """提取负面评价的高频问题关键词"""
    if not negative_list:
        print('\n没有负面评价，跳过关键词提取')
        return
    print('\n=== 关键词提取 ===')
    ai_categories = {}
    if use_ai:
        print('正在用 AI 分析负面评价的问题类别（较慢）...')
        for r in tqdm(negative_list, desc='AI 分析', unit='条', ncols=70):
            category = _ai_extract_category(r['评价内容'])
            ai_categories[category] = ai_categories.get(category, 0) + 1
    problem_words = {
        '起球': 0, '色差': 0, '异味': 0, '破损': 0, '开线': 0,
        '线头': 0, '缝线': 0, '太慢': 0, '慢': 0, '偏小': 0,
        '偏大': 0, '褶皱': 0, '静电': 0, '掉色': 0, '不透气': 0,
        '不舒适': 0, '不舒服': 0, '不划算': 0, '不值': 0,
        '态度差': 0, '客服': 0
    }
    for r in negative_list:
        text = r['评价内容']
        for word in problem_words:
            if word in text:
                problem_words[word] += 1
    sorted_words = sorted(
        [(w, c) for w, c in problem_words.items() if c > 0],
        key=lambda x: -x[1]
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('=' * 60 + '\n')
        f.write('负面评价关键词汇总\n')
        f.write('=' * 60 + '\n\n')
        f.write('【方法 A：AI 问题类别统计】\n')
        if ai_categories:
            for cat, count in sorted(ai_categories.items(), key=lambda x: -x[1]):
                f.write(f'{cat}: {count} 次\n')
        else:
            f.write('（未启用 AI 分析，加 --keywords 参数启用）\n')
        f.write('\n【方法 B：词频统计（高频问题词）】\n')
        if sorted_words:
            for word, count in sorted_words:
                f.write(f'"{word}": 出现 {count} 次\n')
        else:
            f.write('（未检测到预定义的问题词）\n')
    print(f'关键词汇总已导出到 {output_path}')
    print('\nTop 5 问题词:')
    for word, count in sorted_words[:5]:
        print(f'  "{word}": {count} 次')


def parse_args():
    parser = argparse.ArgumentParser(description='批量电商评价情感分析工具 V2')
    parser.add_argument('--input', '-i', default='评价数据.csv', help='输入文件路径')
    parser.add_argument('--output', '-o', default='评价分析结果.csv', help='输出文件路径')
    parser.add_argument('--keywords', '-k', action='store_true', help='开启 AI 关键词提取')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print('=' * 60)
    print('批量电商评价情感分析工具 V2')
    print('=' * 60)
    print(f'输入文件: {args.input}')
    print(f'输出文件: {args.output}')
    print(f'AI 关键词提取: {"开启" if args.keywords else "关闭"}')
    print('=' * 60)
    print('\n[1/5] 读取数据...')
    reviews = load_reviews(args.input)
    print(f'共读取 {len(reviews)} 条评价')
    print('\n[2/5] 批量情感分析...')
    results = batch_analyze(reviews, args.output)
    print('\n[3/5] 统计汇总...')
    summarize(results)
    print('\n[4/5] 导出负面评价...')
    negative_list = export_negative(results, '负面评价汇总.txt')
    print('\n[5/5] 关键词提取...')
    extract_keywords(results, negative_list, '关键词汇总.txt', use_ai=args.keywords)
    print('\n=== 全部完成 ===')