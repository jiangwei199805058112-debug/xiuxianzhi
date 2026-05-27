"""轻量盗术系统。"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from cultivation_assets import equipment_bonus, grant_equipment
from growth_system import gain_mastery, has_insight


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
THEFT_NEGATIVE_FLAGS = {"旁门痕迹过重", "手脚不干净", "被多名族人指认", "虽有奇技，难入正道法眼", "窃法反噬", "因果缠身"}

SUCCESS_PREFIXES: Dict[str, List[str]] = {
    "basic": [
        "你借人群遮掩，指尖轻轻一翻。",
        "你假作整理衣袖，顺势把零碎物件纳入掌中。",
        "你踩准摊前嘈杂的一瞬，下手极快。",
    ],
    "stall": [
        "你趁夜色绕到摊后，拆开一只没锁牢的木箱。",
        "你避过更夫脚步，在摊布下摸到可用之物。",
        "你沿着坊市暗巷潜行，翻到一份无人认领的货。",
    ],
    "intel": [
        "你从茶棚旧账里抽出几页夹纸。",
        "你截下一封尚未送出的短笺。",
        "你在说书人换茶时记下几句真消息。",
    ],
    "manual": [
        "你借阅典册时暗藏拓纸，将残页纹路压下。",
        "你绕进旧阁背窗，匆匆描下几段口诀。",
        "你在族学值守换班时，拓走一角残缺功法。",
    ],
    "cultivation": [
        "你隔着静室门缝牵动一丝外泄气机。",
        "你以盗息法贴近对方吐纳节律，强行截走一缕修为。",
        "你趁对方行功收束之际，抽走一段散乱灵机。",
    ],
    "luck": [
        "你在香灰将灭时截下一点浮动气数。",
        "你以旁门手法拨开一枚好运签的归处。",
        "你盯住对方眉心气机，将一缕顺风势偷来。",
    ],
    "opportunity": [
        "你提前一步赶到约定岔路，接走本该属于旁人的线索。",
        "你在机缘主人迟疑时横插一手。",
        "你顺着风声摸到隐秘地点，抢先取走一份小机缘。",
    ],
    "fate": [
        "你以盗术勾住一段将断未断的因果线。",
        "你在灯影摇晃时改了半寸因果归处。",
        "你冒险把一段旁人小祸移到自己影中。",
    ],
    "lifespan": [
        "你按住腕脉，以阴冷秘法截来一线生机。",
        "你听见耳边似有年轮剥落，仍将寿元牵入体内。",
        "你借对方旧伤松动之机，偷来一丝寿数。",
    ],
    "inheritance": [
        "你冒险触动传承禁纹，在反震前撕下一缕核心烙印。",
        "你趁传承印记换主未稳，将一部分记忆强行盗走。",
        "你在 NPC 心神动摇的一刹那，偷入传承最深处。",
    ],
}

FAILURE_TEXTS: Dict[str, List[str]] = {
    "basic": [
        "对方忽然回头，你只摸到一把冷汗。",
        "你指尖刚碰到钱袋，摊主便警觉地按住衣襟。",
        "人群突然散开，你的动作被迫停在半途。",
    ],
    "stall": [
        "摊位下暗铃轻响，你不得不立刻退走。",
        "夜巡脚步来得太快，你翻出的东西只能原样塞回。",
        "木箱夹层里藏着警示符，你刚碰到便心头一跳。",
    ],
    "intel": [
        "短笺上竟有暗记，你只读了两行便被迫收手。",
        "茶棚掌柜换账太快，你没能抄下关键信息。",
        "你听到的消息被故意掺了假，一时难辨真伪。",
    ],
    "manual": [
        "功法残页边缘有留影粉，你不敢继续拓印。",
        "旧阁门轴忽然响了一声，你只好把拓纸揉碎。",
        "典册灵纹轻震，似乎已经记下你的气息。",
    ],
    "cultivation": [
        "对方气机忽然内敛，你反被吐纳节律震开。",
        "你截取修为时慢了半息，散乱灵机反冲经脉。",
        "对方丹田灵力回旋，你的盗息法被强行弹开。",
    ],
    "luck": [
        "那缕气运像游鱼般滑走，反在你指间留下一点寒意。",
        "好运签忽然折断，你意识到气数并不肯易主。",
        "对方眉心气机一亮，你偷来的势头当场散尽。",
    ],
    "opportunity": [
        "机缘主人来得比你预料更早，你只能隐入阴影。",
        "藏物处已被人设下记号，你一碰便知道不妙。",
        "线索半途断掉，像是有人故意等你上钩。",
    ],
    "fate": [
        "因果线忽然绷紧，反将你的心神勒了一下。",
        "灯影倒卷，半段因果缠回你自己身上。",
        "你试图改线，却听见识海里传来一声裂响。",
    ],
    "lifespan": [
        "寿元阴气反扑，胸口像被冷针扎过。",
        "那线生机刚入体便化作阴债，反噬气血。",
        "对方旧伤中藏着怨气，你一触便被拖住。",
    ],
    "inheritance": [
        "传承禁制骤然亮起，你几乎被当场锁住神魂。",
        "NPC 传承深处有旧主残念，你刚探入便遭反震。",
        "烙印换主的一瞬提前结束，你被余波狠狠扫出。",
    ],
}

MONTHLY_EVENT_TEXTS: Dict[str, List[str]] = {
    "owner": [
        "盗术反噬：有失主认出你的手法，你花{loss}枚灵石打点，声望-1，暴露度+{exposure}。",
        "盗术反噬：旧事被人翻起，你赔出{loss}枚灵石压话，声望-1，暴露度+{exposure}。",
    ],
    "market": [
        "盗术反噬：坊市传出盗修传闻，有人把矛头指向你，结仇+1，声望-2，暴露度+{exposure}。",
        "盗术反噬：摊主们私下串供，认定你手脚不净，结仇+1，声望-2，暴露度+{exposure}。",
    ],
    "heishui": [
        "盗术反噬：黑水中人似乎记住了你的路数，追踪标记+1，暴露度+{exposure}。",
        "盗术反噬：有黑水掮客隔街看了你一眼，追踪标记+1，暴露度+{exposure}。",
    ],
    "luck": [
        "盗术反噬：偷来的气运散得很快，气运-1，业力+{karma}。",
        "盗术反噬：几件小事连续失手，偷来的好运开始回潮，气运-1，业力+{karma}。",
    ],
    "fate": [
        "盗术反噬：因果缠身，几桩旧事同时找上门，声望-1，业力+{karma}，心魔+{heart}。",
        "盗术反噬：你梦见几条细线缠住手腕，醒后心神不宁，声望-1，业力+{karma}，心魔+{heart}。",
    ],
    "lifespan": [
        "盗术反噬：寿元阴债夜半回潮，气血-{hp_loss}，心魔+2，业力+{karma}。",
        "盗术反噬：胸口旧寒忽然发作，像有人隔空讨债，气血-{hp_loss}，心魔+2，业力+{karma}。",
    ],
    "inheritance": [
        "盗术反噬：传承原主暗中追查，你受了一记隔空警告，结仇+1，声望-3，暴露度+{exposure}，业力+{karma}。",
        "盗术反噬：被盗传承的旧印在夜里发烫，原主已循迹而来，结仇+1，声望-3，暴露度+{exposure}，业力+{karma}。",
    ],
    "rumor": [
        "盗术反噬：旁支院里有人低声议论你的手脚不干净，声望-1，暴露度+{exposure}。",
        "盗术反噬：几名族人见你便收起钱袋，传言已起，声望-1，暴露度+{exposure}。",
    ],
}


def _get_int(player: Any, attr: str, default: int = 0) -> int:
    try:
        return int(getattr(player, attr, default))
    except (TypeError, ValueError):
        return default


def _line(lines: Dict[str, List[str]], key: str) -> str:
    options = lines.get(key) or lines.get("basic") or [""]
    return random.choice(options)


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
    mastery_text = gain_mastery(player, "theft_mastery", 4)
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
        + (f"\n{mastery_text}" if mastery_text else "")
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
    if has_insight(player, "妙手无痕"):
        rate += 4.0
    if has_insight(player, "窥隙探囊") and theft_type in {"intel", "manual", "cultivation"}:
        rate += 5.0
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
    if cfg.get("high_tier"):
        player.theft_high_tier_successes += 1
    _gain_theft_exp(player, int(cfg.get("exp_success", 4)))


def _apply_success_effect(player: Any, theft_type: str) -> str:
    if theft_type == "basic":
        stones = random.randint(3, 7)
        herbs = random.randint(1, 3)
        player.spirit_stones += stones
        player.herbs += herbs
        if random.random() < 0.28:
            _add_exposure(player, 1)
        return f"{_line(SUCCESS_PREFIXES, theft_type)}灵石+{stones}，普通灵草+{herbs}。"

    if theft_type == "stall":
        roll = random.random()
        _add_exposure(player, random.randint(1, 2))
        if roll < 0.35:
            player.pills += 1
            return f"{_line(SUCCESS_PREFIXES, theft_type)}摸走一只未封口的小瓷瓶，丹药+1。"
        if roll < 0.70:
            if random.random() < 0.5:
                player.talisman_fire += 1
                return f"{_line(SUCCESS_PREFIXES, theft_type)}得火弹符+1。"
            player.talisman_guard += 1
            return f"{_line(SUCCESS_PREFIXES, theft_type)}得护身符+1。"
        item_name = grant_equipment(player, random.choice(["cloth_boots", "calm_charm", "iron_sword"]))
        return f"{_line(SUCCESS_PREFIXES, theft_type)}翻得一件旧装备：{item_name}。" if item_name else f"{_line(SUCCESS_PREFIXES, theft_type)}得些可用杂物。"

    if theft_type == "intel":
        intel = random.randint(2, 4)
        player.intelligence += intel
        player.explore_intel_bonus += 1 if random.random() < 0.45 else 0
        if _get_int(player, "theft_skill") >= 25 and random.random() < 0.35:
            player.black_market_clue += 1
            player.heishui_tournament_bonuses["trial"] = int(player.heishui_tournament_bonuses.get("trial", 0)) + 1
            return f"{_line(SUCCESS_PREFIXES, theft_type)}情报中夹着黑水暗线，情报值+{intel}，黑市线索+1。"
        section = random.choice(["mind", "trial", "combat"])
        player.heishui_tournament_bonuses[section] = int(player.heishui_tournament_bonuses.get(section, 0)) + 1
        return f"{_line(SUCCESS_PREFIXES, theft_type)}情报值+{intel}，对应试炼略有准备。"

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
            return f"{_line(SUCCESS_PREFIXES, theft_type)}竟拼出一门低阶完整功法，功法残页+{fragments}，斗法经验+2，攻击+1。"
        return f"{_line(SUCCESS_PREFIXES, theft_type)}功法残页+{fragments}。"

    if theft_type == "cultivation":
        progress = random.randint(8, 14)
        player.stolen_cultivation_count += 1
        player.gain_cultivation_progress(progress)
        player.cultivation += random.randint(1, 3)
        _add_exposure(player, random.randint(4, 7))
        _add_karma(player, random.randint(5, 8))
        player.hp -= random.randint(1, 4)
        return f"{_line(SUCCESS_PREFIXES, theft_type)}修炼进度+{progress}，业力与暴露随之上涨。"

    if theft_type == "luck":
        player.stolen_luck_count += 1
        player.luck += 1 + (1 if random.random() < 0.18 else 0)
        _add_exposure(player, random.randint(3, 5))
        _add_karma(player, random.randint(4, 7))
        return f"{_line(SUCCESS_PREFIXES, theft_type)}短期行事似乎顺了些，气运+1。"

    if theft_type == "opportunity":
        player.stolen_opportunity_count += 1
        player.enemy_count += 1
        player.reputation -= 1
        _add_exposure(player, random.randint(4, 7))
        _add_karma(player, random.randint(3, 6))
        reward = random.choice(["aged_herbs_10", "pills", "equipment", "intel"])
        if reward == "aged_herbs_10":
            player.aged_herbs_10 += 1
            return f"{_line(SUCCESS_PREFIXES, theft_type)}十年份灵草+1，但原主隐约记住了你。"
        if reward == "pills":
            player.pills += 2
            return f"{_line(SUCCESS_PREFIXES, theft_type)}丹药+2，但原主隐约记住了你。"
        if reward == "intel":
            player.intelligence += 4
            return f"{_line(SUCCESS_PREFIXES, theft_type)}情报值+4，但原主隐约记住了你。"
        item_name = grant_equipment(player, random.choice(["greenwood_sword", "sense_charm", "quiet_robe"]))
        return f"{_line(SUCCESS_PREFIXES, theft_type)}得{item_name}，但原主隐约记住了你。"

    if theft_type == "fate":
        player.stolen_fate_count += 1
        if FATE_SHIELD_FLAG not in player.market_flags:
            player.market_flags.append(FATE_SHIELD_FLAG)
        player.dao_heart += 1
        _add_exposure(player, random.randint(5, 8))
        _add_karma(player, random.randint(8, 12))
        return f"{_line(SUCCESS_PREFIXES, theft_type)}似可替你挡一次小祸，道心+1，但因果债已缠身。"

    if theft_type == "lifespan":
        player.stolen_lifespan_count += 1
        hp_gain = random.randint(3, 5)
        player.max_hp += hp_gain
        player.hp += hp_gain
        player.heart_demon += random.randint(2, 4)
        _add_exposure(player, random.randint(7, 10))
        _add_karma(player, random.randint(12, 16))
        return f"{_line(SUCCESS_PREFIXES, theft_type)}气血上限+{hp_gain}，但阴冷业力缠上经脉。"

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
        return f"{_line(SUCCESS_PREFIXES, theft_type)}功法残页+3，悟性+2，神识+2，攻击+2{equipment_text}。"

    return "你下手得逞，却只摸到些无关紧要的东西。"


def _apply_failure_backlash(player: Any, theft_type: str) -> str:
    if theft_type == "cultivation":
        loss = random.randint(3, 7)
        player.cultivation_progress = max(0, player.cultivation_progress - loss)
        player.mp = max(0, player.mp - random.randint(2, 5))
        karma_gain = random.randint(2, 4)
        _add_karma(player, karma_gain)
        return f"{_line(FAILURE_TEXTS, theft_type)}修炼进度-{loss}，业力+{karma_gain}，灵力受损。"
    if theft_type in {"luck", "opportunity"}:
        karma_gain = random.randint(2, 4)
        luck_loss = 1 if random.random() < 0.30 else 0
        _add_karma(player, karma_gain)
        player.luck = max(0, player.luck - luck_loss)
        loss_text = f"，气运-{luck_loss}" if luck_loss else ""
        return f"{_line(FAILURE_TEXTS, theft_type)}业力+{karma_gain}{loss_text}。"
    if theft_type == "fate":
        karma_gain = random.randint(5, 8)
        heart_gain = random.randint(1, 3)
        _add_karma(player, karma_gain)
        player.heart_demon += heart_gain
        return f"{_line(FAILURE_TEXTS, theft_type)}业力+{karma_gain}，心魔+{heart_gain}。"
    if theft_type == "lifespan":
        karma_gain = random.randint(6, 10)
        hp_loss = random.randint(4, 8)
        _add_karma(player, karma_gain)
        player.hp = max(0, player.hp - hp_loss)
        return f"{_line(FAILURE_TEXTS, theft_type)}气血-{hp_loss}，业力+{karma_gain}。"
    if theft_type == "inheritance":
        exposure_gain = random.randint(8, 12)
        karma_gain = random.randint(8, 14)
        hp_loss = random.randint(8, 14)
        _add_exposure(player, exposure_gain)
        _add_karma(player, karma_gain)
        player.hp = max(0, player.hp - hp_loss)
        player.enemy_count += 1
        return f"{_line(FAILURE_TEXTS, theft_type)}暴露度+{exposure_gain}，业力+{karma_gain}，气血-{hp_loss}，结仇+1。"
    return _line(FAILURE_TEXTS, theft_type)


def attempt_theft(player: Any, theft_type: str) -> Dict[str, object]:
    if theft_type not in THEFT_TYPES:
        return {"success": False, "needs_resolution": False, "text": "你一时不知该偷什么。"}
    requirement = _requirement_text(player, theft_type)
    if requirement:
        return {"success": False, "needs_resolution": False, "text": requirement}

    cfg = THEFT_TYPES[theft_type]
    player.theft_attempts += 1
    if cfg.get("high_tier"):
        player.theft_high_tier_attempts += 1
    rate = calculate_theft_success_rate(player, "", theft_type)
    if random.random() * 100 <= rate:
        _success_common(player, theft_type)
        text = _apply_success_effect(player, theft_type)
        mastery_text = gain_mastery(player, "theft_mastery", 3 if cfg.get("high_tier") else 2)
        return {
            "success": True,
            "needs_resolution": False,
            "rate": rate,
            "text": f"{cfg['name']}成功（成功率约{rate:.0f}%）。{text}" + (f"\n{mastery_text}" if mastery_text else ""),
        }

    player.theft_failures += 1
    _gain_theft_exp(player, int(cfg.get("exp_fail", 2)))
    failure_exposure = random.randint(0, 2)
    if has_insight(player, "妙手无痕"):
        failure_exposure = max(0, failure_exposure - 1)
    _add_exposure(player, failure_exposure)
    backlash = _apply_failure_backlash(player, theft_type)
    exposure_text = f"败露痕迹：暴露度+{failure_exposure}。" if failure_exposure else "你暂时没留下明显暴露痕迹。"
    mastery_text = gain_mastery(player, "theft_mastery", 2 if cfg.get("high_tier") else 1)
    return {
        "success": False,
        "needs_resolution": True,
        "rate": rate,
        "text": f"{cfg['name']}失败（成功率约{rate:.0f}%）。{backlash}{exposure_text}" + (f"\n{mastery_text}" if mastery_text else ""),
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
        exposure_gain = random.randint(0, 2)
        _add_exposure(player, exposure_gain)
        if paid < cost:
            old_enemy = player.enemy_count
            player.reputation -= 1
            player.enemy_count += 1 if random.random() < 0.18 else 0
            enemy_gain = player.enemy_count - old_enemy
            result = (
                f"赔偿处理：损失灵石{paid}/{cost}，暴露度+{exposure_gain}，旁门声望-1，"
                f"结仇+{enemy_gain}。你赔得不够，只勉强压下风波。"
            )
        else:
            reputation_loss = 1 if high_tier and random.random() < 0.45 else 0
            player.reputation -= reputation_loss
            result = (
                f"赔偿处理：损失灵石{paid}，暴露度+{exposure_gain}，旁门声望-{reputation_loss}。"
                "你将事端暂时按下。"
            )
    elif choice == "2":
        player.theft_refusals += 1
        reputation_loss = 2 + (1 if high_tier else 0)
        player.reputation -= reputation_loss
        player.enemy_count += 1
        exposure_gain = random.randint(3, 5)
        _add_exposure(player, exposure_gain)
        target = random.choice(list(player.npc_affection))
        affection_loss = random.randint(2, 5)
        player.npc_affection[target] -= affection_loss
        result = (
            f"拒赔处理：旁门声望-{reputation_loss}，{target}好感-{affection_loss}，"
            f"暴露度+{exposure_gain}，结仇+1。你省下赔偿，却让旁人记恨。"
        )
    else:
        player.theft_escape_count += 1
        reputation_loss = 3 + (2 if high_tier else 0)
        enemy_gain = 1 + (1 if high_tier and random.random() < 0.45 else 0)
        exposure_gain = random.randint(6, 11)
        karma_gain = random.randint(3, 7) + (3 if high_tier else 0)
        tracking_gain = 1 if random.random() < (0.24 if high_tier else 0.10) else 0
        hp_loss = random.randint(2, 8)
        if has_insight(player, "来去无踪"):
            exposure_gain = max(2, exposure_gain - 2)
            karma_gain = max(0, karma_gain - 1)
            hp_loss = max(0, hp_loss - 2)
            if tracking_gain and random.random() < 0.35:
                tracking_gain = 0
        player.reputation -= reputation_loss
        player.enemy_count += enemy_gain
        _add_exposure(player, exposure_gain)
        _add_karma(player, karma_gain)
        player.tracking_marks += tracking_gain
        player.hp = max(0, player.hp - hp_loss)
        _gain_theft_exp(player, 2)
        result = (
            f"强行脱身：暴露度+{exposure_gain}，业力+{karma_gain}，追踪标记+{tracking_gain}，"
            f"气血-{hp_loss}，旁门声望-{reputation_loss}，结仇+{enemy_gain}。"
            "你逃过当场追问，却留下更重痕迹。"
        )
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

    player.theft_monthly_event_count += 1
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
        exposure_gain = random.randint(3, 6)
        player.spirit_stones -= loss
        player.reputation -= 1
        _add_exposure(player, exposure_gain)
        text = _line(MONTHLY_EVENT_TEXTS, event).format(loss=loss, exposure=exposure_gain)
    elif event == "market":
        player.reputation -= 2
        player.enemy_count += 1
        exposure_gain = random.randint(4, 7)
        _add_exposure(player, exposure_gain)
        text = _line(MONTHLY_EVENT_TEXTS, event).format(exposure=exposure_gain)
    elif event == "heishui":
        player.tracking_marks += 1
        exposure_gain = random.randint(3, 6)
        _add_exposure(player, exposure_gain)
        text = _line(MONTHLY_EVENT_TEXTS, event).format(exposure=exposure_gain)
    elif event == "luck":
        player.luck = max(0, player.luck - 1)
        karma_gain = random.randint(2, 5)
        _add_karma(player, karma_gain)
        text = _line(MONTHLY_EVENT_TEXTS, event).format(karma=karma_gain)
    elif event == "fate":
        player.reputation -= 1
        karma_gain = random.randint(4, 7)
        heart_gain = random.randint(1, 3)
        _add_karma(player, karma_gain)
        player.heart_demon += heart_gain
        text = _line(MONTHLY_EVENT_TEXTS, event).format(karma=karma_gain, heart=heart_gain)
    elif event == "lifespan":
        karma_gain = random.randint(5, 9)
        hp_loss = random.randint(3, 7)
        _add_karma(player, karma_gain)
        player.hp = max(0, player.hp - hp_loss)
        player.heart_demon += 2
        text = _line(MONTHLY_EVENT_TEXTS, event).format(karma=karma_gain, hp_loss=hp_loss)
    elif event == "inheritance":
        player.enemy_count += 1
        player.reputation -= 3
        exposure_gain = random.randint(8, 12)
        karma_gain = random.randint(5, 9)
        hp_loss = random.randint(5, 10)
        _add_exposure(player, exposure_gain)
        _add_karma(player, karma_gain)
        player.hp = max(0, player.hp - hp_loss)
        text = _line(MONTHLY_EVENT_TEXTS, event).format(exposure=exposure_gain, karma=karma_gain, hp_loss=hp_loss)
    else:
        player.reputation -= 1
        exposure_gain = random.randint(2, 5)
        _add_exposure(player, exposure_gain)
        text = _line(MONTHLY_EVENT_TEXTS, "rumor").format(exposure=exposure_gain)

    player.clamp()
    return text


def theft_tournament_adjustments(player: Any) -> Dict[str, object]:
    successes = _get_int(player, "theft_successes")
    failures = _get_int(player, "theft_failures")
    attempts = _get_int(player, "theft_attempts")
    enemies = _get_int(player, "enemy_count")
    bad_reputation = max(0, -_get_int(player, "reputation"))
    fragments = _get_int(player, "stolen_manual_fragments")
    high_count = (
        _get_int(player, "stolen_cultivation_count")
        + _get_int(player, "stolen_luck_count")
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
    if attempts >= 8 or high_count > 0:
        flags.append("旁门痕迹过重")
    if failures >= 3 or bad_reputation >= 6:
        flags.append("手脚不干净")
    if enemies >= 3:
        flags.append("被多名族人指认")
    if high_count >= 2 or (attempts > 0 and _get_int(player, "karma") >= 55):
        flags.append("虽有奇技，难入正道法眼")
    if fragments >= 2 and (failures >= 2 or _get_int(player, "stolen_cultivation_count") > 0):
        flags.append("窃法反噬")
    if attempts > 0 and (
        _get_int(player, "stolen_fate_count") > 0
        or _get_int(player, "stolen_lifespan_count") > 0
        or _get_int(player, "karma") >= 45
    ):
        flags.append("因果缠身")

    notes: List[str] = []
    if "手脚不干净" in flags:
        notes.append("手脚不净：多次败露或声望受损，族中对你的来路多了几分戒心。")
    if "旁门痕迹过重" in flags:
        notes.append("旁门留痕：盗术使用频繁，身法虽利，却难免留下旁门气息。")
    if "窃法反噬" in flags:
        notes.append("窃法反噬：功法残页与偷修为带来战力，也让问心时的气机不够清正。")
    if "因果缠身" in flags:
        notes.append("因果缠身：气运、因果或寿元类盗术牵扯过深，族老隐约察觉后患。")
    return {
        "mind": mind,
        "trial": trial,
        "combat": combat,
        "total": mind + trial + combat,
        "flags": flags,
        "notes": notes,
    }


def theft_status_text(player: Any) -> str:
    attempts = _get_int(player, "theft_attempts")
    successes = _get_int(player, "theft_successes")
    rate = successes * 100 / attempts if attempts else 0.0
    high_successes = (
        _get_int(player, "stolen_cultivation_count")
        + _get_int(player, "stolen_luck_count")
        + _get_int(player, "stolen_opportunity_count")
        + _get_int(player, "stolen_fate_count")
        + _get_int(player, "stolen_lifespan_count")
        + _get_int(player, "stolen_inheritance_count")
    )
    return (
        "盗术旁门："
        f"盗术{_get_int(player, 'theft_skill')}｜经验{_get_int(player, 'theft_exp')}｜熟练{_get_int(player, 'theft_mastery')}｜"
        f"尝试{attempts}｜成功{successes}（{rate:.0f}%）｜失败{_get_int(player, 'theft_failures')}｜"
        f"赔偿{_get_int(player, 'theft_compensations')}｜拒赔{_get_int(player, 'theft_refusals')}｜"
        f"强逃{_get_int(player, 'theft_escape_count')}｜声望{_get_int(player, 'reputation'):+d}｜"
        f"结仇{_get_int(player, 'enemy_count')}\n"
        "高阶盗术："
        f"尝试{_get_int(player, 'theft_high_tier_attempts')}｜成功{_get_int(player, 'theft_high_tier_successes')}｜"
        f"高阶收益{high_successes}｜功法残页{_get_int(player, 'stolen_manual_fragments')}｜"
        f"修为{_get_int(player, 'stolen_cultivation_count')}｜气运{_get_int(player, 'stolen_luck_count')}｜"
        f"机缘{_get_int(player, 'stolen_opportunity_count')}｜因果{_get_int(player, 'stolen_fate_count')}｜"
        f"寿元{_get_int(player, 'stolen_lifespan_count')}｜传承{_get_int(player, 'stolen_inheritance_count')}｜"
        f"月末反噬{_get_int(player, 'theft_monthly_event_count')}"
    )
