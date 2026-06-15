#!/usr/bin/env python3
"""
个人品牌内容 Agent
- 角色：39岁顺义内向型妈妈，定位"心理边界+AI效率+山水疗愈"
- 每天生成小红书版 + 公众号版两篇文章草稿
- 通过 Server酱 分两条推送到微信
"""

import os
import time
from datetime import datetime

import openai
import requests


# ────────────────────────────────────────
# 按周几给今日主题方向提示
# ────────────────────────────────────────

TOPIC_HINTS = {
    0: "亲子心理边界（课题分离、愧疚感拆解）",
    1: "AI妈妈效率工具（遛娃攻略、菜谱生成、家长会发言稿、家务分配）",
    2: "个人成长（39岁重启、职场疗愈、第二曲线）—— 今天是周三，优先用'如果…会怎样'假设实验体裁",
    3: "京郊静修与内向者充电（独处角落、一日止语、山水感悟）",
    4: "亲子心理边界（发脾气后的修复、愤怒作为边界信号、'不'的练习）",
    5: "AI工具或个人成长自由组合，可以写一件本周真实发生的小事",
    6: "自由选题，最个人化的内容，写最近触动你的一个瞬间",
}

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


# ────────────────────────────────────────
# 内容生成
# ────────────────────────────────────────

def generate_content(date_str: str, weekday: int) -> tuple[str, str, str]:
    """
    使用 DeepSeek 生成今日小红书版+公众号版两篇文章
    返回 (topic, xhs_content, gzh_content)
    """
    client = openai.OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

    prompt = f"""你是以下角色，请完全进入角色来创作：

【角色设定】
39岁、居住在北京顺义的内向型妈妈。正在经营个人品牌，核心定位是"帮助妈妈用心理边界保护自己，用AI工具节省时间，用山水自然疗愈内心"。文字风格温暖、真诚、不端着，像在跟一个朋友聊天。

【真实素材库（可自由调用，让内容更真实）】
- 39岁顺义妈妈，有9岁儿子
- 曾被老板以绩效为由不发年终奖和股票，这段经历让我深刻理解边界的重要
- 有100万存款作为安全垫，正在探索新方向
- 核心主张：内疚不是爱，是越界；愤怒是边界被侵犯的信号
- 常用AI工具（Kimi、ChatGPT）解决生活问题
- 喜欢去京郊山里独处，正在收集安静角落

【今天的信息】
日期：{date_str}（{WEEKDAY_NAMES[weekday]}）
今日主题方向：{TOPIC_HINTS[weekday]}

【选题规则——从以下5种方法中选1种来确定今日具体选题】
1. 素材再组合：从素材库随机抽取1个心理学概念 + 1个生活场景 + 1个AI工具，组合成新选题
2. 问题反推：选一个妈妈常见烦恼（如对孩子发火、和伴侣争执、职场委屈），反向给出基于我理念的解法
3. 假设实验（周三优先）：用"如果我一周不对孩子说'快点'，会发生什么？"类体裁，写一个模拟实践报告
4. 金句解读：从金句库（"内疚不是爱，是越界"、"愤怒是边界被侵犯的信号"）选一句深度解读或案例
5. 自由创作：结合今日主题方向，写一个真实、有温度的故事或感悟

【任务】
选定今日具体选题，然后同时生成两篇文章——小红书版和公众号版。

**输出格式（严格遵守，不要输出任何多余说明文字）：**

TOPIC: <一句话说明今日具体选题>

===XHS_START===
【标题】（带数字或强烈情绪词，吸引人点击，不超过20字）

正文（200-350字，要有完整的故事感：先写一个真实场景或触动瞬间，再说自己的感受和转变，最后给读者一句能带走的话。有分点或emoji，温暖口语化）

#妈妈心理边界 #内向妈妈 #顺义妈妈 #[再加2个贴合本文的标签]

🎨 AI绘图提示词：[一句中文，描述与本文情绪契合的温暖画面，适合小红书配图风格，如"傍晚阳光下，一个女人坐在窗边喝茶，神情平静而笃定"]
===XHS_END===

===GZH_START===
【标题】（有叙事感，引发好奇或共鸣，不超过25字）

正文（300-800字，有叙事、有金句、有真实感）

---
💬 [一个引发读者共鸣、愿意留言的互动问题]
===GZH_END===

【语气自查——创作时保持】
✓ 像跟朋友说话，不是在讲课
✓ 用"我"开头分享真实感受
✓ 有一句能让读者停下来想一想的金句
✓ 避免说教和专业术语堆砌
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    # 解析 TOPIC
    topic = ""
    for line in raw.splitlines():
        if line.startswith("TOPIC:"):
            topic = line[len("TOPIC:"):].strip()
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
            gzh = gzh_part.strip()  # 没有结束标记也取内容

    return topic, xhs, gzh


# ────────────────────────────────────────
# 微信推送
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
    today   = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday  = today.weekday()  # 0=周一 … 6=周日
    month_day = today.strftime("%m/%d")

    print(f"\n{'='*45}")
    print(f"个人品牌内容 Agent 启动 — {date_str}（{WEEKDAY_NAMES[weekday]}）")
    print(f"{'='*45}\n")

    # 1. 生成内容
    print("正在生成今日内容...\n")
    topic, xhs, gzh = generate_content(date_str, weekday)
    print(f"今日选题：{topic}\n")

    # 2. 推送小红书版
    xhs_body = f"> 📅 {date_str}（{WEEKDAY_NAMES[weekday]}）\n> 今日选题：{topic}\n\n---\n\n{xhs}"
    send_to_wechat(f"📱 内容草稿·小红书版 {month_day}", xhs_body)

    time.sleep(2)  # 避免推送频率限制

    # 3. 推送公众号版
    gzh_body = f"> 📅 {date_str}（{WEEKDAY_NAMES[weekday]}）\n> 今日选题：{topic}\n\n---\n\n{gzh}"
    send_to_wechat(f"📖 内容草稿·公众号版 {month_day}", gzh_body)

    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
