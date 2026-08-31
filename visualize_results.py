"""
第 2 周 Day 2 —— 电商评价情感分析 · 数据可视化
==========================================
把昨天的分析结果变成图表：
  - 饼图：正面/负面/中性评价占比
  - 柱状图：差评关键词 Top 10
  - 组合看板：两张图放在一起

你只需要在 TODO 标记处填代码，每个任务填完就跑一次看效果。

用到的新知识：
  - matplotlib：Python 最流行的画图库
  - 中文显示设置：matplotlib 默认不支持中文，需要特殊配置
"""

import csv
import matplotlib.pyplot as plt
from collections import Counter
import os

# ============================================
# 【重要】让 matplotlib 能显示中文
# ============================================
# 原理：matplotlib 默认字体不包含中文字符，
# 所以中文会显示为方块。这里手动指定中文字体。
# Windows 系统自带 "Microsoft YaHei"（微软雅黑）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'STSong']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


# ============================================
# 任务 1：读取昨天的分析结果
# ============================================
def load_results(filename='评价分析结果.csv'):
    results = []
    with open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


# ============================================
# 任务 2：画饼图 —— 情感分布
# ============================================
def plot_pie(results):
    # 1. 统计各情感的数量
    sentiment_counts = Counter()
    for r in results:
        sentiment_counts[r['情感']] += 1

    # 2. 准备数据
    labels = ['正面', '负面', '中性']
    sizes = [
        sentiment_counts.get('正面', 0),
        sentiment_counts.get('负面', 0),
        sentiment_counts.get('中性', 0)
    ]
    colors = ['#66b3ff', '#ff9999', '#99ff99']

    # 3. 画饼图
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90)
    plt.title('电商评价情感分布')
    plt.show()


# ============================================
# 任务 3：画柱状图 —— 差评关键词 Top 10
# ============================================
def plot_bar_keywords(results):
    keyword_counter = Counter()
    try:
        with open('关键词汇总.txt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 格式是 "关键词": 出现 X 次
                if '": 出现' in line and '次' in line:
                    # 提取引号里的关键词
                    keyword = line.split('"')[1]
                    # 提取数字
                    count = int(line.split('出现')[1].replace('次', '').strip())
                    keyword_counter[keyword] = count
    except FileNotFoundError:
        print("⚠️ 关键词汇总.txt 不存在，先跑 V2 脚本生成它")
        return

    if not keyword_counter:
        print("没有关键词数据，跳过柱状图")
        return

    # 取 Top 10
    top10 = keyword_counter.most_common(10)
    words = [item[0] for item in top10]
    counts = [item[1] for item in top10]

    # 画水平柱状图
    plt.figure(figsize=(10, 6))
    plt.barh(words[::-1], counts[::-1], color='#ff6b6b')
    plt.xlabel('出现次数')
    plt.title('差评关键词 Top 10')
    plt.tight_layout()
    plt.show()


# ============================================
# 任务 4：组合看板 —— 两张图放在一起
# ============================================
def plot_dashboard(results):
    # 1. 先准备饼图数据
    sentiment_counts = Counter()
    for r in results:
        sentiment_counts[r['情感']] += 1

    labels = ['正面', '负面', '中性']
    sizes = [
        sentiment_counts.get('正面', 0),
        sentiment_counts.get('负面', 0),
        sentiment_counts.get('中性', 0)
    ]
    colors = ['#66b3ff', '#ff9999', '#99ff99']

    # 2. 再准备柱状图数据
    keyword_counter = Counter()
    try:
        with open('关键词汇总.txt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '": 出现' in line and '次' in line:
                    keyword = line.split('"')[1]
                    count = int(line.split('出现')[1].replace('次', '').strip())
                    keyword_counter[keyword] = count
    except FileNotFoundError:
        print("⚠️ 关键词汇总.txt 不存在")
        return

    top10 = keyword_counter.most_common(10)
    words = [item[0] for item in top10]
    counts = [item[1] for item in top10]

    # 3. 创建 1行2列 的子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('电商评价情感分析看板', fontsize=16, fontweight='bold')

    # 左边：饼图
    ax1.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90)
    ax1.set_title('情感分布')

    # 右边：柱状图
    ax2.barh(words[::-1], counts[::-1], color='#ff6b6b')
    ax2.set_xlabel('出现次数')
    ax2.set_title('差评关键词 Top 10')

    plt.tight_layout()

    # 4. 保存为图片
    plt.savefig('分析看板.png', dpi=150, bbox_inches='tight')
    print("✅ 看板已保存为 分析看板.png")
    plt.show()


# ============================================
# 主程序
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("📊 电商评价情感分析 · 数据可视化")
    print("=" * 50)
    
    # 加载数据
    results = load_results()
    if not results:
        print("❌ 没有读取到数据，请确认 评价分析结果.csv 存在")
    else:
        print(f"\n✅ 读取到 {len(results)} 条评价数据\n")
        
        # 任务 2
        print("--- 任务 2：饼图 ---")
        plot_pie(results)
        
        # 任务 3
        print("\n--- 任务 3：柱状图 ---")
        plot_bar_keywords(results)
        
        # 任务 4（进阶）
        print("\n--- 任务 4：组合看板 ---")
        plot_dashboard(results)
