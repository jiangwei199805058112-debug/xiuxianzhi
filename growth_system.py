"""根基、熟练度、博学度与融会贯通系统。"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List


MASTERY_FIELDS = [
    "cultivation_mastery",
    "combat_mastery",
    "alchemy_mastery",
    "herb_mastery",
    "spirit_field_mastery",
    "intel_mastery",
    "social_mastery",
    "theft_mastery",
    "demonic_mastery",
    "market_mastery",
]

MASTERY_NAMES = {
    "cultivation_mastery": "修炼熟练度",
    "combat_mastery": "斗法熟练度",
    "alchemy_mastery": "炼丹熟练度",
    "herb_mastery": "采药熟练度",
    "spirit_field_mastery": "灵植熟练度",
    "intel_mastery": "情报熟练度",
    "social_mastery": "人情熟练度",
    "theft_mastery": "盗术熟练度",
    "demonic_mastery": "魔道熟练度",
    "market_mastery": "坊市熟练度",
}


def _value(player: Any, attr: str) -> int:
    try:
        return int(getattr(player, attr, 0))
    except (TypeError, ValueError):
        return 0


def mastery_count_at_least(player: Any, threshold: int) -> int:
    return sum(1 for field in MASTERY_FIELDS if _value(player, field) >= threshold)


def mastery_total(player: Any) -> int:
    return sum(_value(player, field) for field in MASTERY_FIELDS)


def calculate_breadth(player: Any) -> int:
    count = 0
    for field in MASTERY_FIELDS:
        value = _value(player, field)
        if value >= 10:
            count += 1
        if value >= 25:
            count += 1
        if value >= 50:
            count += 1
        if value >= 80:
            count += 1
    return min(10, count // 2)


def _has_many_masteries(player: Any, threshold: int, count: int) -> bool:
    return mastery_count_at_least(player, threshold) >= count


def _insight_conditions() -> Dict[str, Callable[[Any], bool]]:
    return {
        "静水深流": lambda p: _value(p, "foundation") >= 40 and _value(p, "cultivation_mastery") >= 20,
        "法随心动": lambda p: _value(p, "cultivation_mastery") >= 20 and _value(p, "combat_mastery") >= 20,
        "药力归元": lambda p: _value(p, "cultivation_mastery") >= 20 and _value(p, "alchemy_mastery") >= 20,
        "药理通明": lambda p: _value(p, "alchemy_mastery") >= 20 and _value(p, "spirit_field_mastery") >= 15,
        "山野老手": lambda p: _value(p, "herb_mastery") >= 20 and _value(p, "speed") >= 10,
        "山路先知": lambda p: _value(p, "herb_mastery") >= 15 and _value(p, "intel_mastery") >= 15,
        "族中耳目": lambda p: _value(p, "social_mastery") >= 20 and _value(p, "intel_mastery") >= 20,
        "妙手无痕": lambda p: _value(p, "theft_mastery") >= 25 and _value(p, "intel_mastery") >= 15,
        "窥隙探囊": lambda p: _value(p, "theft_mastery") >= 35 and _value(p, "divine_sense") >= 8,
        "来去无踪": lambda p: _value(p, "theft_mastery") >= 25 and _value(p, "speed") >= 10,
        "正邪互参": lambda p: _value(p, "demonic_mastery") >= 20 and _value(p, "dao_heart") >= 12,
        "血战入骨": lambda p: _value(p, "demonic_mastery") >= 25 and _value(p, "combat_mastery") >= 20,
        "市井老道": lambda p: _value(p, "market_mastery") >= 20 and _value(p, "intel_mastery") >= 15,
        "百艺旁通": lambda p: _has_many_masteries(p, 15, 5),
        "万法互证": lambda p: _has_many_masteries(p, 25, 5)
        and _value(p, "foundation") >= 60
        and calculate_breadth(p) >= 5,
        "厚积薄发": lambda p: foundation_burst_ready(p),
    }


INSIGHT_DESCRIPTIONS = {
    "静水深流": "打坐收益小幅提高，心魔增长略降。",
    "法随心动": "法术训练收益提高，大比斗法台小幅加成。",
    "药力归元": "丹药吸收效率提高，服丹心魔略降。",
    "药理通明": "炼丹材料消耗小概率减少，炼丹失败惩罚略降。",
    "山野老手": "百药山受伤概率降低，低收益概率降低。",
    "山路先知": "百药山收益更稳定，稀有发现概率略升。",
    "族中耳目": "情报收益提高，大比情报加成小幅提高。",
    "妙手无痕": "盗术成功率小幅提高，失败暴露略降。",
    "窥隙探囊": "偷功法、偷情报、偷修为成功率提高。",
    "来去无踪": "强行脱身惩罚降低。",
    "正邪互参": "魔道心魔反噬略低，但业力不降低。",
    "血战入骨": "魔道斗法收益提高，但声望惩罚更明显。",
    "市井老道": "普通坊市交易更稳，打听行情成功率提高。",
    "百艺旁通": "所有熟练度获取小幅提高。",
    "万法互证": "所有熟练度获取提高，大比三关小幅综合加成。",
    "厚积薄发": "大比前满足根基与博学条件时触发一次综合爆发。",
}


def has_insight(player: Any, name: str) -> bool:
    return name in list(getattr(player, "unlocked_insights", []) or [])


def update_unlocked_insights(player: Any) -> List[str]:
    unlocked = [str(name) for name in list(getattr(player, "unlocked_insights", []) or []) if str(name)]
    new_names: List[str] = []
    conditions = _insight_conditions()
    for name in INSIGHT_DESCRIPTIONS:
        if name not in unlocked and conditions[name](player):
            unlocked.append(name)
            new_names.append(name)
    player.unlocked_insights = unlocked
    return new_names


def gain_mastery(player: Any, mastery_key: str, base_amount: int, foundation_gain: int = 0) -> str:
    lines: List[str] = []
    if foundation_gain:
        player.foundation += max(0, foundation_gain)
        lines.append(f"根基+{max(0, foundation_gain)}")
    if mastery_key and base_amount > 0:
        breadth = calculate_breadth(player)
        multiplier = 1.0 + min(0.30, breadth * 0.03)
        if has_insight(player, "百艺旁通"):
            multiplier += 0.05
        if has_insight(player, "万法互证"):
            multiplier += 0.08
        gain = max(1, int(round(base_amount * multiplier)))
        if _value(player, "foundation") >= 60 and random.random() < 0.12:
            gain += 1
        if _value(player, "foundation") >= 90 and random.random() < 0.08:
            gain += 1
        setattr(player, mastery_key, _value(player, mastery_key) + gain)
        lines.append(f"{MASTERY_NAMES.get(mastery_key, mastery_key)}+{gain}")
    player.clamp()
    new_names = update_unlocked_insights(player)
    player.clamp()
    if new_names:
        lines.append("解锁融会：" + "、".join(new_names))
    return "，".join(lines) + "。" if lines else ""


BREAKTHROUGH_INSIGHT_OPTIONS = {
    "1": "稳固根基",
    "2": "专注修炼",
    "3": "斗法磨砺",
    "4": "丹道体悟",
    "5": "山野求生",
    "6": "灵植亲和",
    "7": "情报先手",
    "8": "人情往来",
    "9": "旁门妙手",
    "10": "魔念入骨",
}


def breakthrough_insight_menu_text(player: Any) -> str:
    lines = [f"突破感悟：待选择 {max(0, _value(player, 'breakthrough_insight_pending'))} 次"]
    lines.extend(
        [
            "1. 稳固根基：根基+8，气血上限+6，防御+1，道心+1",
            "2. 专注修炼：修为+3，修炼速度+1，修炼熟练度+5",
            "3. 斗法磨砺：攻击+2，斗法经验+2，斗法熟练度+5",
            "4. 丹道体悟：炼丹熟练度+8，悟性+1，心魔-1",
            "5. 山野求生：采药熟练度+6，体魄+1，身法+1",
            "6. 灵植亲和：灵植熟练度+8，普通灵草+2，根基+2",
            "7. 情报先手：情报熟练度+8，情报值+2，神识+1",
            "8. 人情往来：人情熟练度+8，魅力+1，正道声望+2，随机族人好感+2",
            "9. 旁门妙手：盗术熟练度+8，盗术+4，身法+1，暴露度+1",
            "10. 魔念入骨：魔道熟练度+8，攻击+3，修为+3，业力+2，心魔+1",
            "0. 返回",
        ]
    )
    return "\n".join(lines)


def apply_breakthrough_insight(player: Any, choice: str) -> str:
    if _value(player, "breakthrough_insight_pending") <= 0:
        update_unlocked_insights(player)
        return "你暂时没有待选择的突破感悟。"
    label = BREAKTHROUGH_INSIGHT_OPTIONS.get(choice)
    if not label:
        return "你暂时没有选择突破感悟。"

    if choice == "1":
        player.foundation += 8
        player.max_hp += 6
        player.hp += 6
        player.defense += 1
        player.dao_heart += 1
    elif choice == "2":
        player.cultivation += 3
        player.cultivation_speed += 1
        player.cultivation_mastery += 5
    elif choice == "3":
        player.attack += 2
        player.combat_exp += 2
        player.combat_mastery += 5
    elif choice == "4":
        player.alchemy_mastery += 8
        player.comprehension += 1
        player.heart_demon -= 1
    elif choice == "5":
        player.herb_mastery += 6
        player.physique += 1
        player.speed += 1
    elif choice == "6":
        player.spirit_field_mastery += 8
        player.herbs += 2
        player.foundation += 2
    elif choice == "7":
        player.intel_mastery += 8
        player.intelligence += 2
        player.divine_sense += 1
    elif choice == "8":
        player.social_mastery += 8
        player.charm += 1
        player.righteous_reputation += 2
        if getattr(player, "npc_affection", None):
            npc = random.choice(list(player.npc_affection))
            player.npc_affection[npc] += 2
    elif choice == "9":
        player.theft_mastery += 8
        player.theft_skill += 4
        player.speed += 1
        player.exposure += 1
    elif choice == "10":
        player.demonic_mastery += 8
        player.attack += 3
        player.cultivation += 3
        player.karma += 2
        player.heart_demon += 1

    player.breakthrough_insight_pending -= 1
    player.clamp()
    new_names = update_unlocked_insights(player)
    player.clamp()
    suffix = "解锁融会：" + "、".join(new_names) + "。" if new_names else ""
    return f"你选择突破感悟：{label}。{suffix}"


def growth_status_text(player: Any) -> str:
    mastery_text = "｜".join(
        f"{MASTERY_NAMES[field].replace('熟练度', '')}{_value(player, field)}" for field in MASTERY_FIELDS
    )
    insights = list(getattr(player, "unlocked_insights", []) or [])
    insight_text = "、".join(str(name) for name in insights) if insights else "无"
    return (
        "根基融会："
        f"根基{_value(player, 'foundation')}｜博学度{calculate_breadth(player)}｜"
        f"熟练总和{mastery_total(player)}｜突破{_value(player, 'breakthrough_count')}次｜"
        f"待选感悟{_value(player, 'breakthrough_insight_pending')}｜"
        f"厚积薄发{'已触发' if getattr(player, 'foundation_burst_triggered', False) else '未触发'}\n"
        f"熟练度：{mastery_text}\n"
        f"融会状态：{len(insights)}项｜{insight_text}"
    )


def foundation_burst_ready(player: Any) -> bool:
    return (
        _value(player, "foundation") >= 55
        and calculate_breadth(player) >= 4
        and mastery_count_at_least(player, 15) >= 5
    )


def foundation_burst_bonus(player: Any) -> Dict[str, object]:
    if getattr(player, "foundation_burst_triggered", False) or not foundation_burst_ready(player):
        return {"triggered": False, "mind": 0, "trial": 0, "combat": 0, "total": 0, "text": ""}

    resource_strain = _value(player, "cultivation_pressure") > 0 or _value(player, "spirit_stones") <= 1
    total = 0 if resource_strain else 1
    risk = (
        _value(player, "karma") >= 35
        or _value(player, "demonic_qi") >= 45
        or _value(player, "exposure") >= 60
        or _value(player, "tracking_marks") >= 2
        or _value(player, "enemy_count") >= 4
    )
    if risk:
        total = max(0, total - 1)
    parts = {"mind": 0, "trial": 0, "combat": 0}
    for _ in range(total):
        parts[random.choice(["mind", "trial", "combat"])] += 1
    player.foundation_burst_triggered = True
    text = (
        "一年修行将尽，你回望所学。\n"
        "采药知山势，炼丹知药性，斗法知灵机，情报知人心。\n"
        "诸般技艺原本散乱，此刻却似一条暗线，在你心中缓缓贯通。\n"
        "触发：厚积薄发。"
    )
    if risk:
        text += "只是业力、暴露或旧怨拖住部分灵机，这点贯通来得更浅。"
    if resource_strain:
        text += "只是耗材与人情未足，灵机只作体悟，难以化成大比加分。"
    return {"triggered": True, "mind": parts["mind"], "trial": parts["trial"], "combat": parts["combat"], "total": total, "text": text}


def growth_tournament_adjustments(player: Any) -> Dict[str, object]:
    notes: List[str] = []
    mind = 1 if _value(player, "foundation") >= 70 else 0
    trial = 0
    combat = 0
    breadth_bonus = 1 if calculate_breadth(player) >= 6 else 0
    mind += breadth_bonus
    trial += breadth_bonus
    combat += breadth_bonus
    if _value(player, "foundation") >= 40:
        notes.append("根基深厚：测灵问心更稳。")
    if breadth_bonus:
        notes.append("博学旁通：三关发挥更稳定。")

    insight_bonuses = [
        ("法随心动", "combat"),
        ("药力归元", "mind"),
        ("药理通明", "trial"),
        ("山野老手", "trial"),
        ("山路先知", "trial"),
        ("族中耳目", "mind"),
        ("市井老道", "trial"),
    ]
    for name, section in insight_bonuses:
        if has_insight(player, name):
            if section == "mind":
                mind += 1
            elif section == "trial":
                trial += 1
            else:
                combat += 1
            notes.append(f"{name}：{INSIGHT_DESCRIPTIONS[name]}")
    if has_insight(player, "万法互证"):
        mind += 1
        trial += 1
        combat += 1
        notes.append("万法互证：诸般技艺互相印证，三关各有小成。")

    mind = min(3, mind)
    trial = min(3, trial)
    combat = min(3, combat)
    return {"mind": mind, "trial": trial, "combat": combat, "total": mind + trial + combat, "notes": notes}
