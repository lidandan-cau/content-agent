#!/usr/bin/env python3
"""
心理知识日更 Agent
- 每天生成一个心理学知识点 + 一个相关故事
- 同时输出小红书版 + 公众号版
- 通过 Server酱 推送到微信
"""

import os
import time
from datetime import datetime

import openai
import requests


# ────────────────────────────────────────
# 按周几划定心理学主题方向
# ────────────────────────────────────────

TOPIC_HINTS = {
    0: "认知心理学——思维偏差与认知扭曲（确认偏误、过度泛化、灾难化思维、非黑即白思维等）",
    1: "情绪心理学——情绪的本质与调节（情绪命名、情绪压抑的代价、情感颗粒度、情绪的信号意义）",
    2: "关系心理学——依恋、沟通与边界（依恋类型、非暴力沟通、课题分离、投射、共情疲劳）",
    3: "发展心理学——童年经历与成长模式（内在小孩、原生家庭模式、心理创伤与修复、重新养育自己）",
    4: "行为心理学——习惯、动机与行为改变（强化与惩罚、拖延的心理根源、习惯回路、自我效能感）",
    5: "积极心理学——幸福感、韧性与心流（心流体验、心理韧性、感恩练习、PERMA模型、自我决定理论）",
    6: "自由选题——近期有共鸣的心理学概念，可结合社会热点或日常生活场景",
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ────────────────────────────────────────
# 心理学知识素材库（供 AI 参考调用）
# ────────────────────────────────────────

PSYCH_CONCEPTS = """
认知类：确认偏误、沉没成本谬误、达克效应、心理账户、锚定效应、
        过度泛化、灾难化思维、非黑即白思维、归因偏差、认知失调

情绪类：情绪颗粒度、情绪压抑与替代性爆发、情感麻木、
        习得性无助、情绪传染、愤怒背后的一次情绪理论

关系类：安全型/焦虑型/回避型依恋、投射性认同、
        共情疲劳、情感勒索、煤气灯效应、课题分离、
        边界侵犯、镜像神经元与共情

发展类：内在小孩、原生家庭的心理脚本、
        心理创伤的躯体化表现、复杂性创伤、
        修复性体验、重新养育自己

行为类：习惯回路（触发-行为-奖励）、拖延与完美主义的关系、
        自我效能感、正强化与负强化、行为激活疗法

积极类：心流状态、心理韧性的五要素、感恩练习的神经机制、
        意义感与幸福感的区别、自我决定理论（自主/胜任/联结）、
        成长型思维与固定型思维
"""


# ────────────────────────────────────────
# 内容生成
# ────────────────────────────────────────

def generate_content(date_str: str, weekday: int) -> tuple[str, str, str]:
    """
    使用 DeepSeek 生成今日心理知识点 + 故事（小红书版+公众号版）
    返回 (concept, xhs_content, gzh_content)
    """
    client = openai.OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

    prompt = f"""你是一位温暖、有深度的心理学科普作者，公众号名称是"丹爱科技与生活"。
你的读者主要是30-45岁的女性，有生活压力，想了解心理学但不喜欢学术感太重的内容。
你的写作风格：用日常生活场景解释心理学概念，有故事、有温度、有实用价值，像朋友在聊天。

今天是 {date_str}（{WEEKDAY_NAMES[weekday]}）
今日主题方向：{TOPIC_HINTS[weekday]}

可参考的心理学概念库：
{PSYCH_CONCEPTS}

【创作任务】
从今日主题方向中选定一个具体的心理学概念，然后生成小红书版和公众号版两篇文章。

每篇文章结构：
1. 用一句话解释这个心理学概念（去掉术语，说人话）
2. 写一个真实感强的故事（主角是普通妈妈/职场女性/日常场景），
   故事里自然体现这个概念的作用或危害
3. 给读者一个可以立刻用上的小方法或视角转变

**输出格式（严格遵守，不输出任何多余说明）：**

CONCEPT: <今日心理学概念名称>

===XHS_START===
【标题】（带情绪词或数字，吸引点击，不超过20字，不要出现"心理学"三个字）

📖 今日心理知识：
[用1-2句话解释这个概念，完全不用专业术语，像解释给朋友听]

🌿 一个故事：
[150-200字，真实场景，有具体细节，读者能对号入座]

💡 带走一句话：
[一句能让读者停下来想一想的金句或方法]

#心理学日常 #情绪管理 #[贴合本文的标签] #[贴合本文的标签] #丹爱科技与生活

🎨 AI绘图提示词：[一句中文，描述与本文情绪契合的温暖画面]
===XHS_END===

===GZH_START===
【标题】（有叙事感，引发好奇，不超过25字，不要出现"心理学"三个字）

📖 今日心理知识：[概念名称]
[用2-3句话解释这个概念，深入一点但仍然口语化，可以举一个最简单的例子]

---

🌿 故事
[350-500字，完整故事，有开头有转折有结局，主角有名字，场景具体，
 故事里自然呈现心理学概念的运作方式，不要直接说"这就是XX概念"，
 让读者自己感受到]

---

💡 实用建议
[3条，每条一句话，具体可操作，不是大道理]

---

💬 [一个引发读者共鸣、愿意留言的互动问题]

📩 私信关键词领取资料：「清单」边界自查清单｜「工具」AI效率工具清单｜「提示词」妈妈AI提示词工具包｜「地图」京郊安静角落地图｜「急救」情绪急救包
===GZH_END===

【语气自查】
✓ 故事里的主角有真实感，不是"某位女士"而是"小林"或"我朋友阿雅"
✓ 心理学概念解释完全没有术语，读者不需要任何背景知识
✓ 给的方法是今天就能用的，不是"多关爱自己"这种空话
✓ 整体像一个懂心理学的朋友在分享，不是在上课
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    # 解析概念名
    concept = ""
    for line in raw.splitlines():
        if line.startswith("CONCEPT:"):
            concept = line[len("CONCEPT:"):].strip()
            break

    # 解析小红书版
    xhs = ""
    if "===XHS_START===" in raw and "===XHS_END===" in raw:
        xhs = raw.split("===XHS_START===")[1].split("===XHS_END===")[0].strip()

    # 解析公众号版
    gzh = ""
    if "===GZH_START===" in raw:
        gzh_part = raw.split("===GZH_START===")[1]
        if "===GZH_END===" in gzh_part:
            gzh = gzh_part.split("===GZH_END===")[0].strip()
        else:
            gzh = gzh_part.strip()

    return concept, xhs, gzh


# ────────────────────────────────────────
# 微信推送（Server酱）
# ────────────────────────────────────────

def send_to_wechat(title: str, content: str) -> bool:
    """通过 Server酱 推送"""
    send_key = os.environ.get("SERVERCHAN_KEY", "")
    if not send_key:
        print(f"[推送] 未配置 SERVERCHAN_KEY")
        print(f"标题: {title}\n{content[:300]}...\n")
        return False
    try:
        resp = requests.post(
            f"https://sctapi.ftqq.com/{send_key}.send",
            data={"title": title, "desp": content},
            timeout=15,
        )
        result = resp.json()
        if result.get("code") == 0:
            print(f"[推送] 成功：{title}")
            return True
        else:
            print(f"[推送] 失败: {result}")
            return False
    except Exception as e:
        print(f"[推送] 异常: {e}")
        return False


# ────────────────────────────────────────
# 主流程
# ────────────────────────────────────────

def main():
    today    = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday  = today.weekday()
    month_day = today.strftime("%m/%d")

    print(f"\n{'='*45}")
    print(f"心理知识日更 Agent 启动 — {date_str}（{WEEKDAY_NAMES[weekday]}）")
    print(f"{'='*45}\n")

    print("正在生成今日心理知识内容...\n")
    concept, xhs, gzh = generate_content(date_str, weekday)
    print(f"今日概念：{concept}\n")

    # 推送小红书版
    xhs_body = f"> 📅 {date_str}（{WEEKDAY_NAMES[weekday]}）\n> 今日概念：{concept}\n\n---\n\n{xhs}"
    send_to_wechat(f"🧠 心理知识·小红书版 {month_day}", xhs_body)

    time.sleep(2)

    # 推送公众号版
    gzh_body = f"> 📅 {date_str}（{WEEKDAY_NAMES[weekday]}）\n> 今日概念：{concept}\n\n---\n\n{gzh}"
    send_to_wechat(f"🧠 心理知识·公众号版 {month_day}", gzh_body)

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
