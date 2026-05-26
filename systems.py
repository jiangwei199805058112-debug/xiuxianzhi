"""第一章行动系统。"""

from __future__ import annotations

import random
from typing import Callable, Dict, List

from data import ACTION_NAMES, ATTRIBUTE_NAMES, MONTHLY_EVENTS, NPCS
from player import Player


def action_menu_text() -> str:
    lines = ["可选行动："]
    for key, name in ACTION_NAMES.items():
        lines.append(f"{key}. {name}")
    lines.append("S. 存档")
    lines.append("L. 读档")
    lines.append("Q. 退出")
    return "\n".join(lines)


def _roll(low: int, high: int) -> int:
    return random.randint(low, high)


def _choose_npc(prompt: str) -> str:
    names = list(NPCS)
    print(prompt)
    for index, name in enumerate(names, start=1):
        print(f"{index}. {name}：{NPCS[name]}")
    choice = input("请选择对象：").strip()
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(names):
            return names[index - 1]
    print("你一时拿不定主意，最后去见了沈清婉。")
    return names[0]


def action_cultivate(player: Player) -> str:
    gain = _roll(2, 4) + player.root_growth
    used_pill = False
    if player.pills > 0:
        player.pills -= 1
        gain += _roll(2, 4)
        used_pill = True
    player.cultivation += gain
    player.heart_demon += _roll(0, 2)
    player.exposure += 1 if gain >= 6 else 0
    player.clamp()
    pill_text = "你服下一枚丹药，药力推着灵气贯通小周天。" if used_pill else "你没有丹药辅佐，只靠吐纳慢慢打磨。"
    return f"你闭门修炼一旬。{pill_text}修为提升 {gain}。"


def action_martial(player: Player) -> str:
    combat_gain = _roll(2, 4)
    physique_gain = _roll(1, 2)
    player.combat_exp += combat_gain
    player.physique += physique_gain
    player.contribution += 1
    player.heart_demon = max(0, player.heart_demon - 1)
    if player.demonic_qi > 25:
        player.exposure += 1
    player.clamp()
    return f"你在演武场与同辈拆招，斗法提升 {combat_gain}，体魄提升 {physique_gain}。"


def action_gather_herbs(player: Player) -> str:
    herb_gain = _roll(2, 5)
    stone_gain = _roll(0, 2)
    player.herbs += herb_gain
    player.spirit_stones += stone_gain
    player.physique += 1
    if random.random() < 0.25:
        player.exposure += 2
        extra = "回程时你被巡山族人问了几句，暴露度略升。"
    else:
        extra = "你避开人多的山道，顺利回到旁支小院。"
    player.clamp()
    return f"你入山采药，得到灵草 {herb_gain}，灵石 {stone_gain}。{extra}"


def action_spirit_field(player: Player) -> str:
    contribution_gain = _roll(2, 4)
    herb_gain = _roll(1, 3)
    player.contribution += contribution_gain
    player.herbs += herb_gain
    player.righteous_reputation += 1
    player.npc_affection["沈素秋"] += 2
    player.clamp()
    return f"你照看家族灵田，得灵草 {herb_gain}，家族贡献增加 {contribution_gain}。沈素秋对你印象稍好。"


def action_jade_bottle(player: Player) -> str:
    if player.herbs <= 0:
        player.herbs += 1
        player.exposure += 2
        player.clamp()
        return "你没有可催熟的灵草，只能用古玉瓶凝出一株幼苗。灵草 +1，暴露度 +2。"

    base = _roll(3, 6)
    player.herbs += base
    player.exposure += _roll(4, 7)
    player.heart_demon += 1
    if player.exposure >= 60:
        player.righteous_reputation -= 1
        warning = "近期灵草来路太齐整，已经有人暗中留意。"
    else:
        warning = "你把催熟后的灵草分散藏好，没有立刻引人怀疑。"
    player.clamp()
    return f"你以古玉瓶催熟灵草，灵草增加 {base}。{warning}"


def action_refine_pills(player: Player) -> str:
    if player.herbs >= 3 and player.spirit_stones >= 1:
        player.herbs -= 3
        player.spirit_stones -= 1
        made = _roll(2, 4)
        player.pills += made
        player.comprehension += 1
        player.exposure += 1
        player.clamp()
        return f"你借小炉炼制粗丹，消耗 3 株灵草和 1 枚灵石，得到丹药 {made}。"

    player.contribution += 1
    player.npc_affection["沈清婉"] += 1
    player.clamp()
    return "材料不足，你改去丹房帮忙分拣药材，家族贡献 +1，沈清婉好感 +1。"


def action_family_work(player: Player) -> str:
    contribution_gain = _roll(3, 5)
    stone_gain = _roll(1, 3)
    player.contribution += contribution_gain
    player.spirit_stones += stone_gain
    player.righteous_reputation += 2
    player.heart_demon = max(0, player.heart_demon - 1)
    player.clamp()
    return f"你接下家族杂务，跑腿、抄册、守夜皆做，贡献 +{contribution_gain}，灵石 +{stone_gain}。"


def action_visit_npc(player: Player) -> str:
    npc = _choose_npc("你准备拜访哪位族人？")
    affection_gain = _roll(3, 6)
    player.npc_affection[npc] += affection_gain
    if npc == "沈怀远":
        player.combat_exp += 1
    elif npc == "沈清婉":
        player.comprehension += 1
    elif npc == "沈素秋":
        player.contribution += 1
    elif npc == "沈砚":
        player.heart_demon += 1
        player.combat_exp += 1
    player.clamp()
    return f"你带着合适的由头拜访{npc}，好感提升 {affection_gain}。"


def action_love_lock(player: Player) -> str:
    npc = _choose_npc("情意锁低阶残印只能轻轻牵引情绪，你要影响谁？")
    affection_gain = _roll(4, 8) + player.love_lock_level
    player.npc_affection[npc] += affection_gain
    player.heart_demon += _roll(1, 3)
    player.karma += 1
    player.exposure += 1
    player.clamp()
    return (
        f"你催动情意锁残印，只借一点熟悉感牵引{npc}。"
        f"{npc}好感提升 {affection_gain}，但心魔与业力也留下细痕。"
    )


def action_soul_banner(player: Player) -> str:
    player.soul_banner_awakened = True
    refine_gain = _roll(1, 2)
    combat_gain = _roll(2, 4)
    cultivation_gain = _roll(1, 3)
    player.souls_refined += refine_gain
    player.combat_exp += combat_gain
    player.cultivation += cultivation_gain
    player.demonic_qi += _roll(5, 9)
    player.karma += _roll(3, 6)
    player.heart_demon += _roll(2, 5)
    player.righteous_reputation -= 2
    player.exposure += _roll(2, 4)
    player.clamp()
    return (
        "你在荒坟外以残幡收拢游魂，只敢炼化最浅的一缕阴气。"
        f"修为 +{cultivation_gain}，斗法 +{combat_gain}，炼魂次数 +{refine_gain}。"
    )


def action_meditate(player: Player) -> str:
    heart_drop = _roll(3, 6)
    demonic_drop = _roll(1, 3)
    exposure_drop = _roll(1, 3)
    player.heart_demon -= heart_drop
    player.demonic_qi -= demonic_drop
    player.exposure -= exposure_drop
    player.righteous_reputation += 1
    player.clamp()
    return f"你焚香静坐，压下杂念。心魔 -{heart_drop}，魔气 -{demonic_drop}，暴露度 -{exposure_drop}。"


ACTION_HANDLERS: Dict[str, Callable[[Player], str]] = {
    "1": action_cultivate,
    "2": action_martial,
    "3": action_gather_herbs,
    "4": action_spirit_field,
    "5": action_jade_bottle,
    "6": action_refine_pills,
    "7": action_family_work,
    "8": action_visit_npc,
    "9": action_love_lock,
    "10": action_soul_banner,
    "11": action_meditate,
}


def perform_action(player: Player, choice: str) -> str:
    handler = ACTION_HANDLERS.get(choice)
    if handler is None:
        return "无效行动。"
    result = handler(player)
    player.advance_action()
    return result


def monthly_event(player: Player) -> str:
    event = random.choice(MONTHLY_EVENTS)
    for attr, value in event["effects"].items():
        setattr(player, attr, getattr(player, attr) + int(value))
    player.clamp()
    effects_text = "，".join(
        f"{ATTRIBUTE_NAMES.get(key, key)}{value:+d}" for key, value in event["effects"].items()
    )
    return f"月末事件：{event['title']}\n{event['text']}\n影响：{effects_text}"


def risk_summary(player: Player) -> List[str]:
    warnings: List[str] = []
    if player.exposure >= 70:
        warnings.append("古玉瓶的异常已接近被族中察觉。")
    if player.heart_demon >= 70:
        warnings.append("心魔深重，可能拖累大比心性评分。")
    if player.demonic_qi >= 50:
        warnings.append("魔气缠身，正道族老或会起疑。")
    if player.karma >= 50:
        warnings.append("业力过重，隐藏线结局风险升高。")
    return warnings
