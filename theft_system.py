"""轻量盗术系统。"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from cultivation_assets import equipment_bonus, grant_equipment


THEFT_TYPES: Dict[str, Dict[str, object]] = {
    "basic": {
        "name": "顺手牵羊",
        "min_skill": 0,
        "difficulty": 18,
        "cap": (15, 90),
        "compensation": 3,
        "target_level": 1,
        "exp_success": 4,
        "exp_fail": 2,
    },
    "stall": {
        "name": "夜探摊位",
        "min_skill": 10,
        "difficulty": 25,
        "cap": (15, 90),
        "compensation": 5,
        "target_level": 2,
        "exp_success": 6,
        "exp_fail": 3,
    },
    "intel": {
        "name": "盗取情报",
        "min_skill": 10,
        "difficulty": 26,
        "cap": (15, 90),
        "compensation": 6,
        "target_level": 2,
        "exp_success": 6,
        "exp_fail": 3,
        "tracking_sensitive": True,
    },
    "manual": {
        "name": "窃取功法",
        "min_skill": 25,
        "difficulty": 44,
        "cap": (5, 75),
        "compensation": 10,
        "target_level": 3,
        "exp_success": 8,
        "exp_fail": 4,
    },
    "cultivation": {
        "name": "窃取修为",
        "min_skill": 45,
        "difficulty": 58,
        "cap": (5, 75),
        "compensation": 14,
        "target_level": 4,
        "exp_success": 9,
        "exp_fail": 5,
        "high_tier": True,
    },
    "luck": {
        "name": "窃取气运",
        "min_skill": 65,
        "difficulty": 72,
        "cap": (3, 65),
        "compensation": 24,
        "target_level": 5,
        "exp_success": 10,
        "exp_fail": 6,
        "high_tier": True,
    },
    "opportunity": {
        "name": "截胡机缘",
        "min_skill": 65,
        "difficulty": 74,
        "cap": (3, 65),
        "compensation": 26,
        "target_level": 5,
        "exp_success": 10,
        "exp_fail": 6,
        "high_tier": True,
    },
    "fate": {
        "name": "窃取因果",
        "min_skill": 80,
        "difficulty": 86,
        "cap": (2, 55),
        "compensation": 34,
        "target_level": 6,
        "exp_success": 12,
        "exp_fail": 7,
        "high_tier": True,
    },
    "lifespan": {
        "name": "窃取寿元",
        "min_skill": 80,
        "difficulty": 88,
        "cap": (2, 55),
        "compensation": 36,
        "target_level": 6,
        "exp_success": 12,
        "exp_fail": 7,
        "high_tier": True,
    },
    "inheritance": {
        "name": "窃取 NPC 传承",
        "min_skill": 95,
        "difficulty": 104,
        "cap": (1, 45),
        "compensation": 55,
        "target_level": 7,
        "exp_success": 16,
        "exp_fail": 9,
        "high_tier": True,
    },
}

THEFT_MENU_ITEMS: List[tuple[str, str, str]] = [
    ("2", "顺手牵羊", "basic"),
    ("3", "夜探摊位", "stall"),
    ("4", "盗取情报", "intel"),
    ("5", "窃取功法", "manual"),
    ("6", "窃取修为", "cultivation"),
    ("7", "窃取气运", "luck"),
    ("8", "截胡机缘", "opportunity"),
    ("9", "窃取因果", "fate"),
    ("10", "窃取寿元", "lifespan"),
    ("11", "窃取 NPC 传承", "inheritance"),
]

THEFT_TYPE_BY_MENU = {key: theft_type for key, _, theft_type in THEFT_MENU_ITEMS}
FATE_SHIELD_FLAG = "stolen_fate_shield"


def _get_int(player: Any, attr: str, default: int = 0) -> int:
    try:
        return int(getattr(player, attr, default))
    except (TypeError, ValueError):
        return default


def _add_exposure(player: Any, amount: int) -> None:
    if amount <= 0:
        return
    player.exposure += amount
    player.theft_exposure_gain += amount


def _add_karma(player: Any, amount: int) -> None:
    if amount <= 0:
        return
    player.karma += amount
    player.theft_karma_gain += amount


def _gain_theft_exp(player: Any, amount: int) -> None:
    before = _get_int(player, "theft_exp") // 12
    player.theft_exp += max(0, amount)
    after = _get_int(player, "theft_exp") // 12
    if after > before:
        player.theft_skill += after - before


def train_theft(player: Any) -> str:
    exp_gain = random.randint(8, 12) + max(0, _get_int(player, "divine_sense")) // 4
    skill_gain = random.randint(3, 5) + max(0, _get_int(player, "speed")) // 8
    if _get_int(player, "theft_skill") >= 70:
        skill_gain = max(1, skill_gain - 2)
    player.theft_skill += skill_gain
    _gain_theft_exp(player, exp_gain)
    speed_gain = 1 if random.random() < 0.55 else 0
    sense_gain = 1 if random.random() < 0.45 else 0
    combat_gain = 1 if random.random() < 0.40 else 0
    player.speed += speed_gain
    player.divine_sense += sense_gain
    player.combat_exp += combat_gain
    player.mp = max(0, player.mp - random.randint(0, 2))
    player.exposure += 1 if random.random() < 0.25 else 0
    player.clamp()
    growth_text = []
    if speed_gain:
        growth_text.append("身法+1")
    if sense_gain:
        growth_text.append("神识+1")
    if combat_gain:
        growth_text.append("斗法经验+1")
    detail = "，" + "，".join(growth_text) if growth_text else ""
    return (
        f"你练习换指、藏息与走位，盗术经验+{exp_gain}，盗术+{skill_gain}{detail}。"
        "此法毕竟偏门，练得越深越需谨慎。"
    )


def calculate_theft_success_rate(player: Any, target_type: str, theft_type: str) -> float:
    del target_type
    cfg = THEFT_TYPES.get(theft_type, THEFT_TYPES["basic"])
    low, high = cfg["cap"]  # type: ignore[misc]
    skill = _get_int(player, "theft_skill")
    stealth_bonus = (
        max(0, equipment_bonus(player, "speed")) * 2
        + max(0, equipment_bonus(player, "divine_sense")) * 2
        + max(0, equipment_bonus(player, "dao_heart"))
    )
    realm_advantage = (_get_int(player, "realm_level", 1) - int(cfg.get("target_level", 1))) * 3
    rate = (
        62
        + skill * 1.05
        + _get_int(player, "speed") * 0.45
        + _get_int(player, "divine_sense") * 0.55
        + min(8, _get_int(player, "intelligence") // 3)
        + stealth_bonus
        + realm_advantage
        - int(cfg["difficulty"])
        - _get_int(player, "exposure") * 0.12
        - _get_int(player, "enemy_count") * 1.8
        - max(0, -_get_int(player, "reputation")) * 0.15
    )
    if cfg.get("high_tier"):
        rate -= _get_int(player, "karma") * 0.16
    if cfg.get("tracking_sensitive"):
        rate -= _get_int(player, "tracking_marks") * 4.0
    if theft_type == "inheritance" and _get_int(player, "stolen_inheritance_count") > 0:
        rate = 0
    return max(float(low), min(float(high), rate))


def _requirement_text(player: Any, theft_type: str) -> str:
    cfg = THEFT_TYPES[theft_type]
    required = int(cfg["min_skill"])
    current = _get_int(player, "theft_skill")
    if current >= required:
        return ""
    return f"{cfg['name']}至少需要盗术{required}，你当前盗术{current}，贸然下手只会露馅。"


def _success_common(player: Any, theft_type: str) -> None:
    cfg = THEFT_TYPES[theft_type]
    player.theft_successes += 1
    _gain_theft_exp(player, int(cfg.get("exp_success", 4)))


def _apply_success_effect(player: Any, theft_type: str) -> str:
    if theft_type == "basic":
        stones = random.randint(3, 7)
        herbs = random.randint(1, 3)
        player.spirit_stones += stones
        player.herbs += herbs
        if random.random() < 0.28:
            _add_exposure(player, 1)
        return f"你趁人不备顺走些零碎，灵石+{stones}，普通灵草+{herbs}。"

    if theft_type == "stall":
        roll = random.random()
        _add_exposure(player, random.randint(1, 2))
        if roll < 0.35:
            player.pills += 1
            return "你夜探摊位，摸走一只未封口的小瓷瓶，丹药+1。"
        if roll < 0.70:
            if random.random() < 0.5:
                player.talisman_fire += 1
                return "你夜探摊位，得火弹符+1。"
            player.talisman_guard += 1
            return "你夜探摊位，得护身符+1。"
        item_name = grant_equipment(player, random.choice(["cloth_boots", "calm_charm", "iron_sword"]))
        return f"你夜探摊位，翻得一件旧装备：{item_name}。" if item_name else "你夜探摊位，得些可用杂物。"

    if theft_type == "intel":
        intel = random.randint(2, 4)
        player.intelligence += intel
        player.explore_intel_bonus += 1 if random.random() < 0.45 else 0
        if _get_int(player, "theft_skill") >= 25 and random.random() < 0.35:
            player.black_market_clue += 1
            player.heishui_tournament_bonuses["trial"] = int(player.heishui_tournament_bonuses.get("trial", 0)) + 1
            return f"你盗来一份夹着黑水暗线的情报，情报值+{intel}，黑市线索+1。"
        section = random.choice(["mind", "trial", "combat"])
        player.heishui_tournament_bonuses[section] = int(player.heishui_tournament_bonuses.get(section, 0)) + 1
        return f"你盗来族中大比小抄，情报值+{intel}，对应试炼略有准备。"

    if theft_type == "manual":
        fragments = 1 + (1 if random.random() < 0.18 else 0)
        player.stolen_manual_fragments += fragments
        player.comprehension += 1 if random.random() < 0.35 else 0
        player.gain_cultivation_progress(random.randint(8, 14))
        if player.stolen_manual_fragments % 3 == 0:
            player.gain_cultivation_progress(random.randint(4, 7))
            player.mp += 1
        if _get_int(player, "theft_skill") >= 45 and random.random() < 0.12:
            player.combat_exp += 2
            player.attack += 1
            return f"你从旧匣里拓下一门低阶完整功法，功法残页+{fragments}，斗法经验+2，攻击+1。"
        return f"你拓下几页残缺功法，功法残页+{fragments}。"

    if theft_type == "cultivation":
        progress = random.randint(8, 14)
        player.stolen_cultivation_count += 1
        player.gain_cultivation_progress(progress)
        player.cultivation += random.randint(1, 3)
        _add_exposure(player, random.randint(4, 7))
        _add_karma(player, random.randint(5, 8))
        player.hp -= random.randint(1, 4)
        return f"你以旁门秘手牵引他人气机，修炼进度+{progress}，业力与暴露随之上涨。"

    if theft_type == "luck":
        player.stolen_luck_count += 1
        player.luck += 1 + (1 if random.random() < 0.18 else 0)
        _add_exposure(player, random.randint(3, 5))
        _add_karma(player, random.randint(4, 7))
        return "你截下一缕浮动气运，短期行事似乎顺了些，气运+1。"

    if theft_type == "opportunity":
        player.stolen_opportunity_count += 1
        player.enemy_count += 1
        player.reputation -= 1
        _add_exposure(player, random.randint(4, 7))
        _add_karma(player, random.randint(3, 6))
        reward = random.choice(["aged_herbs_10", "pills", "equipment", "intel"])
        if reward == "aged_herbs_10":
            player.aged_herbs_10 += 1
            return "你半途截胡一桩小机缘，十年份灵草+1，但原主隐约记住了你。"
        if reward == "pills":
            player.pills += 2
            return "你半途截胡一桩小机缘，丹药+2，但原主隐约记住了你。"
        if reward == "intel":
            player.intelligence += 4
            return "你半途截胡一桩小机缘，情报值+4，但原主隐约记住了你。"
        item_name = grant_equipment(player, random.choice(["greenwood_sword", "sense_charm", "quiet_robe"]))
        return f"你半途截胡一桩小机缘，得{item_name}，但原主隐约记住了你。"

    if theft_type == "fate":
        player.stolen_fate_count += 1
        if FATE_SHIELD_FLAG not in player.market_flags:
            player.market_flags.append(FATE_SHIELD_FLAG)
        player.dao_heart += 1
        _add_exposure(player, random.randint(5, 8))
        _add_karma(player, random.randint(8, 12))
        return "你强行移来一段微弱因果，似可替你挡一次小祸，道心+1，但因果债已缠身。"

    if theft_type == "lifespan":
        player.stolen_lifespan_count += 1
        hp_gain = random.randint(3, 5)
        player.max_hp += hp_gain
        player.hp += hp_gain
        player.heart_demon += random.randint(2, 4)
        _add_exposure(player, random.randint(7, 10))
        _add_karma(player, random.randint(12, 16))
        return f"你盗来一线寿元，气血上限+{hp_gain}，但阴冷业力缠上经脉。"

    if theft_type == "inheritance":
        player.stolen_inheritance_count += 1
        player.stolen_manual_fragments += 3
        player.comprehension += 2
        player.divine_sense += 2
        player.mp += 5
        player.attack += 2
        player.enemy_count += 2
        player.reputation -= 5
        _add_exposure(player, random.randint(12, 18))
        _add_karma(player, random.randint(16, 24))
        item_name = grant_equipment(player, random.choice(["greenwood_sword", "sense_charm"]))
        equipment_text = f"，并夺得{item_name}" if item_name else ""
        return f"你冒险窃走一份 NPC 传承，功法残页+3，悟性+2，神识+2，攻击+2{equipment_text}。"

    return "你下手得逞，却只摸到些无关紧要的东西。"


def _apply_failure_backlash(player: Any, theft_type: str) -> str:
    if theft_type == "cultivation":
        loss = random.randint(3, 7)
        player.cultivation_progress = max(0, player.cultivation_progress - loss)
        player.mp = max(0, player.mp - random.randint(2, 5))
        _add_karma(player, random.randint(2, 4))
        return f"偷修为时气机反噬，修炼进度-{loss}，灵力受损。"
    if theft_type in {"luck", "opportunity"}:
        _add_karma(player, random.randint(2, 4))
        player.luck = max(0, player.luck - (1 if random.random() < 0.30 else 0))
        return "你触到不属于自己的气数，心头一寒。"
    if theft_type == "fate":
        _add_karma(player, random.randint(5, 8))
        player.heart_demon += random.randint(1, 3)
        return "因果线猛然回卷，心魔暗涨。"
    if theft_type == "lifespan":
        _add_karma(player, random.randint(6, 10))
        player.hp = max(0, player.hp - random.randint(4, 8))
        return "寿元阴债反噬，气血骤降。"
    if theft_type == "inheritance":
        _add_exposure(player, random.randint(8, 12))
        _add_karma(player, random.randint(8, 14))
        player.hp = max(0, player.hp - random.randint(8, 14))
        player.enemy_count += 1
        return "传承禁制反震，你险些当场暴露，气血大损。"
    return "失主似有所觉，你只得收手。"


def attempt_theft(player: Any, theft_type: str) -> Dict[str, object]:
    if theft_type not in THEFT_TYPES:
        return {"success": False, "needs_resolution": False, "text": "你一时不知该偷什么。"}
    requirement = _requirement_text(player, theft_type)
    if requirement:
        return {"success": False, "needs_resolution": False, "text": requirement}

    cfg = THEFT_TYPES[theft_type]
    player.theft_attempts += 1
    rate = calculate_theft_success_rate(player, "", theft_type)
    if random.random() * 100 <= rate:
        _success_common(player, theft_type)
        text = _apply_success_effect(player, theft_type)
        player.clamp()
        return {
            "success": True,
            "needs_resolution": False,
            "rate": rate,
            "text": f"{cfg['name']}成功（成功率约{rate:.0f}%）。{text}",
        }

    player.theft_failures += 1
    _gain_theft_exp(player, int(cfg.get("exp_fail", 2)))
    _add_exposure(player, random.randint(0, 2))
    backlash = _apply_failure_backlash(player, theft_type)
    player.clamp()
    return {
        "success": False,
        "needs_resolution": True,
        "rate": rate,
        "text": f"{cfg['name']}失败（成功率约{rate:.0f}%）。{backlash}",
    }


def resolve_theft_failure(player: Any, theft_type: str, choice: str) -> str:
    cfg = THEFT_TYPES.get(theft_type, THEFT_TYPES["basic"])
    base_cost = int(cfg.get("compensation", 5))
    high_tier = bool(cfg.get("high_tier"))
    if choice == "1":
        cost = base_cost + _get_int(player, "enemy_count")
        paid = min(cost, _get_int(player, "spirit_stones"))
        player.spirit_stones -= paid
        player.theft_compensations += 1
        _add_exposure(player, random.randint(0, 2))
        if paid < cost:
            player.reputation -= 1
            player.enemy_count += 1 if random.random() < 0.18 else 0
            result = f"你赔了{paid}枚灵石仍不够数，只勉强压下风波。"
        else:
            player.reputation -= 1 if high_tier and random.random() < 0.45 else 0
            result = f"你赔出{paid}枚灵石，将事端暂时按下。"
    elif choice == "2":
        player.theft_refusals += 1
        player.reputation -= 2 + (1 if high_tier else 0)
        player.enemy_count += 1
        _add_exposure(player, random.randint(3, 5))
        target = random.choice(list(player.npc_affection))
        player.npc_affection[target] -= random.randint(2, 5)
        result = "你硬说此事与自己无关，省下赔偿，却让旁人记恨。"
    else:
        player.theft_escape_count += 1
        player.reputation -= 3 + (2 if high_tier else 0)
        player.enemy_count += 1 + (1 if high_tier and random.random() < 0.45 else 0)
        _add_exposure(player, random.randint(6, 11))
        _add_karma(player, random.randint(3, 7) + (3 if high_tier else 0))
        player.tracking_marks += 1 if random.random() < (0.24 if high_tier else 0.10) else 0
        player.hp = max(0, player.hp - random.randint(2, 8))
        _gain_theft_exp(player, 2)
        result = "你强行脱身，虽逃过当场追问，却留下更重痕迹。"
    player.clamp()
    return result


def resolve_monthly_theft_event(player: Any) -> str:
    if _get_int(player, "theft_attempts") <= 0:
        return ""
    risk = (
        _get_int(player, "theft_failures") * 2
        + _get_int(player, "enemy_count") * 5
        + max(0, -_get_int(player, "reputation")) * 2
        + _get_int(player, "exposure") // 12
        + _get_int(player, "karma") // 10
        + _get_int(player, "stolen_luck_count") * 2
        + _get_int(player, "stolen_fate_count") * 4
        + _get_int(player, "stolen_lifespan_count") * 5
        + _get_int(player, "stolen_inheritance_count") * 8
    )
    chance = min(42, 3 + risk)
    if random.randint(1, 100) > chance:
        return ""

    if FATE_SHIELD_FLAG in player.market_flags and random.random() < 0.45:
        player.market_flags.remove(FATE_SHIELD_FLAG)
        _add_karma(player, 2)
        player.clamp()
        return "盗术反噬：偷来的因果替你挡下一次追问，但因果债又沉了几分，业力+2。"

    event_pool: List[str] = ["rumor", "owner", "owner", "market"]
    if _get_int(player, "tracking_marks") > 0:
        event_pool.append("heishui")
    if _get_int(player, "stolen_luck_count") > 0:
        event_pool.append("luck")
    if _get_int(player, "stolen_fate_count") > 0:
        event_pool.append("fate")
    if _get_int(player, "stolen_lifespan_count") > 0:
        event_pool.append("lifespan")
    if _get_int(player, "stolen_inheritance_count") > 0:
        event_pool.extend(["inheritance", "inheritance"])
    event = random.choice(event_pool)

    if event == "owner":
        loss = min(_get_int(player, "spirit_stones"), random.randint(2, 8) + _get_int(player, "enemy_count"))
        player.spirit_stones -= loss
        player.reputation -= 1
        _add_exposure(player, random.randint(3, 6))
        text = f"盗术反噬：有失主认出你的手法，你花{loss}枚灵石打点，声望-1。"
    elif event == "market":
        player.reputation -= 2
        player.enemy_count += 1
        _add_exposure(player, random.randint(4, 7))
        text = "盗术反噬：坊市传出盗修传闻，有人把矛头指向你，结仇+1。"
    elif event == "heishui":
        player.tracking_marks += 1
        _add_exposure(player, random.randint(3, 6))
        text = "盗术反噬：黑水中人似乎记住了你的路数，追踪标记+1。"
    elif event == "luck":
        player.luck = max(0, player.luck - 1)
        _add_karma(player, random.randint(2, 5))
        text = "盗术反噬：偷来的气运散得很快，气运-1，业力上浮。"
    elif event == "fate":
        player.reputation -= 1
        _add_karma(player, random.randint(4, 7))
        player.heart_demon += random.randint(1, 3)
        text = "盗术反噬：因果缠身，几桩旧事同时找上门，心魔与业力上升。"
    elif event == "lifespan":
        _add_karma(player, random.randint(5, 9))
        player.hp = max(0, player.hp - random.randint(3, 7))
        player.heart_demon += 2
        text = "盗术反噬：寿元阴债夜半回潮，气血受损，心魔+2。"
    elif event == "inheritance":
        player.enemy_count += 1
        player.reputation -= 3
        _add_exposure(player, random.randint(8, 12))
        _add_karma(player, random.randint(5, 9))
        player.hp = max(0, player.hp - random.randint(5, 10))
        text = "盗术反噬：传承原主暗中追查，你受了一记隔空警告，结仇与暴露大增。"
    else:
        player.reputation -= 1
        _add_exposure(player, random.randint(2, 5))
        text = "盗术反噬：旁支院里有人低声议论你的手脚不干净，声望-1。"

    player.clamp()
    return text


def theft_tournament_adjustments(player: Any) -> Dict[str, object]:
    successes = _get_int(player, "theft_successes")
    failures = _get_int(player, "theft_failures")
    enemies = _get_int(player, "enemy_count")
    bad_reputation = max(0, -_get_int(player, "reputation"))
    fragments = _get_int(player, "stolen_manual_fragments")
    high_count = (
        _get_int(player, "stolen_luck_count")
        + _get_int(player, "stolen_opportunity_count")
        + _get_int(player, "stolen_fate_count")
        + _get_int(player, "stolen_lifespan_count")
        + _get_int(player, "stolen_inheritance_count")
    )
    penalty = min(6, enemies // 3 + failures // 6 + bad_reputation // 12 + max(0, _get_int(player, "karma") - 40) // 15)
    penalty_step = min(3, penalty // 2)
    mind = min(4, fragments // 2 + successes // 5 + _get_int(player, "stolen_fate_count")) - penalty_step
    trial = min(5, successes // 3 + _get_int(player, "stolen_luck_count") + _get_int(player, "stolen_opportunity_count")) - penalty_step
    combat = (
        min(
            6,
            fragments // 2
            + successes // 5
            + _get_int(player, "stolen_cultivation_count") * 2
            + _get_int(player, "stolen_inheritance_count") * 2,
        )
        - penalty_step
    )
    flags: List[str] = []
    if _get_int(player, "theft_attempts") >= 8 or high_count > 0:
        flags.append("旁门痕迹过重")
    if failures >= 3 or bad_reputation >= 6:
        flags.append("手脚不干净")
    if enemies >= 3:
        flags.append("被多名族人指认")
    if high_count >= 2 or _get_int(player, "karma") >= 55:
        flags.append("虽有奇技，难入正道法眼")
    return {
        "mind": mind,
        "trial": trial,
        "combat": combat,
        "total": mind + trial + combat,
        "flags": flags,
    }


def theft_status_text(player: Any) -> str:
    attempts = _get_int(player, "theft_attempts")
    successes = _get_int(player, "theft_successes")
    rate = successes * 100 / attempts if attempts else 0.0
    return (
        "盗术旁门："
        f"盗术{_get_int(player, 'theft_skill')}｜经验{_get_int(player, 'theft_exp')}｜"
        f"尝试{attempts}｜成功{successes}（{rate:.0f}%）｜失败{_get_int(player, 'theft_failures')}｜"
        f"赔偿{_get_int(player, 'theft_compensations')}｜拒赔{_get_int(player, 'theft_refusals')}｜"
        f"强逃{_get_int(player, 'theft_escape_count')}｜声望{_get_int(player, 'reputation'):+d}｜"
        f"结仇{_get_int(player, 'enemy_count')}"
    )
